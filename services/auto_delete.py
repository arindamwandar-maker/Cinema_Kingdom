import logging

from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import ExtBot

from database import Database

# API calls that create a message the bot can later delete again.
TRACKED_ENDPOINTS = frozenset({
    'sendMessage',
    'sendPhoto',
    'sendVideo',
    'sendAudio',
    'sendDocument',
    'sendAnimation',
    'sendVoice',
    'sendVideoNote',
    'sendSticker',
    'sendMediaGroup',
    'sendPoll',
    'sendGame',
    'sendInvoice',
    'copyMessage',
})


class AutoDeleteBot(ExtBot):
    """An ExtBot that books every message it sends for auto-deletion.

    Handlers used to call db.add_message() by hand and most of them forgot.
    This is the one place all outgoing messages pass through, so nothing the
    bot posts is left lying around after AUTO_DELETE_TIME.
    """

    def __init__(self, *args, db=None, config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry_db = db
        self._registry_config = config

    async def _post(self, endpoint, data=None, **kwargs):
        result = await super()._post(endpoint, data, **kwargs)

        if endpoint in TRACKED_ENDPOINTS:
            try:
                self.track(result)
            except Exception as exc:
                # Never let bookkeeping break a send.
                logging.warning('Auto-delete tracking failed for %s: %s', endpoint, exc)

        return result

    def track(self, result):
        messages = result if isinstance(result, list) else [result]

        for message in messages:
            if not isinstance(message, dict):
                continue

            message_id = message.get('message_id')
            chat_id = (message.get('chat') or {}).get('id')
            if chat_id is None:
                # copyMessage answers with a flat chat_id instead of a chat.
                chat_id = message.get('chat_id')

            if not message_id or chat_id is None:
                continue
            if self.is_kept(chat_id):
                continue

            self._registry_db.add_message(
                chat_id,
                message_id,
                seconds=self._registry_config.AUTO_DELETE_TIME,
            )

    def is_kept(self, chat_id) -> bool:
        """Chats whose bot messages must survive.

        MyStorage holds the original movie posts; deleting those would destroy
        the whole catalogue. Admin chats keep their lists long enough to press
        a button.
        """
        if chat_id == self._registry_config.STORAGE_CHANNEL:
            return True

        if not self._registry_config.DELETE_ADMIN_MESSAGES:
            return chat_id in self.admin_ids()

        return False

    def admin_ids(self):
        ids = {self._registry_config.SUPER_ADMIN_ID}
        ids.update(self._registry_config.ADMIN_IDS)
        try:
            ids.update(self._registry_db.get_admin_ids())
        except Exception as exc:
            logging.warning('Admin list for auto-delete unavailable: %s', exc)
        return ids


class AutoDeleteService:

    def __init__(self, db: Database):
        self.db = db

    async def cleanup(self, context):
        """
        Database-এ যেসব message-এর expiry time শেষ হয়েছে,
        সেগুলো Telegram থেকে delete করে এবং database tracking remove করে।
        কোনো extra cleanup message পাঠাবে না।
        """

        try:
            expired_messages = self.db.get_expired_messages()

            if not expired_messages:
                return

            deleted_count = 0

            for row in expired_messages:
                chat_id = row[0]
                message_id = row[1]

                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=message_id
                    )

                    deleted_count += 1

                except BadRequest as exc:
                    # Message আগে থেকেই delete হয়ে গেলে বা delete করা সম্ভব না হলে
                    logging.debug(
                        "Message already deleted or unavailable: chat=%s message=%s error=%s",
                        chat_id,
                        message_id,
                        exc
                    )

                except Forbidden as exc:
                    # Bot-এর delete permission না থাকলে
                    logging.warning(
                        "Bot has no delete permission: chat=%s message=%s error=%s",
                        chat_id,
                        message_id,
                        exc
                    )

                except TelegramError as exc:
                    logging.warning(
                        "Telegram auto-delete error: chat=%s message=%s error=%s",
                        chat_id,
                        message_id,
                        exc
                    )

                except Exception as exc:
                    logging.exception(
                        "Unexpected auto-delete error: chat=%s message=%s error=%s",
                        chat_id,
                        message_id,
                        exc
                    )

                finally:
                    # Telegram message delete হোক বা আগে থেকেই deleted থাকুক,
                    # database tracking remove করা হবে।
                    try:
                        self.db.remove_message(
                            chat_id,
                            message_id
                        )
                    except Exception as exc:
                        logging.warning(
                            "Failed to remove message tracking: chat=%s message=%s error=%s",
                            chat_id,
                            message_id,
                            exc
                        )

            logging.info(
                "Auto-delete completed: %s expired message(s) processed, %s deleted.",
                len(expired_messages),
                deleted_count
            )

        except Exception as exc:
            logging.exception(
                "Auto-delete cleanup failed: %s",
                exc
            )
