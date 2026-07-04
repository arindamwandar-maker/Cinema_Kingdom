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
        self.token_manager = TokenManager()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return

        self.db.add_or_update_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

        if context.args:
            payload = context.args[0]
            joined = await self.force_join.check_force_join(user.id)
            if not joined:
                await self.force_join_message(update)
                return

            if payload.startswith("movie_"):
                try:
                    movie_id = int(payload.replace("movie_", "", 1))
                except ValueError:
                    await message.reply_text("❌ Invalid movie link.")
                    return
                movie = self.db.get_movie(movie_id)
                if not movie:
                    await message.reply_text("❌ Movie not found.")
                    return
                await self.send_movie_message(update, movie)
                return

            movie_id = self.token_manager.verify_token(payload)
            if movie_id is None:
                await message.reply_text(
                    "❌ This download link has expired or is invalid.\n\nPlease return to the bot and generate a new download link."
                )
                return

            movie = self.db.get_movie(movie_id)
            self.token_manager.remove_token(payload)
            if not movie:
                await message.reply_text("❌ Movie not found.")
                return

            self.db.increment_downloads(movie_id)
            title = html.escape(movie["title"])
            await message.reply_document(
                document=movie["file_id"],
                caption=(
                    f"🎬 <b>{title}</b>\n\n"
                    "✅ Download started successfully.\n\n"
                    "🍿 Enjoy your movie!\n\n"
                    "❤️ Thank you for using Cinema Kingdom."
                ),
                parse_mode=ParseMode.HTML,
            )
            return

        joined = await self.force_join.check_force_join(user.id)
        if not joined:
            await self.force_join_message(update)
            return

        await message.reply_text(
            text=self.config.WELCOME_MSG.format(first_name=html.escape(user.first_name or "Friend")),
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.main_menu(),
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        if message:
            await message.reply_text(text=self.config.HELP_MSG, parse_mode=ParseMode.HTML, reply_markup=Keyboards.main_menu())

    async def force_join_message(self, update: Update):
        message = update.effective_message
        if not message:
            return
        text = (
            "🔒 <b>Access Restricted</b>\n\n"
            "To use <b>Cinema Kingdom</b>, you must join our official Channel and Community Group first.\n\n"
            "📢 Join the Update Channel\n"
            "👥 Join the Community Group\n\n"
            "After joining both, press <b>✅ I've Joined</b>."
        )
        await message.reply_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.force_join_menu(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
        )

    async def send_movie_message(self, update: Update, movie: dict):
        message = update.effective_message
        if not message:
            return
        title = html.escape(movie["title"])
        text = (
            f"🎬 <b>{title}</b>\n\n"
            "Your movie is ready.\n\n"
            "👇 Click <b>Generate Download Link</b> below.\n\n"
            "🔐 A secure shortener download link will be created.\n"
            "⏳ The link will remain valid for only <b>5 minutes</b>."
        )
        await message.reply_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(movie["id"]),
        )
