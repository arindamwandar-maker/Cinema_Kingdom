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

            logging.warning(
                "Google Sheet disabled: GOOGLE_SHEET_URL is empty"
            )

            return

        try:

            credentials = self._load_credentials(
                config
            )

            if credentials is None:
                return

            client = gspread.authorize(
                credentials
            )

            self.spreadsheet = client.open_by_url(
                config.GOOGLE_SHEET_URL
            )

            logging.info(
                "Google Sheet connected successfully: %s",
                self.spreadsheet.title
            )

        except Exception as exc:

            logging.exception(
                "Google Sheet init error: %s",
                exc
            )

    @staticmethod
    def _load_credentials(config):

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        raw_json = (
            config.GOOGLE_CREDENTIALS_JSON
            or os.getenv(
                "GOOGLE_CREDENTIALS_JSON",
                ""
            )
        )

        raw_base64 = (
            config.GOOGLE_CREDENTIALS_BASE64
            or os.getenv(
                "GOOGLE_CREDENTIALS_BASE64",
                ""
            )
        )

        try:

            if raw_base64:

                raw_json = base64.b64decode(
                    raw_base64
                ).decode(
                    "utf-8"
                )

            if raw_json:

                raw_json = raw_json.strip()

                # Railway value-এর শুরুতে/শেষে quote থাকলে remove
                if (
                    raw_json.startswith('"')
                    and raw_json.endswith('"')
                ):

                    raw_json = json.loads(
                        raw_json
                    )

                info = json.loads(
                    raw_json
                )

                if "private_key" in info:

                    info["private_key"] = (
                        info["private_key"]
                        .replace(
                            "\\n",
                            "\n"
                        )
                    )

                return Credentials.from_service_account_info(
                    info,
                    scopes=scopes
                )

            if (
                config.GOOGLE_CREDENTIALS_FILE
                and os.path.exists(
                    config.GOOGLE_CREDENTIALS_FILE
                )
            ):

                return Credentials.from_service_account_file(
                    config.GOOGLE_CREDENTIALS_FILE,
                    scopes=scopes
                )

            logging.warning(
                "Google Sheet disabled: set "
                "GOOGLE_CREDENTIALS_JSON or "
                "GOOGLE_CREDENTIALS_BASE64"
            )

            return None

        except Exception as exc:

            logging.exception(
                "Google credentials could not be loaded: %s",
                exc
            )

            return None

    def get_or_create_worksheet(
        self,
        title,
        headers
    ):

        if self.spreadsheet is None:
            return None

        try:

            worksheet = self.spreadsheet.worksheet(
                title
            )

        except WorksheetNotFound:

            worksheet = self.spreadsheet.add_worksheet(
                title=title,
                rows=1000,
                cols=max(
                    len(headers),
                    10
                )
            )

            worksheet.append_row(
                headers,
                value_input_option="USER_ENTERED"
            )

            return worksheet

        # Existing worksheet-এর headers update করবে

        try:

            current_headers = worksheet.row_values(
                1
            )

            if current_headers != headers:

                worksheet.update(
                    range_name=f"A1:{self._column_letter(len(headers))}1",
                    values=[headers]
                )

        except Exception as exc:

            logging.warning(
                "Worksheet header update failed for %s: %s",
                title,
                exc
            )

        return worksheet

    @staticmethod
    def _column_letter(number: int) -> str:

        result = ""

        while number:

            number, remainder = divmod(
                number - 1,
                26
            )

            result = chr(
                65 + remainder
            ) + result

        return result or "A"

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
            return False

        try:

            worksheet.append_row([
                str(request_id),
                str(user_id),
                username or "",
                first_name or "",
                movie_name or "",
                request_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ], value_input_option="USER_ENTERED")

            logging.info(
                "Movie request saved to Google Sheet: %s",
                request_id
            )

            return True

        except Exception as exc:

            logging.exception(
                "Movie Request sheet error: %s",
                exc
            )

            return False

    def add_storage_upload(
        self,
        movie_name,
        movie_id,
        uploaded_by,
        upload_time,
        file_size=""
    ):

        headers = [
            "Movie Name",
            "Movie ID",
            "Uploaded By",
            "Date & Time",
            "File Size",
            "Status",
            "Deleted By",
            "Deleted Time"
        ]

        worksheet = self.get_or_create_worksheet(
            "Storage Uploads",
            headers
        )

        if worksheet is None:
            return False

        try:

            worksheet.append_row([
                movie_name or "",
                str(movie_id),
                uploaded_by or "",
                upload_time or "",
                file_size or "",
                "Active",
                "",
                ""
            ], value_input_option="USER_ENTERED")

            logging.info(
                "Storage upload saved to Google Sheet: %s",
                movie_id
            )

            return True

        except Exception as exc:

            logging.exception(
                "Storage Upload sheet error: %s",
                exc
            )

            return False

    def mark_movie_deleted(
        self,
        movie_id,
        deleted_by,
        deleted_time
    ):

        headers = [
            "Movie Name",
            "Movie ID",
            "Uploaded By",
            "Date & Time",
            "File Size",
            "Status",
            "Deleted By",
            "Deleted Time"
        ]

        worksheet = self.get_or_create_worksheet(
            "Storage Uploads",
            headers
        )

        if worksheet is None:
            return False

        try:

            movie_ids = worksheet.col_values(
                2
            )

            target_row = None

            for row_number, stored_id in enumerate(
                movie_ids,
                start=1
            ):

                if row_number == 1:
                    continue

                if str(stored_id).strip() == str(
                    movie_id
                ).strip():

                    target_row = row_number
                    break

            if target_row is None:

                logging.warning(
                    "Movie ID not found in Storage Uploads sheet: %s",
                    movie_id
                )

                return False

            worksheet.update(
                range_name=f"F{target_row}:H{target_row}",
                values=[[
                    "Movie Deleted",
                    deleted_by or "",
                    deleted_time or ""
                ]]
            )

            logging.info(
                "Movie marked deleted in Google Sheet: %s",
                movie_id
            )

            return True

        except Exception as exc:

            logging.exception(
                "Google Sheet delete update error: %s",
                exc
            )

            return False

    def test_connection(self):

        if self.spreadsheet is None:

            return (
                False,
                "Google Sheet is not connected. "
                "Check Railway variables and Sheet sharing."
            )

        try:

            worksheet = self.get_or_create_worksheet(
                "System Test",
                [
                    "Status",
                    "Message",
                    "Time"
                ]
            )

            worksheet.append_row([
                "OK",
                "Cinema Kingdom bot connected successfully",
                __import__("datetime")
                .datetime.now()
                .strftime("%Y-%m-%d %H:%M:%S")
            ], value_input_option="USER_ENTERED")

            return (
                True,
                "Google Sheet connection successful."
            )

        except Exception as exc:

            return (
                False,
                f"Google Sheet test failed: {exc}"
            )
