import html
import logging
import os
from datetime import datetime

from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services.google_sheet import GoogleSheetService


class StorageService:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.bot = Bot(token=config.BOT_TOKEN)
        self.storage_channel = config.STORAGE_CHANNEL
        self.sheet = GoogleSheetService(config)

    async def handle_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        if not message:
            return
        if message.chat.id != self.storage_channel:
            return

        media = message.document or message.video or message.audio or message.animation
        if media is None:
            return

        file_id = media.file_id
        file_size = getattr(media, "file_size", 0) or 0
        file_name = getattr(media, "file_name", "") or ""

        if message.caption:
            movie_title = message.caption.strip().splitlines()[0]
        elif file_name:
            movie_title = os.path.splitext(file_name)[0]
        else:
            movie_title = "Unknown Movie"

        if not movie_title or movie_title == "Unknown Movie":
            await message.reply_text("❌ Movie title not found. Please upload with caption or filename.")
            return

        exists = self.db.movie_exists(movie_title)
        if exists:
            await message.reply_text(
                "⚠️ <b>Movie Already Exists</b>\n\n"
                f"🎬 <b>Movie Name:</b> {html.escape(movie_title)}\n"
                f"🆔 <b>Movie ID:</b> #{exists['id']}",
                parse_mode=ParseMode.HTML,
            )
            return

        description = f"Original File: {file_name}" if file_name else ""
        if message.from_user:
            uploader = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
            uploaded_by_id = message.from_user.id
        else:
            uploader = "Channel Upload"
            uploaded_by_id = 0

        movie_id = self.db.add_movie(
            title=movie_title,
            description=description,
            file_id=file_id,
            file_size=file_size,
            uploaded_by=uploaded_by_id,
            tags=movie_title.lower(),
        )

        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_size_text = self.format_size(file_size)

        try:
            self.sheet.add_storage_upload(
                movie_name=movie_title,
                movie_id=movie_id,
                uploaded_by=uploader,
                upload_time=upload_time,
                file_size=file_size_text,
            )
        except Exception as exc:
            logging.warning("Storage upload sheet failed: %s", exc)

        logging.info("Movie saved: %s (%s)", movie_title, movie_id)
        await message.reply_text(
            "✅ <b>Movie Added Successfully</b>\n\n"
            f"🎬 <b>Movie Name:</b> {html.escape(movie_title)}\n"
            f"🆔 <b>Movie ID:</b> #{movie_id}\n"
            f"👤 <b>Upload By:</b> {html.escape(uploader)}\n"
            f"🕒 <b>Date & Time:</b> {html.escape(upload_time)}\n"
            f"💾 <b>File Size:</b> {html.escape(file_size_text)}\n\n"
            "📁 Stored successfully and searchable in Cinema Kingdom.",
            parse_mode=ParseMode.HTML,
        )

    @staticmethod
    def format_size(size):
        if not size:
            return "Unknown"
        size = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
