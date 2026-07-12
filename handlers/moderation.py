import logging
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationHandlerStop, ContextTypes

from config import Config
from database import Database


class ModerationHandler:
    URL_PATTERN = re.compile(r'(?i)(https?://|www\.|t\.me/|telegram\.me/)')
    USERNAME_PATTERN = re.compile(r'(?<!\w)@[A-Za-z0-9_]{5,}')

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        if not message or not user or not chat:
            return
        if chat.id != self.config.GROUP_ID or chat.type not in ('group', 'supergroup'):
            return
        if self.db.is_admin(user.id, self.config.ADMIN_IDS):
            return

        text = (message.text or message.caption or '').strip()
        if not text:
            return

        violation = bool(self.URL_PATTERN.search(text))

        if not violation:
            for username in self.USERNAME_PATTERN.findall(text):
                try:
                    target = await context.bot.get_chat(username)
                    if target.type in ('group', 'supergroup', 'channel'):
                        violation = True
                        break
                except Exception:
                    continue

        if not violation:
            return

        try:
            await message.delete()
        except Exception:
            pass

        removed = False
        try:
            await context.bot.ban_chat_member(chat.id, user.id)
            await context.bot.unban_chat_member(chat.id, user.id, only_if_banned=True)
            removed = True
        except Exception as exc:
            logging.warning('Could not remove link sender %s: %s', user.id, exc)

        notice = await context.bot.send_message(
            chat_id=chat.id,
            text=(
                '🚫 <b>Link/Channel Promotion Removed</b>\n\n'
                f'User: {user.mention_html()}\n'
                f'Status: {"Removed from the group" if removed else "Message deleted"}'
            ),
            parse_mode=ParseMode.HTML,
        )
        self.db.add_message(notice.chat.id, notice.message_id, seconds=20)
        raise ApplicationHandlerStop
