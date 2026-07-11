import html
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
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
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return
        text = (message.text or '').strip()
        chat = update.effective_chat
        if chat and chat.id == self.config.GROUP_ID:
            self.db.add_message(chat.id, message.message_id, seconds=self.config.AUTO_DELETE_TIME)
        if len(text.split(maxsplit=1)) < 2:
            await message.reply_text('🎥 <b>Movie Request</b>\n\nUse: <code>/request Movie Name</code>', parse_mode=ParseMode.HTML)
            return
        movie_name = text.split(maxsplit=1)[1].strip()
        self.db.add_or_update_user(user.id, user.username or '', user.first_name or '', user.last_name or '')
        request_id = self.db.add_request(user.id, movie_name)
        self.db.increment_user_requests(user.id)
        sheet_ok = self.sheet.add_request(request_id, user.id, user.username or '', user.first_name or '', movie_name, datetime.now())

        for admin in self.config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin,
                    f'🎬 New Movie Request\n\n👤 {user.first_name or ""}\n📎 @{user.username or "None"}\n🆔 {user.id}\n🎥 {movie_name}\n📝 #{request_id}',
                )
            except Exception:
                pass

        sent = await message.reply_text(
            '✅ <b>Request Submitted</b>\n\n'
            f'🎥 {html.escape(movie_name)}\n📝 Request ID: <code>{request_id}</code>\n\n'
            f'{"✅ Google Sheet updated" if sheet_ok else "⚠️ Google Sheet not updated"}',
            parse_mode=ParseMode.HTML,
        )
        self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
