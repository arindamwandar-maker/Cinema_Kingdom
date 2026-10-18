import html
import logging

from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError

from config import Config
from database import Database
from services.google_sheet import GoogleSheetService


class SheetSyncService:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)

    async def sync_movie_names(self, context):
        """Apply the Movie Name edits made in the Storage Uploads tab.

        Returns one record per changed row so /syncnames can report what
        happened. The background job runner ignores the value.
        """
        if self.sheet.spreadsheet is None:
            return []

        results = []

        for change in self.sheet.get_storage_name_changes():
            row_number = change['row_number']
            movie_id = change['movie_id']
            new_name = change['movie_name']

            result = {
                'row_number': row_number,
                'movie_id': movie_id,
                'old_name': (change.get('last_synced_name') or '').strip(),
                'new_name': new_name,
                'renamed': False,
                'caption_updated': False,
                'error': '',
            }

            movie = self.db.get_movie(movie_id)

            if not movie:
                result['error'] = 'no active movie with this ID'
                results.append(result)
                logging.warning(
                    'Sheet sync skipped: active movie not found for ID %s',
                    movie_id
                )
                continue

            result['old_name'] = movie['title']
            result['renamed'] = movie['title'] != new_name

            if result['renamed'] and not self.db.update_movie_title(movie_id, new_name):
                result['error'] = 'database update failed'
                results.append(result)
                logging.warning(
                    'Sheet sync could not update database for movie ID %s',
                    movie_id
                )
                continue

            result['caption_updated'] = await self.sync_caption(context, movie, new_name)

            if result['renamed'] and not result['caption_updated']:
                await self._notify_caption_failure(context, movie_id, movie['title'], new_name)

            if self.sheet.mark_storage_name_synced(row_number, new_name):
                logging.info(
                    'Movie name synced from Google Sheet: ID=%s Name=%s CaptionUpdated=%s',
                    movie_id,
                    new_name,
                    result['caption_updated']
                )

            results.append(result)

        return results

    async def sync_caption(self, context, movie, new_name) -> bool:
        """Rename the stored file post so MyStorage matches the new title."""
        source_chat_id = movie.get('source_chat_id')
        source_message_id = movie.get('source_message_id')

        if not source_chat_id or not source_message_id:
            return False

        try:
            await context.bot.edit_message_caption(
                chat_id=source_chat_id,
                message_id=source_message_id,
                caption=new_name,
            )
            return True

        except BadRequest as exc:
            # Telegram rejects an edit that changes nothing, which means the
            # caption already holds the new name.
            return 'not modified' in str(exc).lower()

        except TelegramError as exc:
            logging.warning(
                'Sheet sync caption update failed for movie ID %s: %s',
                movie.get('id'),
                exc
            )
            return False

        except Exception as exc:
            logging.exception(
                'Unexpected caption update failure for movie ID %s: %s',
                movie.get('id'),
                exc
            )
            return False

    async def _notify_caption_failure(self, context, movie_id, old_name, new_name):
        try:
            await context.bot.send_message(
                chat_id=self.config.STORAGE_CHANNEL,
                text=(
                    '✏️ <b>Movie Name Updated from Google Sheet</b>\n\n'
                    f'🆔 Movie ID: <code>{movie_id}</code>\n'
                    f'📝 Old Name: {html.escape(old_name)}\n'
                    f'🎬 New Name: <b>{html.escape(new_name)}</b>\n\n'
                    'The database/search name was updated. If the original file caption did not change, '
                    'give the bot <b>Edit Messages</b> permission in MyStorage.'
                ),
                parse_mode=ParseMode.HTML,
            )

        except Exception as exc:
            logging.warning(
                'Sheet sync notice failed for movie ID %s: %s',
                movie_id,
                exc
            )
