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
        message = update.effective_message
        user = update.effective_user
        if not message or not message.text or not user:
            return

        text = message.text.strip()
        self.db.add_or_update_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

        if text.startswith("/"):
            return
        if text in {"🎬 Search Movie", "🎥 Request Movie", "📢 Join Channel", "👥 Join Group", "ℹ️ Help"}:
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
                f"❌ Movie not found for: {text}\n\nUse /request {text} to request this movie.",
                reply_to_message_id=message.message_id,
            )
            self.db.add_message(not_found.chat.id, not_found.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        bot_username = context.bot.username or self.config.BOT_USERNAME
        result = f"🎬 Search Results\n\nFound {len(movies)} movie(s).\n\nSelect your movie below."
        sent = await message.reply_text(
            result,
            reply_markup=Keyboards.movie_buttons(movies, bot_username),
            reply_to_message_id=message.message_id,
        )
        self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
