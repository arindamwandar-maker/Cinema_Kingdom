import html
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.google_sheet import GoogleSheetService


class AdminHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)

    def is_admin(self, user_id: int) -> bool:
        return self.db.is_admin(user_id, self.config.ADMIN_IDS)

    def is_super_admin(self, user_id: int) -> bool:
        return user_id == self.config.SUPER_ADMIN_ID

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        cur = self.db.conn.cursor()
        active = cur.execute("SELECT COUNT(*) FROM movies WHERE status='active'").fetchone()[0]
        deleted = cur.execute("SELECT COUNT(*) FROM movies WHERE status='deleted'").fetchone()[0]
        users = cur.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        pending = cur.execute("SELECT COUNT(*) FROM requests WHERE status='pending'").fetchone()[0]
        downloads = cur.execute("SELECT COALESCE(SUM(downloads),0) FROM movies WHERE status='active'").fetchone()[0]
        await message.reply_text(
            '📊 <b>Cinema Kingdom Statistics</b>\n\n'
            f'🎬 Active Movies: {active}\n🗑 Deleted Movies: {deleted}\n'
            f'👥 Users: {users}\n📥 Pending Requests: {pending}\n⬇ Downloads: {downloads}',
            parse_mode=ParseMode.HTML,
        )

    async def requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        rows = self.db.get_pending_requests()
        if not rows:
            await message.reply_text('✅ No pending movie requests.')
            return
        text = '🎬 <b>Pending Requests</b>\n\n'
        for req in rows[:20]:
            text += f"🆔 #{req['id']}\n👤 {html.escape(req.get('first_name') or 'Unknown')}\n🎥 {html.escape(req['movie_title'])}\n\n"
        await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        if not context.args:
            await message.reply_text('Usage: /broadcast Your Message')
            return
        body = ' '.join(context.args)
        success = 0
        for row in self.db.conn.execute('SELECT user_id FROM users').fetchall():
            try:
                await context.bot.send_message(row[0], body)
                success += 1
            except Exception:
                pass
        await message.reply_text(f'✅ Broadcast completed. Delivered: {success}')

    async def delete_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        if not message or not chat:
            return

        if chat.id != self.config.STORAGE_CHANNEL:
            await message.reply_text('❌ Use this command only in MyStorage: <code>/delete MovieID</code>', parse_mode=ParseMode.HTML)
            return

        # In a channel post Telegram may not provide effective_user. The private storage channel itself is the gate.
        if user and not self.is_admin(user.id):
            await message.reply_text('❌ Only bot admins can delete movies.')
            return

        text = (message.text or message.caption or '').strip()
        parts = text.split()
        if len(parts) < 2:
            await message.reply_text('Usage: <code>/delete 12</code>', parse_mode=ParseMode.HTML)
            return
        try:
            movie_id = int(parts[1])
        except (ValueError, TypeError):
            await message.reply_text('❌ Movie ID must be a number.')
            return

        movie = self.db.get_movie(movie_id)
        if not movie:
            old = self.db.get_movie(movie_id, include_deleted=True)
            await message.reply_text('⚠️ Movie already deleted.' if old else '❌ Movie not found.')
            return

        deleted_by_id = user.id if user else self.config.SUPER_ADMIN_ID
        deleted_by = f'@{user.username}' if user and user.username else str(deleted_by_id)
        deleted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not self.db.delete_movie(movie_id, deleted_by_id):
            await message.reply_text('❌ Delete failed.')
            return

        # Remove the original storage post when possible.
        if movie.get('source_chat_id') and movie.get('source_message_id'):
            try:
                await context.bot.delete_message(movie['source_chat_id'], movie['source_message_id'])
            except Exception:
                pass

        sheet_ok = self.sheet.mark_movie_deleted(movie_id, deleted_by, deleted_time)
        await message.reply_text(
            '🗑 <b>Movie Deleted Successfully</b>\n\n'
            f"🎬 {html.escape(movie['title'])}\n🆔 <code>{movie_id}</code>\n"
            f'👤 {html.escape(deleted_by)}\n🕒 {deleted_time}\n\n'
            f'{"✅ Google Sheet updated" if sheet_ok else "⚠️ Google Sheet not updated"}',
            parse_mode=ParseMode.HTML,
        )

    async def restore_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message, chat = update.effective_user, update.effective_message, update.effective_chat
        if not message or not chat or chat.id != self.config.STORAGE_CHANNEL:
            return
        if user and not self.is_admin(user.id):
            return
        parts = (message.text or '').split()
        if len(parts) < 2:
            await message.reply_text('Usage: /restore MovieID')
            return
        try:
            movie_id = int(parts[1])
        except ValueError:
            await message.reply_text('❌ Invalid Movie ID.')
            return
        if self.db.restore_movie(movie_id):
            self.sheet.mark_movie_active(movie_id)
            await message.reply_text(f'✅ Movie restored: {movie_id}')
        else:
            await message.reply_text('❌ Restore failed.')

    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        if not context.args:
            await message.reply_text('Usage: /addadmin TelegramUserID')
            return
        try:
            admin_id = int(context.args[0])
        except ValueError:
            await message.reply_text('❌ Invalid admin ID.')
            return
        self.db.add_admin(admin_id, user.id)
        await message.reply_text(f'✅ Admin added: {admin_id}')

    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        if not context.args:
            await message.reply_text('Usage: /removeadmin TelegramUserID')
            return
        try:
            admin_id = int(context.args[0])
        except ValueError:
            await message.reply_text('❌ Invalid admin ID.')
            return
        if admin_id == self.config.SUPER_ADMIN_ID:
            await message.reply_text('❌ Super admin cannot be removed.')
            return
        await message.reply_text('✅ Admin removed.' if self.db.remove_admin(admin_id) else '⚠️ Admin not found.')

    async def list_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        admins = sorted(set(self.config.ADMIN_IDS + self.db.get_admin_ids()))
        text = '👑 <b>Bot Admins</b>\n\n' + '\n'.join(
            f"• <code>{aid}</code> — {'Super Admin' if aid == self.config.SUPER_ADMIN_ID else 'Admin'}" for aid in admins
        )
        await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def sheet_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        ok, result = self.sheet.test_connection()
        await message.reply_text(('✅ ' if ok else '❌ ') + result)
