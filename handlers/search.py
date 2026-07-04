from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards


class SearchHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        user = update.effective_user
        if not message or not message.text or not user:
            return

        text = message.text.strip()
        self.db.add_or_update_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

        if text.startswith("/"):
            return

        if text in ["🎬 Search Movie", "🎥 Request Movie", "📢 Join Channel", "👥 Join Group", "ℹ️ Help"]:
            if text == "ℹ️ Help":
                await message.reply_text(self.config.HELP_MSG, parse_mode="Markdown", reply_markup=Keyboards.main_menu())
            elif text == "🎥 Request Movie":
                await message.reply_text("🎥 Send request like this:\n\n`/request Movie Name`", parse_mode="Markdown")
            elif text == "📢 Join Channel":
                await message.reply_text(f"📢 Join: https://t.me/{self.config.CHANNEL_USERNAME.replace('@','')}")
            elif text == "👥 Join Group":
                await message.reply_text(f"👥 Join: https://t.me/{self.config.GROUP_USERNAME.replace('@','')}")
            else:
                await message.reply_text("🎬 Type any movie name to search.")
            return

        if update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
            if not self.db.check_cooldown(user.id, self.config.COOLDOWN_TIME):
                remain = self.db.cooldown_remaining(user.id, self.config.COOLDOWN_TIME)
                warn = await message.reply_text(
                    f"⏳ Please wait {remain} seconds before searching again.",
                    reply_to_message_id=message.message_id,
                )
                self.db.add_message(warn.chat.id, warn.message_id, seconds=self.config.AUTO_DELETE_TIME)
                return

        movies = self.db.search_movies(text, self.config.MAX_MOVIES_PER_SEARCH)
        if not movies:
            not_found = await message.reply_text(
                f"❌ No movie found for **{text}**.\n\nUse `/request {text}` to request it.",
                parse_mode="Markdown",
                reply_to_message_id=message.message_id if update.effective_chat.type in ("group", "supergroup") else None,
            )
            self.db.add_message(not_found.chat.id, not_found.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        result = f"🎬 **Search Results**\n\nFound **{len(movies)}** movie(s).\n\nSelect your movie below."
        sent = await message.reply_text(
            result,
            parse_mode="Markdown",
            reply_markup=Keyboards.movie_buttons(movies),
            reply_to_message_id=message.message_id if update.effective_chat.type in ("group", "supergroup") else None,
        )
        self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
