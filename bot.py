import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import Config
from database import Database
from handlers.admin import AdminHandler
from handlers.callback import CallbackHandler
from handlers.moderation import ModerationHandler
from handlers.request import RequestHandler
from handlers.search import SearchHandler
from handlers.start import StartHandler
from handlers.storage_handler import StorageHandler
from services.auto_delete import AutoDeleteService
from services.logger import setup_logger
from services.promotion import PromotionService
from services.sheet_sync import SheetSyncService


class CinemaKingdomBot:

    def __init__(self):
        self.config = Config()

        self.db = Database(
            self.config.DB_PATH
        )

        self.db.seed_admins(
            self.config.ADMIN_IDS,
            self.config.SUPER_ADMIN_ID
        )

        self.start_handler = StartHandler(
            self.db,
            self.config
        )

        self.search_handler = SearchHandler(
            self.db,
            self.config
        )

        self.request_handler = RequestHandler(
            self.db,
            self.config
        )

        self.callback_handler = CallbackHandler(
            self.db,
            self.config
        )

        self.storage_handler = StorageHandler(
            self.db,
            self.config
        )

        self.admin_handler = AdminHandler(
            self.db,
            self.config
        )

        self.moderation_handler = ModerationHandler(
            self.db,
            self.config
        )

        self.auto_delete = AutoDeleteService(
            self.db
        )

        self.sheet_sync = SheetSyncService(
            self.db,
            self.config
       