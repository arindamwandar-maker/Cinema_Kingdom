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

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        if not message or not user or not chat or not message.text:
            return

        text = message.text.strip()
        self.db.add_or_update_user(user.id, user.username or '', user.first_name or '', user.last_name or '')

        # Every user message in the main group is removed after 5 minutes.
        if chat.id == self.config.GROUP_ID and chat.type in ('group', 'supergroup'):
            self.db.add_message(chat.id, message.message_id, seconds=self.config.AUTO_DELETE_TIME)

        # Menu buttons work in both private chat and group.
        if text == '🎬 Search Movie':
            if chat.type == 'private':
                sent = await message.reply_text(
                    f'🔒 <b>Private Search Disabled</b>\n\nSearch movies in the Cinema Kingdom group:\nhttps://t.me/{self.config.GROUP_USERNAME}',
                    parse_mode=ParseMode.HTML,
                )
            else:
                sent = await message.reply_text('🎬 <b>Search Movie</b>\n\nType the movie name now.\nExample: <code>Avengers</code>', parse_mode=ParseMode.HTML)
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '🎥 Request Movie':
            sent = await message.reply_text('🎥 <b>Request Movie</b>\n\nUse: <code>/request Movie Name</code>', parse_mode=ParseMode.HTML)
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '📢 Join Channel':
            sent = await message.reply_text(f'📢 Join here:\nhttps://t.me/{self.config.CHANNEL_USERNAME}')
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '👥 Join Group':
            sent = await message.reply_text(f'👥 Join here:\nhttps://t.me/{self.config.GROUP_USERNAME}')
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == 'ℹ️ Help':
            sent = await message.reply_text(self.config.HELP_MSG, parse_mode=ParseMode.HTML, reply_markup=Keyboards.main_menu())
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if chat.type == 'private':
            sent = await message.reply_text(
                f'🔒 <b>Private Search Disabled</b>\n\nUse the Cinema Kingdom group to search:\nhttps://t.me/{self.config.GROUP_USERNAME}',
                parse_mode=ParseMode.HTML,
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
        result = await message.reply_text(
            f'🎬 <b>Search Results</b>\n\nFound <b>{len(movies)}</b> movie(s). Select one below.',
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_buttons(movies, username),
            reply_to_message_id=message.message_id,
        )
        self.db.add_message(result.chat.id, result.message_id, seconds=self.config.AUTO_DELETE_TIME)
