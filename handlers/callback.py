import html
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.force_join import ForceJoinService
from services.google_sheet import GoogleSheetService
from services.shortener import ShortenerService
from services.storage import StorageService
from services.token_manager import TokenManager


class CallbackHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.shortener = ShortenerService(
            config.SHORTENER_API_KEY,
            config.SHORTENER_BASE_URL,
            config.SHORTENER_ALIAS,
            config.SHORTENER_RESPONSE_FORMAT,
        )
        self.force_join = ForceJoinService(config)
        self.token_manager = TokenManager(db)
        self.storage = StorageService(db, config)
        self.sheet = GoogleSheetService(config)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return

        await query.answer()
        data = query.data or ''
        user = query.from_user

        if data.startswith('dup_save_'):
            if not self.db.is_admin(user.id, self.config.ADMIN_IDS):
                await query.answer('Only admins can confirm duplicate uploads.', show_alert=True)
                return
            await self.storage.confirm_duplicate(data.replace('dup_save_', '', 1), query)
            return

        if data.startswith('dup_cancel_'):
            if not self.db.is_admin(user.id, self.config.ADMIN_IDS):
                await query.answer('Only admins can cancel duplicate uploads.', show_alert=True)
                return
            await self.storage.cancel_duplicate(data.replace('dup_cancel_', '', 1), query)
            return

        if data == 'adult_no':
            context.user_data.pop('adult_query', None)
            context.user_data.pop('adult_chat_id', None)
            await query.edit_message_text(
                '🔞 This search is not available for users under 18.',
                parse_mode=ParseMode.HTML,
            )
            return

        if data == 'adult_yes':
            search_text = context.user_data.pop('adult_query', None)
            expected_chat_id = context.user_data.pop('adult_chat_id', None)
            if not search_text or not query.message or query.message.chat.id != expected_chat_id:
                await query.edit_message_text('❌ This age confirmation has expired.')
                return
            await self._send_adult_search_results(query, context, search_text)
            return

        if data != 'check_join' and not await self.force_join.check_force_join(user.id):
            await query.edit_message_text(
                "🔒 <b>Access Denied</b>\n\nJoin the official channel and community group, then press <b>I've Joined</b>.",
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.force_join_menu(
                    self.config.CHANNEL_USERNAME,
                    self.config.GROUP_USERNAME,
                ),
            )
            return

        if data.startswith('download_'):
            try:
                await self.handle_download(query, int(data.split('_', 1)[1]), context)
            except ValueError:
                await query.edit_message_text('❌ Invalid movie button.')
            return

        if data.startswith('info_'):
            try:
                await self.handle_movie_info(query, int(data.split('_', 1)[1]))
            except ValueError:
                await query.edit_message_text('❌ Invalid movie button.')
            return

        if data == 'check_join':
            if await self.force_join.check_force_join(user.id):
                await query.edit_message_text('✅ Verification successful. Send /start again to continue.')
            else:
                await query.edit_message_text(
                    '❌ You are still not a member of both places.',
                    reply_markup=Keyboards.force_join_menu(
                        self.config.CHANNEL_USERNAME,
                        self.config.GROUP_USERNAME,
                    ),
                )

    async def _send_adult_search_results(self, query, context, text: str):
        movies = self.db.search_movies(text, self.config.MAX_MOVIES_PER_SEARCH)
        if not movies:
            await query.edit_message_text(
                f'❌ <b>No movie found</b>\n\nSearch: <code>{html.escape(text)}</code>',
                parse_mode=ParseMode.HTML,
            )
            return

        bot_info = await context.bot.get_me()
        username = bot_info.username or self.config.BOT_USERNAME
        lines = ['🔞 <b>18+ Search Results</b>', '']
        for index, movie in enumerate(movies, start=1):
            lines.append(
                f'{index}. <b>{html.escape(movie["title"])}</b> — {self.format_size(movie.get("file_size"))}'
            )
        lines.extend(['', 'Select your movie below.'])
        await query.edit_message_text(
            '\n'.join(lines),
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_buttons(movies, username),
        )
        self.db.add_message(
            query.message.chat.id,
            query.message.message_id,
            seconds=self.config.AUTO_DELETE_TIME,
        )

    async def handle_movie_info(self, query, movie_id: int):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text('❌ Movie not found or deleted.')
            return
        text = (
            '🎬 <b>Movie Information</b>\n\n'
            f"<b>Title:</b> {html.escape(movie['title'])}\n"
            f"<b>Size:</b> {self.format_size(movie['file_size'])}\n"
            f"<b>Views:</b> {movie['views']}\n"
            f"<b>Downloads:</b> {movie['downloads']}"
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(movie_id),
        )

    async def handle_download(self, query, movie_id: int, context: ContextTypes.DEFAULT_TYPE):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text('❌ Movie not found or deleted.')
            return

        token = self.token_manager.generate_token(movie_id, self.config.LINK_EXPIRE_TIME)
        bot_info = await context.bot.get_me()
        username = bot_info.username or self.config.BOT_USERNAME
        deep_link = f'https://t.me/{username}?start={token}'
        final_link = await self.shortener.shorten_link(deep_link)

        local_time = datetime.now(ZoneInfo(self.config.LOCAL_TIMEZONE)).strftime('%Y-%m-%d %I:%M:%S %p')
        username_text = f'@{query.from_user.username}' if query.from_user.username else ''
        event_id = self.db.log_link_event(
            event_type='Link Generated',
            movie_id=movie_id,
            user_id=query.from_user.id,
            username=username_text,
            event_time=local_time,
        )
        self.sheet.log_link_event(
            event_id=event_id,
            event_type='Link Generated',
            movie_id=movie_id,
            movie_name=movie['title'],
            user_id=query.from_user.id,
            username=username_text,
            event_time=local_time,
        )

        await query.edit_message_text(
            f"🎬 <b>{html.escape(movie['title'])}</b>\n\n"
            f"💾 File Size: <b>{self.format_size(movie['file_size'])}</b>\n\n"
            '✅ Your download link is ready.\n\n'
            '1️⃣ Tap <b>Click Here To Download Movie</b>.\n'
            '2️⃣ Wait about <b>20 seconds</b> on the shortener page.\n'
            '3️⃣ Return to Telegram; the movie file will appear in this chat.\n\n'
            '⏳ This message and link expire after <b>5 minutes</b>.',
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('🎬 Click Here To Download Movie', url=final_link)]
            ]),
            disable_web_page_preview=True,
        )
        self.db.add_message(
            query.message.chat.id,
            query.message.message_id,
            movie_id,
            self.config.AUTO_DELETE_TIME,
        )

    @staticmethod
    def format_size(size):
        if not size:
            return 'Unknown'
        value = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if value < 1024:
                return f'{value:.1f} {unit}'
            value /= 1024
        return f'{value:.1f} PB'
