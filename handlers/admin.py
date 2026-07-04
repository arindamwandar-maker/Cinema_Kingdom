from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import Database


class AdminHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.config.ADMIN_IDS

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
        await update.message.reply_text(
            "📊 Cinema Kingdom Statistics\n\n"
            f"🎬 Movies : {movies}\n"
            f"👤 Users : {users}\n"
            f"📥 Pending Requests : {pending}\n"
            f"⬇ Total Downloads : {downloads}"
        )

    async def requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not self.is_admin(update.effective_user.id):
            return
        requests = self.db.get_pending_requests()
        if not requests:
            await update.message.reply_text("✅ No pending movie requests.")
            return
        text = "🎬 Pending Requests\n\n"
        for req in requests[:20]:
            text += f"🆔 #{req['id']}\n👤 {req.get('first_name') or 'Unknown'}\n🎥 {req['movie_title']}\n\n"
        await update.message.reply_text(text)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not self.is_admin(update.effective_user.id):
            return
        if not context.args:
            await update.message.reply_text("Usage:\n/broadcast Your Message")
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
        await update.message.reply_text(f"✅ Broadcast completed.\n\nDelivered : {success}")
