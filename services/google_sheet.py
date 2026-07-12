import base64
import json
import logging
import os
from typing import Dict, List

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound


class GoogleSheetService:
    LINK_HEADERS = [
        'Event ID',
        'Event Type',
        'Movie ID',
        'Movie Name',
        'User ID',
        'Username',
        'Local Date & Time',
    ]

    STORAGE_HEADERS = [
        'Movie Name',
        'Movie ID',
        'Uploaded By',
        'Date & Time',
        'File Size',
        'File ID',
        'Status',
        'Deleted By',
        'Deleted Time',
        'Last Synced Name',
    ]

    def __init__(self, config):
        self.config = config
        self.spreadsheet = None

        if not config.GOOGLE_SHEET_URL:
            logging.warning('Google Sheet disabled: GOOGLE_SHEET_URL is empty')
            return

        try:
            credentials = self._load_credentials(config)
            if credentials is None:
                return

            client = gspread.authorize(credentials)
            self.spreadsheet = client.open_by_url(config.GOOGLE_SHEET_URL)
            logging.info('Google Sheet connected: %s', self.spreadsheet.title)
        except Exception as exc:
            logging.exception('Google Sheet init error: %s', exc)

    @staticmethod
    def _load_credentials(config):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
        ]

        raw_json = config.GOOGLE_CREDENTIALS_JSON or os.getenv('GOOGLE_CREDENTIALS_JSON', '')
        raw_base64 = config.GOOGLE_CREDENTIALS_BASE64 or os.getenv('GOOGLE_CREDENTIALS_BASE64', '')

        try:
            if raw_base64:
                raw_json = base64.b64decode(raw_base64).decode('utf-8')

            if raw_json:
                raw_json = raw_json.strip()
                parsed = json.loads(raw_json)
                if isinstance(parsed, str):
                    parsed = json.loads(parsed)

                if 'private_key' in parsed:
                    parsed['private_key'] = parsed['private_key'].replace('\\n', '\n')

                return Credentials.from_service_account_info(parsed, scopes=scopes)

            if config.GOOGLE_CREDENTIALS_FILE and os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
                return Credentials.from_service_account_file(
                    config.GOOGLE_CREDENTIALS_FILE,
                    scopes=scopes,
                )

            logging.warning('Google Sheet disabled: credentials are not configured')
            return None
        except Exception as exc:
            logging.exception('Google credentials could not be loaded: %s', exc)
            return None

    def get_or_create_worksheet(self, title: str, headers: List[str]):
        if self.spreadsheet is None:
            return None

        try:
            worksheet = self.spreadsheet.worksheet(title)
        except WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=title,
                rows=1000,
                cols=max(10, len(headers)),
            )
            worksheet.append_row(headers, value_input_option='USER_ENTERED')
            return worksheet

        current_headers = worksheet.row_values(1)
        if current_headers != headers:
            worksheet.update(
                range_name=f'A1:{self._column_letter(len(headers))}1',
                values=[headers],
            )

        return worksheet

    @staticmethod
    def _column_letter(number: int) -> str:
        output = ''
        while number:
            number, remainder = divmod(number - 1, 26)
            output = chr(65 + remainder) + output
        return output or 'A'

    def add_request(self, request_id, user_id, username, first_name, movie_name, request_time):
        worksheet = self.get_or_create_worksheet(
            'Movie Requests',
            ['Request ID', 'User ID', 'Username', 'Name', 'Movie Name', 'Request Time'],
        )
        if worksheet is None:
            return False

        try:
            worksheet.append_row(
                [
                    str(request_id),
                    str(user_id),
                    username or '',
                    first_name or '',
                    movie_name or '',
                    request_time.strftime('%Y-%m-%d %H:%M:%S'),
                ],
                value_input_option='USER_ENTERED',
            )
            return True
        except Exception as exc:
            logging.exception('Movie request sheet error: %s', exc)
            return False

    def add_storage_upload(
        self,
        movie_name,
        movie_id,
        uploaded_by,
        upload_time,
        file_size='',
        file_id='',
    ):
        worksheet = self.get_or_create_worksheet('Storage Uploads', self.STORAGE_HEADERS)
        if worksheet is None:
            return False

        try:
            worksheet.append_row(
                [
                    movie_name or '',
                    str(movie_id),
                    uploaded_by or '',
                    upload_time or '',
                    file_size or '',
                    file_id or '',
                    'Active',
                    '',
                    '',
                    movie_name or '',
                ],
                value_input_option='USER_ENTERED',
            )
            return True
        except Exception as exc:
            logging.exception('Storage upload sheet error: %s', exc)
            return False

    def mark_movie_deleted(self, movie_id, deleted_by, deleted_time):
        worksheet = self.get_or_create_worksheet('Storage Uploads', self.STORAGE_HEADERS)
        if worksheet is None:
            return False

        try:
            for row_number, stored_id in enumerate(worksheet.col_values(2), start=1):
                if row_number > 1 and str(stored_id).strip() == str(movie_id):
                    worksheet.update(
                        range_name=f'G{row_number}:I{row_number}',
                        values=[['Movie Deleted', deleted_by or '', deleted_time or '']],
                    )
                    return True
            return False
        except Exception as exc:
            logging.exception('Google Sheet delete update error: %s', exc)
            return False

    def mark_movie_active(self, movie_id):
        worksheet = self.get_or_create_worksheet('Storage Uploads', self.STORAGE_HEADERS)
        if worksheet is None:
            return False

        try:
            for row_number, stored_id in enumerate(worksheet.col_values(2), start=1):
                if row_number > 1 and str(stored_id).strip() == str(movie_id):
                    current_name = worksheet.cell(row_number, 1).value or ''
                    worksheet.update(
                        range_name=f'G{row_number}:J{row_number}',
                        values=[['Active', '', '', current_name]],
                    )
                    return True
            return False
        except Exception as exc:
            logging.exception('Google Sheet restore update error: %s', exc)
            return False

    def get_storage_name_changes(self) -> List[Dict]:
        """Return active rows whose Movie Name differs from Last Synced Name."""
        worksheet = self.get_or_create_worksheet('Storage Uploads', self.STORAGE_HEADERS)
        if worksheet is None:
            return []

        try:
            values = worksheet.get_all_values()
            changes = []

            for row_number, row in enumerate(values[1:], start=2):
                padded = row + [''] * (len(self.STORAGE_HEADERS) - len(row))
                movie_name = padded[0].strip()
                movie_id_text = padded[1].strip()
                status = padded[6].strip().lower()
                last_synced_name = padded[9].strip()

                if not movie_name or not movie_id_text:
                    continue
                if status not in ('', 'active'):
                    continue
                if movie_name == last_synced_name:
                    continue

                try:
                    movie_id = int(movie_id_text)
                except ValueError:
                    logging.warning('Invalid Movie ID in Storage Uploads row %s: %s', row_number, movie_id_text)
                    continue

                changes.append(
                    {
                        'row_number': row_number,
                        'movie_id': movie_id,
                        'movie_name': movie_name,
                        'last_synced_name': last_synced_name,
                    }
                )

            return changes
        except Exception as exc:
            logging.exception('Could not read storage name changes: %s', exc)
            return []

    def mark_storage_name_synced(self, row_number: int, movie_name: str) -> bool:
        worksheet = self.get_or_create_worksheet('Storage Uploads', self.STORAGE_HEADERS)
        if worksheet is None:
            return False

        try:
            worksheet.update_cell(row_number, 10, movie_name)
            return True
        except Exception as exc:
            logging.exception('Could not mark storage name synced for row %s: %s', row_number, exc)
            return False

    def log_link_event(
        self,
        event_id,
        event_type,
        movie_id,
        movie_name,
        user_id,
        username,
        event_time,
    ):
        worksheet = self.get_or_create_worksheet('Link Clicks', self.LINK_HEADERS)
        if worksheet is None:
            return False

        try:
            worksheet.append_row(
                [
                    str(event_id),
                    event_type or '',
                    str(movie_id),
                    movie_name or '',
                    str(user_id),
                    username or '',
                    event_time or '',
                ],
                value_input_option='USER_ENTERED',
            )
            return True
        except Exception as exc:
            logging.exception('Link Clicks sheet error: %s', exc)
            return False

    def test_connection(self):
        if self.spreadsheet is None:
            return False, 'Google Sheet is not connected. Check credentials, URL and sharing.'

        try:
            worksheet = self.get_or_create_worksheet('System Test', ['Status', 'Message'])
            worksheet.append_row(
                ['OK', 'Cinema Kingdom connected successfully'],
                value_input_option='USER_ENTERED',
            )
            return True, 'Google Sheet connection successful.'
        except Exception as exc:
            return False, f'Google Sheet test failed: {exc}'
