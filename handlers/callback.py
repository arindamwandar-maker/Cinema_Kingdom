import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.force_join import ForceJoinService
from services.shortener import ShortenerService
from services.token_manager import TokenManager


class CallbackHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.shortener = ShortenerService(config.SHORTENER_API_KEY, config.SHORTENER_BASE_URL, config.SHORTENER_ALIAS)
        self.force_join = ForceJoinService(config)
        self.token_manager = TokenManager(db)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        await query.answer()
        data = query.data or ""
        user = query.from_user

        if data != "check_join" and not await self.force_join.check_force_join(user.id):
            await query.edit_message_text(
                "🔒 <b>Access Denied</b>\n\nJoin the official channel and community group, then press <b>I've Joined</b>.",
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.force_join_menu(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
            )
            return

        try:
            if data.startswith("download_"):
                await self.handle_download(query, int(data.split("_", 1)[1]), context)
                return
            if data.startswith("info_"):
                await self.handle_movie_info(query, int(data.split("_", 1)[1]))
                return
        except ValueError:
            await query.edit_message_text("❌ Invalid button data.")
            return

        if data == "request":
            await query.edit_message_text("🎥 <b>Movie Request</b>\n\nUse <code>/request Movie Name</code>.", parse_mode=ParseMode.HTML)
        elif data == "search":
            await query.edit_message_text("🔎 Type a movie name in the Cinema Kingdom group.")
        elif data == "check_join":
            if await self.force_join.check_force_join(user.id):
                await query.edit_message_text("✅ Verification successful. Send /start again to continue.")
            else:
                await query.edit_message_text(
                    "❌ You are still not a member of both places.",
                    reply_markup=Keyboards.force_join_menu(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
                )

    async def handle_movie_info(self, query, movie_id: int):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return
        text = (
            "🎬 <b>Movie Information</b>\n\n"
            f"<b>Title:</b> {html.escape(movie['title'])}\n"
            f"<b>Size:</b> {self.format_size(movie['file_size'])}\n"
            f"<b>Views:</b> {movie['views']}\n"
            f"<b>Downloads:</b> {movie['downloads']}"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=Keyboards.movie_button(movie_id))

    async def handle_download(self, query, movie_id: int, context: ContextTypes.DEFAULT_TYPE):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return

        token = self.token_manager.generate_token(movie_id, self.config.LINK_EXPIRE_TIME)
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username or self.config.BOT_USERNAME
        deep_link = f"https://t.me/{bot_username}?start={token}"
        short_link = await self.shortener.shorten_link(deep_link)

        text = (
            f"🎬 <b>{html.escape(movie['title'])}</b>\n\n"
            "✅ Your link is ready.\n\n"
            "Open the button below, complete the shortener page, and Telegram will return you to the bot for the file.\n\n"
            "⏳ Valid for <b>5 minutes</b>."
        )
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Open Download Link", url=short_link)]]),
        )
        self.db.add_message(query.message.chat.id, query.message.message_id, movie_id, self.config.AUTO_DELETE_TIME)

    @staticmethod
    def format_size(size):
        if not size:
            return "Unknown"
        size = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
