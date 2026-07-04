import html

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database


class AdminHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def is_admin(self, user_id: int) -> bool:
        return self.db.is_admin(user_id, self.config.ADMIN_IDS)

    def is_super_admin(self, user_id: int) -> bool:
        return user_id == self.config.SUPER_ADMIN_ID

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not self.is_admin(update.effective_user.id):
            return
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movies")
        movies = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status='pending'")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(downloads) FROM movies")
        downloads = cursor.fetchone()[0] or 0
        await update.effective_message.reply_text(
            "📊 <b>Cinema Kingdom Statistics</b>\n\n"
            f"🎬 Movies : {movies}\n"
            f"👤 Users : {users}\n"
            f"📥 Pending Requests : {pending}\n"
            f"⬇ Total Downloads : {downloads}",
            parse_mode=ParseMode.HTML,
        )

    async def requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not self.is_admin(update.effective_user.id):
            return
        requests = self.db.get_pending_requests()
        if not requests:
            await update.effective_message.reply_text("✅ No pending movie requests.")
            return
        text = "🎬 <b>Pending Requests</b>\n\n"
        for req in requests[:20]:
            text += (
                f"🆔 #{req['id']}\n"
                f"👤 {html.escape(req.get('first_name') or 'Unknown')}\n"
                f"🎥 {html.escape(req['movie_title'])}\n\n"
            )
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not self.is_admin(update.effective_user.id):
            return
        if not context.args:
            await update.effective_message.reply_text("Usage:\n/broadcast Your Message")
            return
        message = " ".join(context.args)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        success = 0
        for row in users:
            try:
                await context.bot.send_message(row[0], message)
                success += 1
            except Exception:
                pass
        await update.effective_message.reply_text(f"✅ Broadcast completed.\n\nDelivered : {success}")

    async def delete_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.effective_message
        chat = update.effective_chat
        if not message or not chat:
            return
        # /delete is intentionally allowed only inside the MyStorage channel.
        # In a channel post, Telegram may not expose effective_user, so channel posting permission is the safety gate.
        if chat.id != self.config.STORAGE_CHANNEL:
            await message.reply_text("❌ Movie delete is allowed only inside MyStorage channel.\n\nUse: /delete MovieID")
            return
        if user and not self.is_admin(user.id):
            return
        if not context.args:
            await message.reply_text("Usage:\n/delete MovieID\nExample: /delete 12")
            return
        try:
            movie_id = int(context.args[0])
        except ValueError:
            await message.reply_text("❌ Invalid Movie ID. Example: /delete 12")
            return
        movie = self.db.get_movie(movie_id)
        if not movie:
            await message.reply_text("❌ Movie not found.")
            return
        deleted = self.db.delete_movie(movie_id)
        if deleted:
            deleted_by = "Channel Admin"
            if user:
                deleted_by = '@' + user.username if user.username else str(user.id)
            await message.reply_text(
                f"✅ <b>Movie Deleted Successfully</b>\n\n🎬 {html.escape(movie['title'])}\n🆔 #{movie_id}\n👤 Deleted By: {html.escape(deleted_by)}",
                parse_mode=ParseMode.HTML,
            )
        else:
            await message.reply_text("❌ Delete failed.")

    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        if not context.args:
            await message.reply_text("Usage: /addadmin TelegramUserID")
            return
        try:
            new_admin = int(context.args[0])
        except ValueError:
            await message.reply_text("❌ Invalid admin ID.")
            return
        self.db.add_admin(new_admin, user.id)
        await message.reply_text(f"✅ Admin added: {new_admin}")

    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.effective_message
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
        removed = self.db.remove_admin(admin_id)
        await message.reply_text("✅ Admin removed." if removed else "⚠️ Admin was not found.")

    async def list_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        message = update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        admins = sorted(set(self.config.ADMIN_IDS + self.db.get_admin_ids()))
        text = "👑 <b>Bot Admins</b>\n\n"
        for admin_id in admins:
            label = "Super Admin" if admin_id == self.config.SUPER_ADMIN_ID else "Admin"
            text += f"• {admin_id} — {label}\n"
        await message.reply_text(text, parse_mode=ParseMode.HTML)
