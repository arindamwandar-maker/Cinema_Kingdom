import html

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
        cursor = self.db.conn.cursor()
        movies = cursor.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
        users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        pending = cursor.execute("SELECT COUNT(*) FROM requests WHERE status='pending'").fetchone()[0]
        downloads = cursor.execute("SELECT COALESCE(SUM(downloads),0) FROM movies").fetchone()[0]
        await message.reply_text(
            f"📊 <b>Cinema Kingdom Statistics</b>\n\n🎬 Movies: {movies}\n👥 Users: {users}\n📥 Pending Requests: {pending}\n⬇ Downloads: {downloads}",
            parse_mode=ParseMode.HTML,
        )

    async def requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        requests = self.db.get_pending_requests()
        if not requests:
            await message.reply_text("✅ No pending movie requests.")
            return
        text = "🎬 <b>Pending Requests</b>\n\n"
        for req in requests[:20]:
            text += f"🆔 #{req['id']}\n👤 {html.escape(req.get('first_name') or 'Unknown')}\n🎥 {html.escape(req['movie_title'])}\n\n"
        await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        if not context.args:
            await message.reply_text("Usage: /broadcast Your Message")
            return
        body = " ".join(context.args)
        success = 0
        for row in self.db.conn.execute("SELECT user_id FROM users").fetchall():
            try:
                await context.bot.send_message(row[0], body)
                success += 1
            except Exception:
                pass
        await message.reply_text(f"✅ Broadcast completed. Delivered: {success}")

    async def delete_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message, chat = update.effective_user, update.effective_message, update.effective_chat
        if not message or not chat:
            return
        if chat.id != self.config.STORAGE_CHANNEL:
            await message.reply_text("❌ Use /delete MovieID only inside MyStorage channel.")
            return
        # In channel posts effective_user may be unavailable. Posting permission in the private storage channel is the gate.
        if user and not self.is_admin(user.id):
            await message.reply_text("❌ Only bot admins can delete movies.")
            return
        if not context.args:
            await message.reply_text("Usage: /delete MovieID\nExample: /delete 12")
            return
        try:
            movie_id = int(context.args[0])
        except ValueError:
            await message.reply_text("❌ Invalid Movie ID.")
            return
        movie = self.db.get_movie(movie_id)
        if not movie:
            await message.reply_text("❌ Movie not found.")
            return

        # Remove original storage post if the bot has permission.
        if movie.get("source_chat_id") and movie.get("source_message_id"):
            try:
                await context.bot.delete_message(movie["source_chat_id"], movie["source_message_id"])
            except Exception:
                pass
        deleted = self.db.delete_movie(movie_id)
        await message.reply_text(
            f"✅ <b>Movie Deleted</b>\n\n🎬 {html.escape(movie['title'])}\n🆔 #{movie_id}" if deleted else "❌ Delete failed.",
            parse_mode=ParseMode.HTML,
        )

    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        if not context.args:
            await message.reply_text("Usage: /addadmin TelegramUserID")
            return
        try:
            admin_id = int(context.args[0])
        except ValueError:
            await message.reply_text("❌ Invalid admin ID.")
            return
        self.db.add_admin(admin_id, user.id)
        await message.reply_text(f"✅ Admin added: {admin_id}")

    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        if not context.args:
            await message.reply_text("Usage: /removeadmin TelegramUserID")
            return
        try:
            admin_id = int(context.args[0])
        except ValueError:
            await message.reply_text("❌ Invalid admin ID.")
            return
        if admin_id == self.config.SUPER_ADMIN_ID:
            await message.reply_text("❌ Super admin cannot be removed.")
            return
        await message.reply_text("✅ Admin removed." if self.db.remove_admin(admin_id) else "⚠️ Admin not found.")

    async def list_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        admins = sorted(set(self.config.ADMIN_IDS + self.db.get_admin_ids()))
        text = "👑 <b>Bot Admins</b>\n\n" + "\n".join(
            f"• {admin_id} — {'Super Admin' if admin_id == self.config.SUPER_ADMIN_ID else 'Admin'}" for admin_id in admins
        )
        await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def sheet_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        ok, result = self.sheet.test_connection()
        await message.reply_text(("✅ " if ok else "❌ ") + result)
