import json
import logging
import os

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetService:
    def __init__(self, config):
        self.config = config
        self.spreadsheet = None

        if not config.GOOGLE_SHEET_URL:
            return

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
            if creds_json:
                creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
            elif os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
                creds = Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
            else:
                logging.warning("Google credentials not found. Set GOOGLE_CREDENTIALS_JSON in Railway or add credentials.json.")
                return

            client = gspread.authorize(creds)
            self.spreadsheet = client.open_by_url(config.GOOGLE_SHEET_URL)

        except Exception as exc:
            logging.warning("Google Sheet init error: %s", exc)
            self.spreadsheet = None

    def _worksheet(self, title, headers):
        if self.spreadsheet is None:
            return None
        try:
            return self.spreadsheet.worksheet(title)
        except Exception:
            ws = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=max(10, len(headers)))
            ws.append_row(headers)
            return ws

    def add_request(self, request_id, user_id, username, first_name, movie_name, request_time):
        ws = self._worksheet("Movie Requests", [
            "Request ID", "User ID", "Username", "Name", "Movie Name", "Request Time"
        ])
        if ws is None:
            return
        try:
            ws.append_row([
                str(request_id),
                str(user_id),
                username,
                first_name,
                movie_name,
                request_time.strftime("%Y-%m-%d %H:%M:%S"),
            ])
        except Exception as exc:
            logging.warning("Movie request sheet error: %s", exc)

    def add_storage_upload(self, movie_name, movie_id, uploaded_by, upload_time, file_size):
        ws = self._worksheet("Storage Uploads", [
            "Movie Name", "Movie ID", "Upload By", "Date & Time", "File Size"
        ])
        if ws is None:
            return
        try:
            ws.append_row([
                movie_name,
                f"#{movie_id}",
                uploaded_by,
                upload_time,
                file_size,
            ])
        except Exception as exc:
            logging.warning("Storage upload sheet error: %s", exc)
