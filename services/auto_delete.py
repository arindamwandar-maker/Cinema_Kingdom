import logging

from telegram import Bot
from telegram.error import TelegramError

from config import Config


class AutoDeleteService:
    def __init__(self, db):
        self.db = db
        self.config = Config()
        self.bot = Bot(token=self.config.BOT_TOKEN)

    async def cleanup(self, context):
        try:
            expired = self.db.get_expired_messages()
            if not expired:
                return
            for chat_id, message_id, movie_id in expired:
                try:
                    await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except TelegramError:
                    pass
                except Exception as exc:
                    logging.warning("Auto delete error: %s", exc)
                finally:
                    self.db.remove_message(chat_id, message_id)
            logging.info("Auto delete completed: %d", len(expired))
        except Exception as exc:
            logging.exception("Auto delete failed: %s", exc)
