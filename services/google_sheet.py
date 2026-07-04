import os
import json
import logging

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetService:

    def __init__(self, config):
        self.config = config
        self.spreadsheet = None

        if not config.GOOGLE_SHEET_URL:
            logging.warning("GOOGLE_SHEET_URL not found")
            return

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")

            if creds_json:
                creds_dict = json.loads(creds_json)
                creds = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=scopes
                )
            else:
                creds = Credentials.from_service_account_file(
                    config.GOOGLE_CREDENTIALS_FILE,
                    scopes=scopes
                )

            client = gspread.authorize(creds)

            self.spreadsheet = client.open_by_url(
                config.GOOGLE_SHEET_URL
            )

            logging.info("Google Sheet connected successfully")

        except Exception as exc:
            logging.warning("Google Sheet init error: %s", exc)

    def get_or_create_worksheet(self, title, headers):
        if self.spreadsheet is None:
            return None

        try:
            worksheet = self.spreadsheet.worksheet(title)

        except Exception:
            worksheet = self.spreadsheet.add_worksheet(
                title=title,
                rows=1000,
                cols=max(len(headers), 10)
            )
            worksheet.append_row(headers)

        return worksheet

    def add_request(
        self,
        request_id,
        user_id,
        username,
        first_name,
        movie_name,
        request_time
    ):
        worksheet = self.get_or_create_worksheet(
            "Movie Requests",
            [
                "Request ID",
                "User ID",
                "Username",
                "Name",
                "Movie Name",
                "Request Time"
            ]
        )

        if worksheet is None:
            return

        try:
            worksheet.append_row([
                str(request_id),
                str(user_id),
                username or "",
                first_name or "",
                movie_name or "",
                request_time.strftime("%Y-%m-%d %H:%M:%S")
            ])

        except Exception as exc:
            logging.warning("Movie Request sheet error: %s", exc)

    def add_storage_upload(
        self,
        movie_name,
        movie_id,
        uploaded_by,
        upload_time,
        file_size=""
    ):
        worksheet = self.get_or_create_worksheet(
            "Storage Uploads",
            [
                "Movie Name",
                "Movie ID",
                "Uploaded By",
                "Date & Time",
                "File Size"
            ]
        )

        if worksheet is None:
            return

        try:
            worksheet.append_row([
                movie_name or "",
                str(movie_id),
                uploaded_by or "",
                upload_time or "",
                file_size or ""
            ])

        except Exception as exc:
            logging.warning("Storage Upload sheet error: %s", exc)