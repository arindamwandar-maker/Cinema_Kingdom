import json
import logging
import os
import sqlite3
import threading
import time
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession

from services.google_sheet import GoogleSheetService

DRIVE_FILES = 'https://www.googleapis.com/drive/v3/files'
DRIVE_UPLOAD = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'
BACKUP_NAME = 'cinema-kingdom-bot.db'
KEEP = 5


class DbBackupService:

    def __init__(self, config):
        self.db_path = config.DB_PATH
        self.folder_id = os.getenv('DRIVE_BACKUP_FOLDER_ID', '').strip()
        self.interval = int(os.getenv('DB_BACKUP_INTERVAL', '1800'))
        self.session = None

        if not self.folder_id:
            logging.info('DB backup disabled: DRIVE_BACKUP_FOLDER_ID is empty')
            return

        credentials = GoogleSheetService._load_credentials(config)
        if credentials is None:
            logging.warning('DB backup disabled: Google credentials are not configured')
            return

        self.session = AuthorizedSession(credentials)

    def _list_backups(self):
        query = (
            f"name='{BACKUP_NAME}' and '{self.folder_id}' in parents "
            "and trashed=false"
        )
        url = f'{DRIVE_FILES}?q={quote(query)}&orderBy=createdTime%20desc&pageSize=100'
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json().get('files', [])

    def restore_if_missing(self):
        if not self.session:
            return

        if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
            return

        try:
            backups = self._list_backups()
        except Exception:
            logging.exception('DB restore failed while listing Drive backups')
            return

        for meta in backups:
            response = self.session.get(
                f'{DRIVE_FILES}/{meta["id"]}?alt=media',
                timeout=180,
            )
            if response.status_code != 200:
                logging.warning('DB restore: backup %s returned %s', meta['id'], response.status_code)
                continue
            if not response.content.startswith(b'SQLite format 3'):
                logging.warning('DB restore: backup %s is not a SQLite file', meta['id'])
                continue

            parent = os.path.dirname(os.path.abspath(self.db_path))
            os.makedirs(parent, exist_ok=True)
            with open(self.db_path, 'wb') as handle:
                handle.write(response.content)

            logging.info(
                'DB restored from Drive backup %s (%s bytes)',
                meta['id'],
                len(response.content),
            )
            return

        logging.error('DB restore: no usable backup found in the Drive folder')

    def _upload(self, path):
        metadata = {'name': BACKUP_NAME, 'parents': [self.folder_id]}
        with open(path, 'rb') as handle:
            files = {
                'metadata': (
                    'metadata.json',
                    json.dumps(metadata),
                    'application/json; charset=UTF-8',
                ),
                'file': (BACKUP_NAME, handle, 'application/octet-stream'),
            }
            response = self.session.post(DRIVE_UPLOAD, files=files, timeout=300)
        response.raise_for_status()
        return response.json().get('id')

    def _prune(self):
        try:
            for stale in self._list_backups()[KEEP:]:
                response = self.session.delete(
                    f'{DRIVE_FILES}/{stale["id"]}',
                    timeout=30,
                )
                if response.status_code not in (200, 204):
                    logging.warning('DB prune: could not delete %s', stale['id'])
        except Exception:
            logging.exception('DB prune failed')

    def backup(self):
        if not self.session:
            return

        if not os.path.exists(self.db_path):
            return

        temp_path = f'{self.db_path}.backup-tmp'
        source = None
        target = None
        try:
            source = sqlite3.connect(self.db_path)
            target = sqlite3.connect(temp_path)
            with target:
                source.backup(target)
            target.close()
            target = None
            source.close()
            source = None

            file_id = self._upload(temp_path)
            self._prune()
            logging.info('DB backed up to Drive: %s', file_id)
        except Exception:
            logging.exception('DB backup to Drive failed')
        finally:
            for connection in (target, source):
                if connection is not None:
                    connection.close()
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def start(self):
        if not self.session:
            return None

        def loop():
            while True:
                time.sleep(self.interval)
                self.backup()

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        logging.info('DB backup thread started: every %s seconds', self.interval)
        return thread
