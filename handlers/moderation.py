import logging
import re

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationHandlerStop, ContextTypes

from config import Config
from database import Database
from services.i18n import t


class ModerationHandler:
    URL_PATTERN = re.compile(r'(?i)(https?://|www\.|t\.me/|telegram\.me/)')
    USERNAME_PATTERN = re.compile(r'(?<!\w)@[A-Za-z0-9_]{5,}')
    ATTACHMENTS = (
        'document',
        'video',
        'audio',
        'voice',
        'video_note',
        'animation',
        'sticker',
        'photo',
    )

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def has_attachment(self, message) -> bool:
        return any(getattr(message, name, None) for name in self.ATTACHMENTS)

    async def delete_quietly(self, message):
        try:
            await message.delete()
        except Exception as exc:
            logging.info('Message could not be deleted: %s', exc)

    async def punish(self, context, chat, user, message, reason_key):
        """Delete an unwanted message, then remove the sender from the group.

        A first violation inside the window is only a kick; once the member
        collects GROUP_BAN_STRIKES violations the ban stays in place.
        """
        await self.delete_quietly(message)

        code = self.db.get_user_language(user.id)
        strikes = self.db.add_offense(user.id, self.config.GROUP_OFFENCE_WINDOW)
        banned = strikes >= self.config.GROUP_BAN_STRIKES

        removed = False
        try:
            await context.bot.ban_chat_member(chat.id, user.id)
            removed = True

            if not banned:
                # Telegram has no kick call: banning and unbanning removes the
                # member but lets them rejoin, so this is the warning step.
                await context.bot.unban_chat_member(chat.id, user.id, only_if_banned=True)

        except Exception as exc:
            logging.warning('Could not remove %s: %s', user.id, exc)

        if banned:
            status = '🔒'
        elif removed:
            status = f'🚪 −{self.config.GROUP_BAN_STRIKES - strikes}'
        else:
            status = '🗑'

        # Emoji only besides the rule text, so the notice reads in any language.
        notice = await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f'{t(code, "rule_title")}\n\n'
                f'{t(code, reason_key)}\n\n'
                f'👤 {user.mention_html()}\n'
                f'⚠️ {strikes}/{self.config.GROUP_BAN_STRIKES}  {status}'
            ),
            parse_mode=ParseMode.HTML,
        )
        self.db.add_message(notice.chat.id, notice.message_id, seconds=20)
        raise ApplicationHandlerStop

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        if not message or not user or not chat:
            return
        if chat.id != self.config.GROUP_ID or chat.type not in ('group', 'supergroup'):
            return

        text = (message.text or message.caption or '').strip()
        admin = self.db.is_admin(user.id, self.config.ADMIN_IDS)

        if not admin and self.config.GROUP_BLOCK_ATTACHMENTS and self.has_attachment(message):
            await self.punish(context, chat, user, message, 'rule_attachment')

        # The one message per interval applies to everyone, admins included.
        # Commands are exempt so an admin can still run /sendgroup in a busy hour.
        interval = self.config.GROUP_MESSAGE_INTERVAL
        if interval > 0 and not text.startswith('/') and (text or self.has_attachment(message)):
            if not self.db.check_group_timer(user.id, interval):
                remain = self.db.group_timer_remaining(user.id, interval)
                await self.delete_quietly(message)

                code = self.db.get_user_language(user.id)
                notice = await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f'{t(code, "timer")}\n\n'
                        + t(
                            code,
                            'timer_line',
                            user=user.mention_html(),
                            seconds=remain,
                        )
                    ),
                    parse_mode=ParseMode.HTML,
                )
                self.db.add_message(
                    notice.chat.id,
                    notice.message_id,
                    seconds=min(remain + 2, self.config.AUTO_DELETE_TIME)
                )
                raise ApplicationHandlerStop

        if not text or admin:
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

        await self.punish(context, chat, user, message, 'rule_link')
