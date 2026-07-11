import logging

from telegram.error import TelegramError

from database import Database


class AutoDeleteService:
    def __init__(self, db: Database):
        self.db = db

    async def cleanup(self, context):
        expired = self.db.get_expired_messages()
        if not expired:
            return

        chats_cleaned = set()
        for chat_id, message_id, _movie_id in expired:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                chats_cleaned.add(chat_id)
            except TelegramError as exc:
                # Message may already be deleted or bot may not have permission.
                logging.debug("Auto-delete skipped %s/%s: %s", chat_id, message_id, exc)
            except Exception as exc:
                logging.warning("Auto-delete failed %s/%s: %s", chat_id, message_id, exc)
            finally:
                self.db.remove_message(chat_id, message_id)

        # One short-lived status per affected chat, not one status per deleted message.
        for chat_id in chats_cleaned:
            try:
                note = await context.bot.send_message(
                    chat_id=chat_id,
                    text="🧹✨ Cleanup complete — expired Cinema Kingdom messages were removed.",
                )
                context.job_queue.run_once(
                    self._delete_status,
                    when=5,
                    data={"chat_id": note.chat.id, "message_id": note.message_id},
                    name=f"cleanup-note-{note.chat.id}-{note.message_id}",
                )
            except Exception:
                pass

        logging.info("Auto delete completed (%d messages)", len(expired))

    @staticmethod
    async def _delete_status(context):
        data = context.job.data
        try:
            await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
        except Exception:
            pass
