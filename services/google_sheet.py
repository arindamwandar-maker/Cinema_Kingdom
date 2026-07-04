import os
import logging

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetService:
    def __init__(self, config):
        self.config = config
        self.sheet = None
        if not config.GOOGLE_SHEET_URL:
            return
        if not os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
            logging.warning("Google credentials file not found: %s", config.GOOGLE_CREDENTIALS_FILE)
            return
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS_FILE, scopes=scopes)
            client = gspread.authorize(creds)
            self.sheet = client.open_by_url(config.GOOGLE_SHEET_URL).sheet1
        except Exception as exc:
            logging.warning("Google Sheet init error: %s", exc)

    def add_request(self, request_id, user_id, username, first_name, movie_name, request_time):
        if self.sheet is None:
            return
        self.sheet.append_row([
            str(request_id),
            str(user_id),
            username,
            first_name,
            movie_name,
            request_time.strftime("%Y-%m-%d %H:%M:%S"),
        ])
