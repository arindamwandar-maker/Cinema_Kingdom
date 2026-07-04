from datetime import datetime

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

        if message is None or not message.text:
            return

        user = update.effective_user
        text = message.text.strip()

        self.db.add_or_update_user(
            user.id,
            user.username or "",
            user.first_name or "",
            user.last_name or ""
        )

        if text == "🎬 Search Movie":
            await message.reply_text(
                "🎬 Movie name লিখুন / type করুন।\n\nExample: Avengers"
            )
            return

        if text == "🎥 Request Movie":
            await message.reply_text(
                "🎥 Request করতে লিখুন:\n\n/request Movie Name"
            )
            return

        if text == "📢 Join Channel":
            await message.reply_text(
                f"https://t.me/{self.config.CHANNEL_USERNAME.replace('@', '')}"
            )
            return

        if text == "👥 Join Group":
            await message.reply_text(
                f"https://t.me/{self.config.GROUP_USERNAME.replace('@', '')}"
            )
            return

        if text == "ℹ️ Help":
            await message.reply_text(
                self.config.HELP_MSG,
                parse_mode="HTML"
            )
            return

        if text.startswith("/"):
            return

        if update.effective_chat.type in ["group", "supergroup"]:

            if user.id not in self.config.ADMIN_IDS:

                if not self.db.check_cooldown(user.id):

                    row = self.db.conn.execute(
                        "SELECT last_message FROM cooldowns WHERE user_id=?",
                        (user.id,)
                    ).fetchone()

                    remain = 60

                    if row:
                        last = datetime.fromisoformat(row["last_message"])
                        remain = 60 - (datetime.now() - last).seconds

                    if remain < 1:
                        remain = 1

                    warn = await message.reply_text(
                        "⏳ Please wait before searching again.\n\n"
                        f"Remaining time: {remain} seconds",
                        reply_to_message_id=message.message_id
                    )

                    self.db.add_message(
                        warn.chat.id,
                        warn.message_id
                    )

                    return

        movies = self.db.search_movies(
            text,
            self.config.MAX_MOVIES_PER_SEARCH
        )

        if not movies:

            not_found = await message.reply_text(
                "❌ Movie not found.\n\n"
                "Use /request Movie Name to request this movie.",
                reply_to_message_id=message.message_id
            )

            self.db.add_message(
                not_found.chat.id,
                not_found.message_id
            )

            return

        result = (
            "🎬 Search Results\n\n"
            f"Found {len(movies)} movie(s).\n\n"
            "Select your movie below."
        )

        sent = await message.reply_text(
            result,
            reply_markup=Keyboards.movie_buttons(movies),
            reply_to_message_id=message.message_id
        )

        self.db.add_message(
            sent.chat.id,
            sent.message_id
        )