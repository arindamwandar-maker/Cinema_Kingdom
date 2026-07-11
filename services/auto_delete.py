import logging

from telegram.error import BadRequest, Forbidden, TelegramError

from database import Database


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
