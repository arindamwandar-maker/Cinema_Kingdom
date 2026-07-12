import html
import logging

from telegram.constants import ParseMode
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
            old_name = change.get('last_synced_name') or ''
            row_number = change['row_number']

            movie = self.db.get_movie(movie_id)
            if not movie:
                logging.warning('Sheet sync skipped: active movie not found for ID %s', movie_id)
                continue

            if not self.db.update_movie_title(movie_id, new_name):
                logging.warning('Sheet sync could not update database for movie ID %s', movie_id)
                continue

            caption_updated = False
            source_chat_id = movie.get('source_chat_id')
            source_message_id = movie.get('source_message_id')

            if source_chat_id and source_message_id:
                try:
                    await context.bot.edit_message_caption(
                        chat_id=source_chat_id,
                        message_id=source_message_id,
                        caption=new_name,
                    )
                    caption_updated = True
                except TelegramError as exc:
                    logging.warning('Sheet sync caption update failed for movie ID %s: %s', movie_id, exc)
                except Exception as exc:
                    logging.exception('Unexpected caption update failure for movie ID %s: %s', movie_id, exc)

            if not caption_updated:
                try:
                    await context.bot.send_message(
                        chat_id=self.config.STORAGE_CHANNEL,
                        text=(
                            '✏️ <b>Movie Name Updated from Google Sheet</b>\n\n'
                            f'🆔 Movie ID: <code>{movie_id}</code>\n'
                            f'📝 Old Name: {html.escape(old_name or movie["title"])}\n'
                            f'🎬 New Name: <b>{html.escape(new_name)}</b>\n\n'
                            'The database/search name was updated. If the original file caption did not change, give the bot <b>Edit Messages</b> permission in MyStorage.'
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass

            if self.sheet.mark_storage_name_synced(row_number, new_name):
                logging.info('Movie name synced from Google Sheet: ID=%s Name=%s CaptionUpdated=%s', movie_id, new_name, caption_updated)
