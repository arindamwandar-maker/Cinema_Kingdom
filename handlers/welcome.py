import html
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database


class WelcomeHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def welcome_text(self, user) -> str:
        try:
            greeting = user.mention_html()
        except Exception:
            greeting = html.escape(user.first_name or 'Friend')

        text = self.config.GROUP_WELCOME_MSG.format(
            first_name=greeting,
            group_name=html.escape(self.config.GROUP_NAME),
        )

        if self.config.SUPER_ADMIN_USERNAME:
            text += '\n\n' + self.config.GROUP_WELCOME_ADMIN_LINE.format(
                admin_username=html.escape(self.config.SUPER_ADMIN_USERNAME)
            )

        return text

    async def handle_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        chat = update.effective_chat
        if not message or not chat or chat.id != self.config.GROUP_ID:
            return

        for user in (message.new_chat_members or []):
            if not user or user.id == context.bot.id:
                continue

            self.db.add_or_update_user(
                user.id,
                user.username or '',
                user.first_name or '',
                user.last_name or ''
            )

            try:
                await message.reply_text(
                    self.welcome_text(user),
                    parse_mode=ParseMode.HTML,
                )
            except Exception as exc:
                logging.info('Welcome message not sent to %s: %s', user.id, exc)
