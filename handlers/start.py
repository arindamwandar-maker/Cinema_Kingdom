from telegram import Update
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
        message = update.message
        user = update.effective_user
        if not message or not user:
            return

        self.db.add_or_update_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

        if context.args:
            token = context.args[0]
            joined = await self.force_join.check_force_join(user.id)
            if not joined:
                await self.force_join_message(update)
                return

            movie_id = self.token_manager.verify_token(token)
            if movie_id is None:
                await message.reply_text(
                    "❌ This download link has expired.\n\nPlease return to the bot and generate a new download link."
                )
                return

            movie = self.db.get_movie(movie_id)
            if not movie:
                await message.reply_text("❌ Movie not found.")
                return

            self.token_manager.remove_token(token)
            await message.reply_document(
                document=movie["file_id"],
                caption=(
                    f"🎬 **{movie['title']}**\n\n"
                    "✅ Download started successfully.\n\n"
                    "🍿 Enjoy your movie!\n\n"
                    "❤️ Thank you for using Cinema Kingdom."
                ),
                parse_mode="Markdown",
            )
            return

        joined = await self.force_join.check_force_join(user.id)
        if not joined:
            await self.force_join_message(update)
            return

        await message.reply_text(
            text=self.config.WELCOME_MSG.format(first_name=user.first_name or "Friend"),
            parse_mode="Markdown",
            reply_markup=Keyboards.main_menu(),
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text(
                text=self.config.HELP_MSG,
                parse_mode="Markdown",
                reply_markup=Keyboards.main_menu(),
            )

    async def force_join_message(self, update: Update):
        if not update.message:
            return
        text = (
            "🔒 **Access Restricted**\n\n"
            "To use **Cinema Kingdom**, you must join our official Channel and Community Group first.\n\n"
            "📢 Join the Update Channel\n"
            "👥 Join the Community Group\n\n"
            "After joining both, press **✅ I've Joined**."
        )
        await update.message.reply_text(text=text, parse_mode="Markdown", reply_markup=Keyboards.force_join_menu())

    async def send_movie_message(self, update: Update, movie: dict):
        if not update.message:
            return
        text = (
            f"🎬 **{movie['title']}**\n\n"
            "Your movie is ready.\n\n"
            "👇 Click **Generate Download Link** below.\n\n"
            "🔐 A secure download link will be created.\n"
            "⏳ The link will remain valid for only **5 minutes**."
        )
        await update.message.reply_text(text=text, parse_mode="Markdown", reply_markup=Keyboards.movie_button(movie["id"]))
