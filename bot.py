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
        )

        self.promotion = PromotionService(
            self.config
        )

    async def error_handler(
        self,
        update: object,
        context: ContextTypes.DEFAULT_TYPE
    ):
        logging.exception(
            "Bot Error",
            exc_info=context.error
        )

    def run(self):
        setup_logger()

        if not self.config.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN missing in Railway variables"
            )

        app = (
            Application.builder()
            .token(self.config.BOT_TOKEN)
            .build()
        )

        app.add_error_handler(
            self.error_handler
        )

        # =========================
        # USER COMMANDS
        # =========================

        app.add_handler(
            CommandHandler(
                "start",
                self.start_handler.start
            )
        )

        app.add_handler(
            CommandHandler(
                "help",
                self.start_handler.help
            )
        )

        app.add_handler(
            CommandHandler(
                "request",
                self.request_handler.request
            )
        )

        # =========================
        # ADMIN COMMANDS
        # =========================

        app.add_handler(
            CommandHandler(
                "stats",
                self.admin_handler.stats
            )
        )

        app.add_handler(
            CommandHandler(
                "requests",
                self.admin_handler.requests
            )
        )

        app.add_handler(
            CommandHandler(
                "broadcast",
                self.admin_handler.broadcast
            )
        )

        app.add_handler(
            CommandHandler(
                "sendgroup",
                self.admin_handler.send_group
            )
        )

        app.add_handler(
            CommandHandler(
                "sendchannel",
                self.admin_handler.send_channel
            )
        )

        app.add_handler(
            CommandHandler(
                "sendboth",
                self.admin_handler.send_both
            )
        )

        app.add_handler(
            CommandHandler(
                "delete",
                self.admin_handler.delete_movie
            )
        )

        app.add_handler(
            CommandHandler(
                "restore",
                self.admin_handler.restore_movie
            )
        )

        app.add_handler(
            CommandHandler(
                "addadmin",
                self.admin_handler.add_admin
            )
        )

        app.add_handler(
            CommandHandler(
                "removeadmin",
                self.admin_handler.remove_admin
            )
        )

        app.add_handler(
            CommandHandler(
                "admins",
                self.admin_handler.list_admins
            )
        )

        app.add_handler(
            CommandHandler(
                "sheettest",
                self.admin_handler.sheet_test
            )
        )

        # =========================
        # STORAGE COMMANDS
        # =========================

        app.add_handler(
            MessageHandler(
                filters.Chat(
                    self.config.STORAGE_CHANNEL
                )
                & filters.TEXT
                & filters.Regex(
                    r"^/delete(?:@\w+)?\s+\d+\s*$"
                ),
                self.admin_handler.delete_movie
            )
        )

        app.add_handler(
            MessageHandler(
                filters.Chat(
                    self.config.STORAGE_CHANNEL
                )
                & filters.TEXT
                & filters.Regex(
                    r"^/restore(?:@\w+)?\s+\d+\s*$"
                ),
                self.admin_handler.restore_movie
            )
        )

        # =========================
        # STORAGE FILE UPLOAD
        # =========================

        app.add_handler(
            MessageHandler(
                filters.Chat(
                    self.config.STORAGE_CHANNEL
                )
                & (
                    filters.Document.ALL
                    | filters.VIDEO
                    | filters.AUDIO
                    | filters.ANIMATION
                ),
                self.storage_handler.handle_storage_upload
            )
        )

        # =========================
        # GROUP MODERATION
        # =========================

        app.add_handler(
            MessageHandler(
                filters.Chat(
                    self.config.GROUP_ID
                ),
                self.moderation_handler.handle_message
            ),
            group=0
        )

        # =========================
        # SEARCH HANDLER
        # =========================

        app.add_handler(
            MessageHandler(
                filters.TEXT
                & ~filters.COMMAND,
                self.search_handler.handle_message
            ),
            group=1
        )

        # =========================
        # BUTTON CALLBACKS
        # =========================

        app.add_handler(
            CallbackQueryHandler(
                self.callback_handler.handle_callback
            )
        )

        # =========================
        # BACKGROUND JOBS
        # =========================

        # Auto-delete expired messages
        app.job_queue.run_repeating(
            self.auto_delete.cleanup,
            interval=30,
            first=10
        )

        # Google Sheet movie-name sync
        app.job_queue.run_repeating(
            self.sheet_sync.sync_movie_names,
            interval=self.config.SHEET_SYNC_INTERVAL,
            first=20
        )

        # Promotion message every 1 hour
        app.job_queue.run_repeating(
            self.promotion.send_promotion,
            interval=3600,
            first=30
        )

        logging.info(
            "Cinema Kingdom Bot Started | DB=%s",
            self.config.DB_PATH
        )

        logging.info(
            "Promotion interval set to 3600 seconds"
        )

        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


if __name__ == "__main__":
    CinemaKingdomBot().run()