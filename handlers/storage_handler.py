from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.storage import StorageService


class StorageHandler:
    def __init__(self, db: Database, config: Config):
        self.storage = StorageService(db, config)

    async def handle_storage_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.storage.handle_upload(update, context)
