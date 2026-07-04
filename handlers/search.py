from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards


class SearchHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def is_admin(self, user_id: int) -> bool:
        return self.db.is_admin(user_id, self.config.ADMIN_IDS)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        if not message or not message.text or not user:
            return

        text = message.text.strip()
        self.db.add_or_update_user(user.id, user.username or "", user.first_name or "", user.last_name or "")

        if text.startswith("/"):
            return
        if text == "🎬 Search Movie":
    await message.reply_text("🎬 Movie name লিখুন / type করুন।\nExample: Avengers")
    return

if text == "🎥 Request Movie":
    await message.reply_text("🎥 Request করতে লিখুন:\n/request Movie Name")
    return

if text == "📢 Join Channel":
    await message.reply_text(f"https://t.me/{self.config.CHANNEL_USERNAME.replace('@','')}")
    return

if text == "👥 Join Group":
    await message.reply_text(f"https://t.me/{self.config.GROUP_USERNAME.replace('@','')}")
    return

if text == "ℹ️ Help":
    await message.reply_text(self.config.HELP_MSG)
    return

        if update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
            if not self.is_admin(user.id):
                if not self.db.check_cooldown(user.id, self.config.COOLDOWN_TIME):
                    remain = self.db.cooldown_remaining(user.id, self.config.COOLDOWN_TIME)
                    bar_len = 10
                    filled = max(0, min(bar_len, int((self.config.COOLDOWN_TIME - remain) / self.config.COOLDOWN_TIME * bar_len)))
                    bar = "🟩" * filled + "⬜" * (bar_len - filled)
                    warn = await message.reply_text(
                        "⏳ <b>Slow Down</b>\n\n"
                        f"Please wait <b>{remain} seconds</b> before searching again.\n"
                        f"{bar}\n\n"
                        "This anti-spam notice will auto-delete.",
                        parse_mode="HTML",
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
