from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.google_sheet import GoogleSheetService


class RequestHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)

    async def request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.effective_user:
            return
        user = update.effective_user
        text = update.message.text.strip()

        if len(text.split(maxsplit=1)) < 2:
            await update.message.reply_text(
                "🎥 **Movie Request**\n\nUsage:\n`/request Movie Name`\n\nExample:\n`/request Avengers Endgame`",
                parse_mode="Markdown",
            )
            return

        movie_name = text.split(maxsplit=1)[1].strip()
        await self.process_request(update, context, user, movie_name)

    async def process_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user, movie_name: str):
        self.db.add_or_update_user(user.id, user.username or "", user.first_name or "", user.last_name or "")
        request_id = self.db.add_request(user.id, movie_name)
        self.db.increment_user_requests(user.id)

        try:
            self.sheet.add_request(
                request_id=request_id,
                user_id=user.id,
                username=user.username or "",
                first_name=user.first_name or "",
                movie_name=movie_name,
                request_time=datetime.now(),
            )
        except Exception as exc:
            print("Google Sheet Error:", exc)

        admin_text = (
            "🎬 New Movie Request\n\n"
            f"👤 User : {user.first_name or ''}\n"
            f"📎 Username : @{user.username or 'None'}\n"
            f"🆔 User ID : {user.id}\n"
            f"🎥 Movie : {movie_name}\n"
            f"📝 Request ID : #{request_id}"
        )
        for admin in self.config.ADMIN_IDS:
            try:
                await context.bot.send_message(admin, admin_text)
            except Exception:
                pass

        await update.message.reply_text(
            "✅ **Request Submitted Successfully!**\n\n"
            f"🎥 Movie : **{movie_name}**\n"
            f"📝 Request ID : **#{request_id}**\n\n"
            "Your request has been saved.\n"
            "We will upload the movie as soon as possible.\n\n"
            "Thank you for using Cinema Kingdom ❤️",
            parse_mode="Markdown",
        )
