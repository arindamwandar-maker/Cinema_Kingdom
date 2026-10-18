import logging

from telegram import BotCommand, BotCommandScopeChat
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
from services.promotion import PromotionService
from services.sheet_sync import SheetSyncService


class CinemaKingdomCore:
    """Builds the Application and registers every handler on it.

    Shared by web.py (webhook) and bot.py (polling) so the handler table
    exists only once. Timed jobs are not registered here: they run from
    tick.py, because a hosted web process is not alive between requests.
    """

    def __init__(self):
        self.config = Config()

        if not self.config.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN missing - set it in the .env file"
            )

        self.db = Database(
            self.config.DB_PATH
        )

        self.db.seed_admins(
            self.config.ADMIN_IDS,
            self.config.SUPER_ADMIN_ID
        )

        self.application = (
            Application.builder()
            .token(self.config.BOT_TOKEN)
            .post_init(self.register_command_menu)
            .build()
        )

        # Handlers get this bot so services reuse the Application's connection
        # pool instead of opening their own.
        bot = self.application.bot

        self.start_handler = StartHandler(
            self.db,
            self.config,
            bot
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
            self.config,
            bot
        )

        self.storage_handler = StorageHandler(
            self.db,
            self.config
        )

        self.sheet_sync = SheetSyncService(
            self.db,
            self.config
        )

        self.admin_handler = AdminHandler(
            self.db,
            self.config,
            self.sheet_sync
        )

        self.moderation_handler = ModerationHandler(
            self.db,
            self.config
        )

        self.auto_delete = AutoDeleteService(
            self.db
        )

        self.promotion = PromotionService(
            self.config
        )

        self._register_handlers()

    async def register_command_menu(self, application):
        """Fill Telegram's / suggestion list.

        Users get the download commands everywhere; the short storage keys
        only appear inside MyStorage, where they are the ones that work.
        """
        try:
            await application.bot.set_my_commands([
                BotCommand("start", "Open the bot"),
                BotCommand("help", "How to download a movie"),
                BotCommand("request", "Request a movie"),
            ])

        except Exception as exc:
            logging.warning("Bot command menu not set: %s", exc)

        try:
            await application.bot.set_my_commands(
                [
                    BotCommand("rn", "Rename a movie: /rn MovieID New Name"),
                    BotCommand("del", "Delete a movie: /del MovieID"),
                    BotCommand("rst", "Restore a movie: /rst MovieID"),
                    BotCommand("syncnames", "Apply names edited in the Google Sheet"),
                ],
                scope=BotCommandScopeChat(
                    self.config.STORAGE_CHANNEL
                ),
            )

        except Exception as exc:
            logging.warning("Storage command menu not set: %s", exc)

    async def error_handler(
        self,
        update: object,
        context: ContextTypes.DEFAULT_TYPE
    ):
        logging.exception(
            "Bot Error",
            exc_info=context.error
        )

    def _register_handlers(self):
        app = self.application

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
                ("delete", "del"),
                self.admin_handler.delete_movie
            )
        )

        app.add_handler(
            CommandHandler(
                ("restore", "rst"),
                self.admin_handler.restore_movie
            )
        )

        app.add_handler(
            CommandHandler(
                ("rename", "rn"),
                self.admin_handler.rename_movie
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

        app.add_handler(
            CommandHandler(
                "adtest",
                self.admin_handler.ad_test
            )
        )

        app.add_handler(
            CommandHandler(
                "syncnames",
                self.admin_handler.sync_names
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
                    r"^/(?:delete|del)(?:@\w+)?\s+\d+\s*$"
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
                    r"^/(?:restore|rst)(?:@\w+)?\s+\d+\s*$"
                ),
                self.admin_handler.restore_movie
            )
        )

        app.add_handler(
            MessageHandler(
                filters.Chat(
                    self.config.STORAGE_CHANNEL
                )
                & filters.TEXT
                & filters.Regex(
                    r"^/(?:rename|rn)(?:@\w+)?\s+\d+\s+\S.*$"
                ),
                self.admin_handler.rename_movie
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

        logging.info(
            "Handlers registered | DB=%s",
            self.config.DB_PATH
        )
