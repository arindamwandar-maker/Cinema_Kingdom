import logging
import os

from telegram import Bot, Update
from telegram.ext import ContextTypes


class StorageService:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.bot = Bot(token=config.BOT_TOKEN)
        self.storage_channel = config.STORAGE_CHANNEL

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
                "⚠️ This movie already exists in database.\n\n"
                f"🎬 {movie_title}\n"
                f"🆔 Movie ID: #{exists['id']}"
            )
            return

        description = f"Original File: {file_name}" if file_name else ""
        movie_id = self.db.add_movie(
            title=movie_title,
            description=description,
            file_id=file_id,
            file_size=file_size,
            uploaded_by=message.from_user.id if message.from_user else 0,
            tags=movie_title.lower(),
        )
        logging.info("Movie saved: %s (%s)", movie_title, movie_id)
        await message.reply_text(
            "✅ **Movie Saved Successfully**\n\n"
            f"🎬 **Title:** {movie_title}\n"
            f"🆔 **Movie ID:** #{movie_id}\n"
            f"💾 **Size:** {self.format_size(file_size)}\n\n"
            "The movie is now searchable in Cinema Kingdom.",
            parse_mode="Markdown",
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
