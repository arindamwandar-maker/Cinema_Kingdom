import logging

from telegram import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeChat,
    ChatPermissions,
)
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
from handlers.welcome import WelcomeHandler
from services.auto_delete import AutoDeleteService
from services.community import CommunityService
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
            .post_init(self.prepare_bot)
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

        self.welcome_handler = WelcomeHandler(
            self.db,
            self.config
        )

        self.community = CommunityService(
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

    ADMIN_COMMANDS = [
        BotCommand("stats", "Bot statistics"),
        BotCommand("requests", "Pending movie requests"),
        BotCommand("rn", "Rename a movie: /rn MovieID New Name"),
        BotCommand("del", "Delete a movie: /del MovieID"),
        BotCommand("rst", "Restore a movie: /rst MovieID"),
        BotCommand("syncnames", "Apply names edited in the Google Sheet"),
        BotCommand("broadcast", "Send a message to all users"),
        BotCommand("sendgroup", "Post in the group"),
        BotCommand("sendchannel", "Post in the channel"),
        BotCommand("sendboth", "Post in the group and the channel"),
        BotCommand("admins", "List bot admins"),
        BotCommand("unban", "Let a banned member back in: /unban UserID"),
        BotCommand("addadmin", "Add an admin: /addadmin UserID"),
        BotCommand("removeadmin", "Remove an admin: /removeadmin UserID"),
        BotCommand("sheettest", "Test the Google Sheet connection"),
        BotCommand("adtest", "Test the ad link shortener"),
    ]

    STORAGE_COMMANDS = [
        BotCommand("rn", "Rename a movie: /rn MovieID New Name"),
        BotCommand("del", "Delete a movie: /del MovieID"),
        BotCommand("rst", "Restore a movie: /rst MovieID"),
        BotCommand("stats", "Bot statistics"),
        BotCommand("syncnames", "Apply names edited in the Google Sheet"),
    ]

    async def prepare_bot(self, application):
        """Startup work every boot path has to run."""
        await self.register_command_menu(application)
        await self.apply_group_privacy(application)

    async def apply_group_privacy(self, application):
        """Lock the group down: text only, no invites, no pinning.

        Telegram then refuses the attachment or the invite itself, so nothing
        leaks before the bot gets a chance to delete it. Needs the bot to be a
        group admin with Manage Group.
        """
        attachments = not self.config.GROUP_BLOCK_ATTACHMENTS

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=attachments,
            can_send_documents=attachments,
            can_send_photos=attachments,
            can_send_videos=attachments,
            can_send_video_notes=attachments,
            can_send_voice_notes=attachments,
            can_send_other_messages=attachments,
            can_send_polls=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_topics=False,
        )

        try:
            await application.bot.set_chat_permissions(
                self.config.GROUP_ID,
                permissions
            )
            logging.info('Group privacy permissions applied')

        except Exception as exc:
            logging.warning(
                'Group permissions not applied - the bot needs to be an admin '
                'of %s with Manage Group: %s',
                self.config.GROUP_ID,
                exc
            )

    async def register_command_menu(self, application):
        """Fill Telegram's / suggestion list.

        Users get the download commands everywhere; the admin keys appear
        wherever the admin is, and the short storage keys also work inside
        MyStorage, where channel posts carry no user.
        """
        scopes = [
            (
                [
                    BotCommand("start", "Open the bot"),
                    BotCommand("help", "How to download a movie"),
                    BotCommand("request", "Request a movie"),
                ],
                None,
                "Bot",
            ),
            (
                self.ADMIN_COMMANDS,
                BotCommandScopeAllChatAdministrators(),
                "Admin",
            ),
            (
                self.ADMIN_COMMANDS,
                BotCommandScopeChat(self.config.SUPER_ADMIN_ID),
                "Super admin private",
            ),
            (
                self.STORAGE_COMMANDS,
                BotCommandScopeChat(self.config.STORAGE_CHANNEL),
                "Storage",
            ),
        ]

        for commands, scope, label in scopes:
            try:
                if scope is None:
                    await application.bot.set_my_commands(commands)
                else:
                    await application.bot.set_my_commands(commands, scope=scope)

            except Exception as exc:
                logging.warning("%s command menu not set: %s", label, exc)

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
                "unban",
                self.admin_handler.unban_user
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

        app.add_handler(
            MessageHandler(
                filters.Chat(
                    self.config.STORAGE_CHANNEL
                )
                & filters.TEXT
                & filters.Regex(
                    r"^/(?:stats|stat)(?:@\w+)?\s*$"
                ),
                self.admin_handler.stats
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
                )
                & filters.StatusUpdate.NEW_CHAT_MEMBERS,
                self.welcome_handler.handle_join
            ),
            group=0
        )

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
