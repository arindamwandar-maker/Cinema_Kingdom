import json
import logging
import os

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetService:
    def __init__(self, config):
        self.config = config
        self.book = None
        if not config.GOOGLE_SHEET_URL:
            logging.warning("Google Sheet disabled: GOOGLE_SHEET_URL missing")
            return
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds_json = getattr(config, "GOOGLE_CREDENTIALS_JSON", "") or os.getenv("GOOGLE_CREDENTIALS_JSON", "")
            if creds_json:
                creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
            elif os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
                creds = Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
            else:
                logging.warning("Google credentials missing: set GOOGLE_CREDENTIALS_JSON in Railway")
                return
            client = gspread.authorize(creds)
            self.book = client.open_by_url(config.GOOGLE_SHEET_URL)
        except Exception as exc:
            logging.warning("Google Sheet init error: %s", exc)
            self.book = None

    def _worksheet(self, title: str, headers: list):
        if self.book is None:
            return None
        try:
            ws = self.book.worksheet(title)
        except Exception:
            ws = self.book.add_worksheet(title=title, rows=1000, cols=max(10, len(headers)))
            ws.append_row(headers)
        return ws

    def add_request(self, request_id, user_id, username, first_name, movie_name, request_time):
        ws = self._worksheet("Movie Requests", ["Request ID", "User ID", "Username", "Name", "Movie", "Time"])
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
            logging.warning("Movie request sheet update failed: %s", exc)

    def add_storage_upload(self, movie_name, movie_id, uploaded_by, upload_time, file_size=""):
        ws = self._worksheet("Storage Uploads", ["Movie Name", "Movie ID", "Upload By", "Date & Time", "File Size"])
        if ws is None:
            return
        try:
            ws.append_row([movie_name, str(movie_id), uploaded_by, upload_time, file_size])
        except Exception as exc:
            logging.warning("Storage upload sheet update failed: %s", exc)
