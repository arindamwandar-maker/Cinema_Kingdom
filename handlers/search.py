import html

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards


class SearchHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

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

    def is_adult_query(self, text: str) -> bool:
        lowered = (text or '').lower()
        return any(keyword in lowered for keyword in self.config.ADULT_KEYWORDS)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        if not message or not user or not chat or not message.text:
            return

        text = message.text.strip()
        self.db.add_or_update_user(user.id, user.username or '', user.first_name or '', user.last_name or '')

        if chat.id == self.config.GROUP_ID and chat.type in ('group', 'supergroup'):
            self.db.add_message(chat.id, message.message_id, seconds=self.config.AUTO_DELETE_TIME)

        if text == '🎬 Search Movie':
            if chat.type == 'private':
                sent = await message.reply_text(
                    f'🔒 <b>Private Search Disabled</b>\n\nSearch movies in the Cinema Kingdom group.',
                    parse_mode=ParseMode.HTML,
                    reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
                )
            else:
                sent = await message.reply_text(
                    '🎬 <b>Search Movie</b>\n\nType the movie name now.\nExample: <code>Avengers</code>',
                    parse_mode=ParseMode.HTML,
                )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '🎥 Request Movie':
            sent = await message.reply_text(
                '🎥 <b>Request Movie</b>\n\nUse: <code>/request Movie Name</code>',
                parse_mode=ParseMode.HTML,
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '📢 Join Channel':
            sent = await message.reply_text(
                '📢 Open the official update channel below.',
                reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '👥 Join Group':
            sent = await message.reply_text(
                '👥 Open the Cinema Kingdom community group below.',
                reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == 'ℹ️ Help':
            sent = await message.reply_text(
                self.config.HELP_MSG,
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.main_menu(),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if chat.type == 'private':
            sent = await message.reply_text(
                '🔒 <b>Private Search Disabled</b>\n\nUse the Cinema Kingdom group to search.',
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if chat.id != self.config.GROUP_ID:
            return

        if not self.db.is_admin(user.id, self.config.ADMIN_IDS) and self.config.COOLDOWN_TIME > 0:
            if not self.db.check_cooldown(user.id, self.config.COOLDOWN_TIME):
                remain = self.db.cooldown_remaining(user.id, self.config.COOLDOWN_TIME)
                warn = await message.reply_text(
                    f'⏳ <b>Please wait</b>\n\nYou can search again in <b>{remain} seconds</b>.',
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=message.message_id,
                )
                self.db.add_message(warn.chat.id, warn.message_id, seconds=min(remain + 2, self.config.AUTO_DELETE_TIME))
                return

        if self.is_adult_query(text):
            context.user_data['adult_query'] = text
            context.user_data['adult_chat_id'] = chat.id
            confirm = await message.reply_text(
                '🔞 <b>Age Confirmation Required</b>\n\nThis search may contain 18+ content. Please confirm that you are 18 years old or above.',
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.adult_confirmation(),
                reply_to_message_id=message.message_id,
            )
            self.db.add_message(confirm.chat.id, confirm.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        await self.send_search_results(message, context, text)

    async def send_search_results(self, message, context, text: str):
        movies = self.db.search_movies(text, self.config.MAX_MOVIES_PER_SEARCH)
        if not movies:
            safe = html.escape(text)
            sent = await message.reply_text(
                f'❌ <b>No movie found</b>\n\nSearch: <code>{safe}</code>\n\nRequest it using <code>/request {safe}</code>.',
                parse_mode=ParseMode.HTML,
                reply_to_message_id=message.message_id,
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        bot_info = await context.bot.get_me()
        username = bot_info.username or self.config.BOT_USERNAME

        lines = ['🎬 <b>Search Results</b>', '']
        for index, movie in enumerate(movies, start=1):
            title = html.escape(movie['title'])
            size = self.format_size(movie.get('file_size'))
            lines.append(f'{index}. <b>{title}</b> — {size}')
        lines.extend(['', 'Select your movie below.'])

        result = await message.reply_text(
            '\n'.join(lines),
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_buttons(movies, username),
            reply_to_message_id=message.message_id,
        )
        self.db.add_message(result.chat.id, result.message_id, seconds=self.config.AUTO_DELETE_TIME)
