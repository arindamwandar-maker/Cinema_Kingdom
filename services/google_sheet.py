import base64
import json
import logging
import os

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound


class GoogleSheetService:
    def __init__(self, config):
        self.config = config
        self.spreadsheet = None
        if not config.GOOGLE_SHEET_URL:
            logging.warning('Google Sheet disabled: GOOGLE_SHEET_URL is empty')
            return
        try:
            creds = self._load_credentials(config)
            if creds is None:
                return
            self.spreadsheet = gspread.authorize(creds).open_by_url(config.GOOGLE_SHEET_URL)
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
                # Accept both raw JSON and a JSON string containing JSON.
                parsed = json.loads(raw_json)
                if isinstance(parsed, str):
                    parsed = json.loads(parsed)
                if 'private_key' in parsed:
                    parsed['private_key'] = parsed['private_key'].replace('\\n', '\n')
                return Credentials.from_service_account_info(parsed, scopes=scopes)
            if config.GOOGLE_CREDENTIALS_FILE and os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
                return Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
            logging.warning('Google Sheet disabled: credentials are not configured')
            return None
        except Exception as exc:
            logging.exception('Google credentials could not be loaded: %s', exc)
            return None

    def get_or_create_worksheet(self, title, headers):
        if self.spreadsheet is None:
            return None
        try:
            worksheet = self.spreadsheet.worksheet(title)
        except WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=max(10, len(headers)))
            worksheet.append_row(headers, value_input_option='USER_ENTERED')
            return worksheet
        current = worksheet.row_values(1)
        if current != headers:
            worksheet.update(range_name=f'A1:{self._column_letter(len(headers))}1', values=[headers])
        return worksheet

    @staticmethod
    def _column_letter(number):
        out = ''
        while number:
            number, remainder = divmod(number - 1, 26)
            out = chr(65 + remainder) + out
        return out or 'A'

    def add_request(self, request_id, user_id, username, first_name, movie_name, request_time):
        ws = self.get_or_create_worksheet('Movie Requests', [
            'Request ID', 'User ID', 'Username', 'Name', 'Movie Name', 'Request Time'
        ])
        if ws is None:
            return False
        try:
            ws.append_row([
                str(request_id), str(user_id), username or '', first_name or '', movie_name or '',
                request_time.strftime('%Y-%m-%d %H:%M:%S'),
            ], value_input_option='USER_ENTERED')
            return True
        except Exception as exc:
            logging.exception('Movie request sheet error: %s', exc)
            return False

    def add_storage_upload(self, movie_name, movie_id, uploaded_by, upload_time, file_size='', file_id=''):
        headers = ['Movie Name', 'Movie ID', 'Uploaded By', 'Date & Time', 'File Size', 'File ID', 'Status', 'Deleted By', 'Deleted Time']
        ws = self.get_or_create_worksheet('Storage Uploads', headers)
        if ws is None:
            return False
        try:
            ws.append_row([
                movie_name or '', str(movie_id), uploaded_by or '', upload_time or '', file_size or '',
                file_id or '', 'Active', '', ''
            ], value_input_option='USER_ENTERED')
            return True
        except Exception as exc:
            logging.exception('Storage upload sheet error: %s', exc)
            return False

    def mark_movie_deleted(self, movie_id, deleted_by, deleted_time):
        headers = ['Movie Name', 'Movie ID', 'Uploaded By', 'Date & Time', 'File Size', 'File ID', 'Status', 'Deleted By', 'Deleted Time']
        ws = self.get_or_create_worksheet('Storage Uploads', headers)
        if ws is None:
            return False
        try:
            for row_num, stored_id in enumerate(ws.col_values(2), start=1):
                if row_num > 1 and str(stored_id).strip() == str(movie_id):
                    ws.update(range_name=f'G{row_num}:I{row_num}', values=[['Movie Deleted', deleted_by or '', deleted_time or '']])
                    return True
            return False
        except Exception as exc:
            logging.exception('Google Sheet delete update error: %s', exc)
            return False

    def mark_movie_active(self, movie_id):
        headers = ['Movie Name', 'Movie ID', 'Uploaded By', 'Date & Time', 'File Size', 'File ID', 'Status', 'Deleted By', 'Deleted Time']
        ws = self.get_or_create_worksheet('Storage Uploads', headers)
        if ws is None:
            return False
        try:
            for row_num, stored_id in enumerate(ws.col_values(2), start=1):
                if row_num > 1 and str(stored_id).strip() == str(movie_id):
                    ws.update(range_name=f'G{row_num}:I{row_num}', values=[['Active', '', '']])
                    return True
            return False
        except Exception:
            return False

    def test_connection(self):
        if self.spreadsheet is None:
            return False, 'Google Sheet is not connected. Check credentials, URL and sharing.'
        try:
            ws = self.get_or_create_worksheet('System Test', ['Status', 'Message'])
            ws.append_row(['OK', 'Cinema Kingdom connected successfully'], value_input_option='USER_ENTERED')
            return True, 'Google Sheet connection successful.'
        except Exception as exc:
            return False, f'Google Sheet test failed: {exc}'
