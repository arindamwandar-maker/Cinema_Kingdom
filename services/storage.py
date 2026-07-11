import html
import logging
import os
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.google_sheet import GoogleSheetService


class StorageService:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)

    async def handle_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        chat = update.effective_chat
        if not message or not chat or chat.id != self.config.STORAGE_CHANNEL:
            return

        media = message.document or message.video or message.audio or message.animation
        if media is None:
            return

        file_id = media.file_id
        file_size = getattr(media, 'file_size', 0) or 0
        file_name = getattr(media, 'file_name', '') or ''

        movie_title = ''
        if message.caption:
            movie_title = message.caption.strip().splitlines()[0]
        if not movie_title and file_name:
            movie_title = os.path.splitext(file_name)[0]
        if not movie_title:
            await message.reply_text('❌ Add the movie name as caption or filename.')
            return

        exists = self.db.movie_exists(movie_title)
        if exists:
            await message.reply_text(
                '⚠️ <b>Movie Already Exists</b>\n\n'
                f'🎬 {html.escape(movie_title)}\n'
                f'🆔 Movie ID: <code>{exists["id"]}</code>\n\n'
                f'Delete with <code>/delete {exists["id"]}</code>.',
                parse_mode=ParseMode.HTML,
            )
            return

        user = update.effective_user
        if user:
            uploader = f'@{user.username}' if user.username else str(user.id)
            uploader_id = user.id
        else:
            uploader = 'Channel Admin'
            uploader_id = 0

        movie_id = self.db.add_movie(
            title=movie_title,
            description=f'Original File: {file_name}' if file_name else '',
            file_id=file_id,
            file_size=file_size,
            uploaded_by=uploader_id,
            tags=movie_title.lower(),
            source_chat_id=chat.id,
            source_message_id=message.message_id,
        )

        upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        size_text = self.format_size(file_size)
        sheet_ok = self.sheet.add_storage_upload(
            movie_title, movie_id, uploader, upload_time, size_text, file_id
        )

        await message.reply_text(
            '✅ <b>Movie Added Successfully</b>\n\n'
            f'🎬 <b>Movie Name:</b> {html.escape(movie_title)}\n'
            f'🆔 <b>Movie ID:</b> <code>{movie_id}</code>\n'
            f'👤 <b>Upload By:</b> {html.escape(uploader)}\n'
            f'🕒 <b>Date & Time:</b> {upload_time}\n'
            f'💾 <b>File Size:</b> {size_text}\n\n'
            f'{"✅ Google Sheet updated" if sheet_ok else "⚠️ Google Sheet not updated"}\n'
            f'🗑 Delete: <code>/delete {movie_id}</code>',
            parse_mode=ParseMode.HTML,
        )
        logging.info('Movie saved: %s (%s)', movie_title, movie_id)

    @staticmethod
    def format_size(size):
        if not size:
            return 'Unknown'
        value = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if value < 1024:
                return f'{value:.2f} {unit}'
            value /= 1024
        return f'{value:.2f} PB'
