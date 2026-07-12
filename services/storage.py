import html
import logging
import os
import secrets
import time
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.google_sheet import GoogleSheetService


class StorageService:
    pending_duplicates = {}

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

        user = update.effective_user
        if user:
            uploader = f'@{user.username}' if user.username else str(user.id)
            uploader_id = user.id
        else:
            uploader = 'Channel Admin'
            uploader_id = 0

        payload = {
            'movie_title': movie_title,
            'file_id': file_id,
            'file_size': file_size,
            'file_name': file_name,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'source_chat_id': chat.id,
            'source_message_id': message.message_id,
            'created_at': time.time(),
        }

        exists = self.db.movie_exists(movie_title)
        if exists:
            token = secrets.token_urlsafe(8)
            self.pending_duplicates[token] = payload
            await message.reply_text(
                '⚠️ <b>Duplicate Movie Detected</b>\n\n'
                f'🎬 Movie: <b>{html.escape(movie_title)}</b>\n'
                f'🆔 Existing Movie ID: <code>{exists["id"]}</code>\n\n'
                'Do you want to save this upload as another entry?',
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.duplicate_confirmation(token),
            )
            return

        await self._save_payload(payload, message)

    async def confirm_duplicate(self, token: str, query):
        payload = self.pending_duplicates.pop(token, None)
        if not payload:
            await query.edit_message_text('❌ This duplicate confirmation has expired.')
            return
        await self._save_payload(payload, query.message, edit_existing=True)

    async def cancel_duplicate(self, token: str, query):
        payload = self.pending_duplicates.pop(token, None)
        title = payload['movie_title'] if payload else 'Movie'
        await query.edit_message_text(
            f'❌ Duplicate upload cancelled.\n\n🎬 {html.escape(title)}',
            parse_mode=ParseMode.HTML,
        )

    async def _save_payload(self, payload, reply_message, edit_existing=False):
        movie_id = self.db.add_movie(
            title=payload['movie_title'],
            description=f"Original File: {payload['file_name']}" if payload['file_name'] else '',
            file_id=payload['file_id'],
            file_size=payload['file_size'],
            uploaded_by=payload['uploader_id'],
            tags=payload['movie_title'].lower(),
            source_chat_id=payload['source_chat_id'],
            source_message_id=payload['source_message_id'],
        )

        upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        size_text = self.format_size(payload['file_size'])
        sheet_ok = self.sheet.add_storage_upload(
            payload['movie_title'],
            movie_id,
            payload['uploader'],
            upload_time,
            size_text,
            payload['file_id'],
        )

        text = (
            '✅ <b>Movie Added Successfully</b>\n\n'
            f'🎬 <b>Movie Name:</b> {html.escape(payload["movie_title"])}\n'
            f'🆔 <b>Movie ID:</b> <code>{movie_id}</code>\n'
            f'👤 <b>Upload By:</b> {html.escape(payload["uploader"])}\n'
            f'🕒 <b>Date & Time:</b> {upload_time}\n'
            f'💾 <b>File Size:</b> {size_text}\n\n'
            f'{"✅ Google Sheet updated" if sheet_ok else "⚠️ Google Sheet not updated"}\n'
            f'🗑 Delete: <code>/delete {movie_id}</code>'
        )

        if edit_existing:
            await reply_message.edit_text(text, parse_mode=ParseMode.HTML)
        else:
            await reply_message.reply_text(text, parse_mode=ParseMode.HTML)

        logging.info('Movie saved: %s (%s)', payload['movie_title'], movie_id)

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
