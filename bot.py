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
from handlers.request import RequestHandler
from handlers.search import SearchHandler
from handlers.start import StartHandler
from handlers.storage_handler import StorageHandler
from services.auto_delete import AutoDeleteService
from services.logger import setup_logger


class CinemaKingdomBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()

        self.start_handler = StartHandler(self.db, self.config)
        self.search_handler = SearchHandler(self.db, self.config)
        self.request_handler = RequestHandler(self.db, self.config)
        self.callback_handler = CallbackHandler(self.db, self.config)
        self.storage_handler = StorageHandler(self.db, self.config)
        self.admin_handler = AdminHandler(self.db, self.config)
        self.auto_delete = AutoDeleteService(self.db)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logging.exception("Bot Error", exc_info=context.error)

    def run(self):
        setup_logger()
        if not self.config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN missing in .env / Railway variables")

        app = Application.builder().token(self.config.BOT_TOKEN).build()
        app.add_error_handler(self.error_handler)

        app.add_handler(CommandHandler("start", self.start_handler.start))
        app.add_handler(CommandHandler("help", self.start_handler.help))
        app.add_handler(CommandHandler("request", self.request_handler.request))
        app.add_handler(CommandHandler("stats", self.admin_handler.stats))
        app.add_handler(CommandHandler("requests", self.admin_handler.requests))
        app.add_handler(CommandHandler("broadcast", self.admin_handler.broadcast))

        app.add_handler(
            MessageHandler(
                (filters.Document.ALL | filters.VIDEO | filters.AUDIO | filters.ANIMATION),
                self.storage_handler.handle_storage_upload,
            )
        )

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_handler.handle_message))
        app.add_handler(CallbackQueryHandler(self.callback_handler.handle_callback))

        app.job_queue.run_repeating(self.auto_delete.cleanup, interval=60, first=10)

        logging.info("Cinema Kingdom Bot Started")
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    CinemaKingdomBot().run()
