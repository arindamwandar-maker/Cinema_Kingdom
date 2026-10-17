import asyncio
import logging

from telegram import Bot
from telegram.error import NetworkError, TelegramError

ALLOWED_STATUSES = ("member", "administrator", "creator", "restricted")


class ForceJoinService:
    """Checks the required channel and group memberships.

    The bot object normally comes from the Application, so the shared connection
    pool and proxy handling apply here. A webhook worker is a cold process and
    its first outbound call can fail, so network errors are retried before a
    user is told to join.
    """

    def __init__(self, config, bot=None):
        self.config = config
        self.bot = bot
        self.last_reason = ""

    async def _member_status(self, chat_id, user_id, label):
        if self.bot is None:
            self.bot = Bot(token=self.config.BOT_TOKEN)

        for attempt in (1, 2, 3):
            try:
                member = await self.bot.get_chat_member(chat_id, user_id)
                return member.status

            except NetworkError as exc:
                logging.warning(
                    "Membership lookup retry %s in %s %s: %s",
                    attempt,
                    label,
                    chat_id,
                    exc,
                )
                await asyncio.sleep(attempt)

            except TelegramError as exc:
                self.last_reason = f"{label} {chat_id}: {exc}"
                return None

        self.last_reason = f"{label} {chat_id}: Telegram unreachable"
        return None

    async def check_force_join(self, user_id: int) -> bool:
        for chat_id, label in (
            (self.config.CHANNEL_ID, "channel"),
            (self.config.GROUP_ID, "group"),
        ):
            status = await self._member_status(chat_id, user_id, label)

            if status is None:
                return False

            if status not in ALLOWED_STATUSES:
                self.last_reason = f"{label} {chat_id}: you are '{status}'"
                return False

        self.last_reason = ""
        return True
