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
            logging.warning("Google Sheet disabled: GOOGLE_SHEET_URL is empty")
            return
        try:
            creds = self._load_credentials(config)
            if creds is None:
                return
            client = gspread.authorize(creds)
            self.spreadsheet = client.open_by_url(config.GOOGLE_SHEET_URL)
            logging.info("Google Sheet connected successfully: %s", self.spreadsheet.title)
        except Exception as exc:
            logging.exception("Google Sheet init error: %s", exc)

    @staticmethod
    def _load_credentials(config):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        raw_json = config.GOOGLE_CREDENTIALS_JSON or os.getenv("GOOGLE_CREDENTIALS_JSON", "")
        raw_base64 = config.GOOGLE_CREDENTIALS_BASE64 or os.getenv("GOOGLE_CREDENTIALS_BASE64", "")
        try:
            if raw_base64:
                raw_json = base64.b64decode(raw_base64).decode("utf-8")
            if raw_json:
                info = json.loads(raw_json)
                if "private_key" in info:
                    info["private_key"] = info["private_key"].replace("\\n", "\n")
                return Credentials.from_service_account_info(info, scopes=scopes)
            if config.GOOGLE_CREDENTIALS_FILE and os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
                return Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
            logging.warning(
                "Google Sheet disabled: set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_BASE64, "
                "or provide credentials.json"
            )
            return None
        except Exception as exc:
            logging.exception("Google credentials could not be loaded: %s", exc)
            return None

    def get_or_create_worksheet(self, title, headers):
        if self.spreadsheet is None:
            return None
        try:
            worksheet = self.spreadsheet.worksheet(title)
        except WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=max(len(headers), 10))
            worksheet.append_row(headers, value_input_option="USER_ENTERED")
        return worksheet

    def add_request(self, request_id, user_id, username, first_name, movie_name, request_time):
        worksheet = self.get_or_create_worksheet(
            "Movie Requests",
            ["Request ID", "User ID", "Username", "Name", "Movie Name", "Request Time"],
        )
        if worksheet is None:
            return False
        try:
            worksheet.append_row([
                str(request_id), str(user_id), username or "", first_name or "", movie_name or "",
                request_time.strftime("%Y-%m-%d %H:%M:%S"),
            ], value_input_option="USER_ENTERED")
            logging.info("Movie request saved to Google Sheet: %s", request_id)
            return True
        except Exception as exc:
            logging.exception("Movie Request sheet error: %s", exc)
            return False

    def add_storage_upload(self, movie_name, movie_id, uploaded_by, upload_time, file_size=""):
        worksheet = self.get_or_create_worksheet(
            "Storage Uploads",
            ["Movie Name", "Movie ID", "Uploaded By", "Date & Time", "File Size"],
        )
        if worksheet is None:
            return False
        try:
            worksheet.append_row([
                movie_name or "", str(movie_id), uploaded_by or "", upload_time or "", file_size or "",
            ], value_input_option="USER_ENTERED")
            logging.info("Storage upload saved to Google Sheet: %s", movie_id)
            return True
        except Exception as exc:
            logging.exception("Storage Upload sheet error: %s", exc)
            return False

    def test_connection(self):
        if self.spreadsheet is None:
            return False, "Google Sheet is not connected. Check Railway variables and Sheet sharing."
        try:
            worksheet = self.get_or_create_worksheet("System Test", ["Status", "Message"])
            worksheet.append_row(["OK", "Cinema Kingdom bot connected successfully"], value_input_option="USER_ENTERED")
            return True, "Google Sheet connection successful."
        except Exception as exc:
            return False, f"Google Sheet test failed: {exc}"
