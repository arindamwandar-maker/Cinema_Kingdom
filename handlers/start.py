import html

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.force_join import ForceJoinService
from services.token_manager import TokenManager


class StartHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.force_join = ForceJoinService(config)
        self.token_manager = TokenManager(db)

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
                return

            movie = self.db.get_movie(movie_id)
            self.token_manager.remove_token(payload)
            if not movie:
                await message.reply_text('❌ Movie not found or deleted.')
                return

            self.db.increment_downloads(movie_id)
            sent = await message.reply_document(
                document=movie['file_id'],
                caption=f"🎬 <b>{html.escape(movie['title'])}</b>\n\n✅ File delivered. Enjoy watching!",
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
        if not message:
            return
        await message.reply_text(
            "🔒 <b>Access Restricted</b>\n\nJoin the official channel and community group first, then press <b>I've Joined</b>.",
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.force_join_menu(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
        )

    async def send_movie_message(self, update: Update, movie: dict):
        message = update.effective_message
        if not message:
            return
        sent = await message.reply_text(
            f"🎬 <b>{html.escape(movie['title'])}</b>\n\nClick below to generate the download link.\n\n⏳ Link validity: 5 minutes.",
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(movie['id']),
        )
        self.db.add_message(sent.chat.id, sent.message_id, movie['id'], self.config.AUTO_DELETE_TIME)
