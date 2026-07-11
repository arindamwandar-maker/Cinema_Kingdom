import html
import logging
import os
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services.google_sheet import GoogleSheetService


class StorageService:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.storage_channel = config.STORAGE_CHANNEL
        self.sheet = GoogleSheetService(config)

    async def handle_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        if not message or message.chat.id != self.storage_channel:
            return

        media = message.document or message.video or message.audio or message.animation
        if media is None:
            return

        file_id = media.file_id
        file_size = getattr(media, "file_size", 0) or 0
        file_name = getattr(media, "file_name", "") or ""
        movie_title = (message.caption or "").strip().splitlines()[0] if message.caption else ""
        if not movie_title and file_name:
            movie_title = os.path.splitext(file_name)[0]
        if not movie_title:
            await message.reply_text("❌ Movie title not found. Add a caption or use a filename.")
            return

        exists = self.db.movie_exists(movie_title)
        if exists:
            await message.reply_text(
                "⚠️ <b>Movie Already Exists</b>\n\n"
                f"🎬 <b>Movie Name:</b> {html.escape(movie_title)}\n"
                f"🆔 <b>Movie ID:</b> #{exists['id']}\n\n"
                f"Delete it here with <code>/delete {exists['id']}</code> if needed.",
                parse_mode=ParseMode.HTML,
            )
            return

        if message.from_user:
            uploader = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
            uploaded_by_id = message.from_user.id
        else:
            uploader = "Channel Admin"
            uploaded_by_id = 0

        movie_id = self.db.add_movie(
            title=movie_title,
            description=f"Original File: {file_name}" if file_name else "",
            file_id=file_id,
            file_size=file_size,
            uploaded_by=uploaded_by_id,
            tags=movie_title.lower(),
            source_chat_id=message.chat.id,
            source_message_id=message.message_id,
        )

        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_size_text = self.format_size(file_size)
        sheet_saved = self.sheet.add_storage_upload(movie_title, movie_id, uploader, upload_time, file_size_text)
        sheet_status = "✅ Google Sheet updated" if sheet_saved else "⚠️ Google Sheet not updated"

        await message.reply_text(
            "✅ <b>Movie Added Successfully</b>\n\n"
            f"🎬 <b>Movie Name:</b> {html.escape(movie_title)}\n"
            f"🆔 <b>Movie ID:</b> #{movie_id}\n"
            f"👤 <b>Upload By:</b> {html.escape(uploader)}\n"
            f"🕒 <b>Date & Time:</b> {upload_time}\n"
            f"💾 <b>File Size:</b> {file_size_text}\n\n"
            f"{sheet_status}\n"
            f"🗑 Delete command: <code>/delete {movie_id}</code>",
            parse_mode=ParseMode.HTML,
        )
        logging.info("Movie saved: %s (%s)", movie_title, movie_id)

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
