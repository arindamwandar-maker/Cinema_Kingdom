import logging

from telegram.error import TelegramError

from config import Config
from database import Database
from services.google_sheet import GoogleSheetService


class SheetSyncService:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)

    async def sync_movie_names(self, context):
        if self.sheet.spreadsheet is None:
            return

        changes = self.sheet.get_storage_name_changes()
        if not changes:
            return

        for change in changes:
            movie_id = change['movie_id']
            new_name = change['movie_name']
            row_number = change['row_number']

            movie = self.db.get_movie(movie_id)
            if not movie:
                logging.warning('Sheet sync skipped: active movie not found for ID %s', movie_id)
                continue

            database_updated = self.db.update_movie_title(movie_id, new_name)
            if not database_updated:
                logging.warning('Sheet sync could not update database for movie ID %s', movie_id)
                continue

            source_chat_id = movie.get('source_chat_id')
            source_message_id = movie.get('source_message_id')

            if source_chat_id and source_message_id:
                try:
                    await context.bot.edit_message_caption(
                        chat_id=source_chat_id,
                        message_id=source_message_id,
                        caption=new_name,
                    )
                except TelegramError as exc:
                    logging.warning(
                        'Sheet sync caption update failed for movie ID %s: %s',
                        movie_id,
                        exc,
                    )
                    # Leave Last Synced Name unchanged so the bot retries later.
                    continue
                except Exception as exc:
                    logging.exception(
                        'Unexpected caption update failure for movie ID %s: %s',
                        movie_id,
                        exc,
                    )
                    continue

            if self.sheet.mark_storage_name_synced(row_number, new_name):
                logging.info('Movie name synced from Google Sheet: ID=%s Name=%s', movie_id, new_name)
