import html
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.force_join import ForceJoinService
from services.google_sheet import GoogleSheetService
from services.token_manager import TokenManager


class StartHandler:
    def __init__(self, db: Database, config: Config, bot=None):
        self.db = db
        self.config = config
        self.force_join = ForceJoinService(config, bot)
        self.token_manager = TokenManager(db)
        self.sheet = GoogleSheetService(config)

    def link_line(self, emoji: str, username: str, label: str, prefix: str = ''):
        if not username:
            return None
        return (
            f'{emoji} <a href="https://t.me/{username}">'
            f'{prefix}{html.escape(label)}</a>'
        )

    def delivery_caption(self, title: str) -> str:
        """Caption shipped with the movie file: title, note and our links."""
        lines = [
            f'🎬 <b>{html.escape(title)}</b>',
            '',
            '✅ File delivered. Enjoy watching!',
            '',
        ]

        for line in (
            self.link_line('👥', self.config.GROUP_USERNAME, self.config.GROUP_NAME),
            self.link_line('📢', self.config.CHANNEL_USERNAME, self.config.CHANNEL_NAME),
        ):
            if line:
                lines.append(line)

        if self.config.FILE_CAPTION_NOTE:
            lines.extend(['', html.escape(self.config.FILE_CAPTION_NOTE)])

        return '\n'.join(lines)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return

        self.db.add_or_update_user(user.id, user.username or '', user.first_name or '', user.last_name or '')

        if context.args:
            payload = context.args[0]
            if not await self.force_join.check_force_join(user.id):
                await self.force_join_message(update)
                return

            # Group search opens the bot with movie_<id> and shows the download button.
            if payload.startswith('movie_'):
                try:
                    movie_id = int(payload.split('_', 1)[1])
                except ValueError:
                    await message.reply_text('❌ Invalid movie link.')
                    return
                movie = self.db.get_movie(movie_id)
                if not movie:
                    await message.reply_text('❌ Movie not found or deleted.')
                    return
                self.db.increment_views(movie_id)
                await self.send_movie_message(update, movie)
                return

            # A secure shortener return token delivers the file.
            movie_id = self.token_manager.verify_token(payload)
            if movie_id is None:
                sent = await message.reply_text('❌ This download link expired or is invalid. Generate a new link.')
                self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
                self.sheet.log_download_status(
                    status='Link Expired',
                    movie_name='',
                    movie_id='',
                    user_id=user.id,
                    username=f'@{user.username}' if user.username else '',
                    event_time=datetime.now(ZoneInfo(self.config.LOCAL_TIMEZONE)).strftime('%Y-%m-%d %I:%M:%S %p'),
                )
                return

            movie = self.db.get_movie(movie_id)
            self.token_manager.remove_token(payload)
            if not movie:
                await message.reply_text('❌ Movie not found or deleted.')
                return

            self.db.increment_downloads(movie_id)
            local_time = datetime.now(ZoneInfo(self.config.LOCAL_TIMEZONE)).strftime('%Y-%m-%d %I:%M:%S %p')
            username_text = f'@{user.username}' if user.username else ''
            event_id = self.db.log_link_event(
                event_type='File Delivered',
                movie_id=movie_id,
                user_id=user.id,
                username=username_text,
                event_time=local_time,
            )
            self.sheet.log_link_event(
                event_id=event_id,
                event_type='File Delivered',
                movie_id=movie_id,
                movie_name=movie['title'],
                user_id=user.id,
                username=username_text,
                event_time=local_time,
            )
            self.sheet.log_download_status(
                status='File Delivered',
                movie_name=movie['title'],
                movie_id=movie_id,
                user_id=user.id,
                username=username_text,
                event_time=local_time,
            )
            sent = await message.reply_document(
                document=movie['file_id'],
                caption=self.delivery_caption(movie['title']),
                parse_mode=ParseMode.HTML,
            )
            self.db.add_message(sent.chat.id, sent.message_id, movie_id, self.config.AUTO_DELETE_TIME)
            return

        if not await self.force_join.check_force_join(user.id):
            await self.force_join_message(update)
            return

        await message.reply_text(
            self.config.WELCOME_MSG.format(first_name=html.escape(user.first_name or 'Friend')),
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.main_menu(),
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        if message:
            await message.reply_text(self.config.HELP_MSG, parse_mode=ParseMode.HTML, reply_markup=Keyboards.main_menu())

    async def force_join_message(self, update: Update):
        message = update.effective_message
        user = update.effective_user
        if not message:
            return

        reason = ""

        if (
            user
            and self.force_join.last_reason
            and self.db.is_admin(user.id, self.config.ADMIN_IDS)
        ):
            reason = f"\n\n<i>{html.escape(self.force_join.last_reason)}</i>"

        await message.reply_text(
            "🔒 <b>Access Restricted</b>\n\nJoin the official channel and community group first, then press <b>I've Joined</b>." + reason,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.force_join_menu(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
        )

    async def send_movie_message(self, update: Update, movie: dict):
        message = update.effective_message
        if not message:
            return

        lines = [f"🎬 <b>{html.escape(movie['title'])}</b>", '']
        uploader = (movie.get('uploaded_by_name') or '').strip()

        if uploader:
            lines.append(f'📤 Uploaded by: {html.escape(uploader)}')

        lines.extend([
            '',
            'Click below to generate the download link.',
            '',
            '⏳ Link validity: 5 minutes.',
        ])

        sent = await message.reply_text(
            '\n'.join(lines),
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(movie['id']),
        )
        self.db.add_message(sent.chat.id, sent.message_id, movie['id'], self.config.AUTO_DELETE_TIME)
