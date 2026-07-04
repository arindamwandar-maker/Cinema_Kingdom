import logging

from telegram import Bot
from telegram.error import TelegramError


class ForceJoinService:
    def __init__(self, config):
        self.config = config
        self.bot = Bot(token=config.BOT_TOKEN)

    async def check_force_join(self, user_id: int) -> bool:
        allowed = ("member", "administrator", "creator", "restricted")
        try:
            channel_member = await self.bot.get_chat_member(self.config.CHANNEL_ID, user_id)
            if channel_member.status not in allowed:
                return False

            group_member = await self.bot.get_chat_member(self.config.GROUP_ID, user_id)
            if group_member.status not in allowed:
                return False

            return True
        except TelegramError as exc:
            logging.warning("Force join check failed: %s", exc)
            return False
        except Exception as exc:
            logging.exception("Unknown force join error: %s", exc)
            return False
