import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from handlers.search import render_search_results
from services.force_join import ForceJoinService
from services.google_sheet import GoogleSheetService
from services.shortener import ShortenerService
from services.storage import StorageService
from services.token_manager import TokenManager


class CallbackHandler:

    def __init__(
        self,
        db: Database,
        config: Config,
        bot=None
    ):
        self.db = db
        self.config = config

        self.shortener = ShortenerService(
            api_key=config.SHORTENER_API_KEY,
            base_url=config.SHORTENER_BASE_URL,
            alias=config.SHORTENER_ALIAS,
            response_format=(
                config.SHORTENER_RESPONSE_FORMAT
            )
        )

        self.force_join = ForceJoinService(
            config,
            bot
        )

        self.token_manager = TokenManager(
            db
        )

        self.storage = StorageService(
            db,
            config
        )

        self.sheet = GoogleSheetService(
            config
        )

    async def handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query

        if not query:
            return

        data = query.data or ""
        user = query.from_user

        try:
            await query.answer()
        except Exception:
            pass

        # =========================
        # Duplicate upload actions
        # =========================

        if data.startswith("dup_save_"):

            if not self.db.is_admin(
                user.id,
                self.config.ADMIN_IDS
            ):
                await query.answer(
                    "Only admins can confirm duplicate uploads.",
                    show_alert=True
                )
                return

            token = data.replace(
                "dup_save_",
                "",
                1
            )

            await self.storage.confirm_duplicate(
                token,
                query
            )

            return

        if data.startswith("dup_cancel_"):

            if not self.db.is_admin(
                user.id,
                self.config.ADMIN_IDS
            ):
                await query.answer(
                    "Only admins can cancel duplicate uploads.",
                    show_alert=True
                )
                return

            token = data.replace(
                "dup_cancel_",
                "",
                1
            )

            await self.storage.cancel_duplicate(
                token,
                query
            )

            return

        # =========================
        # 18+ confirmation
        # =========================

        if data == "adult_no":

            context.user_data.pop(
                "adult_query",
                None
            )

            context.user_data.pop(
                "adult_chat_id",
                None
            )

            await query.edit_message_text(
                "🔞 This search is not available "
                "for users under 18."
            )

            return

        if data == "adult_yes":

            search_text = context.user_data.pop(
                "adult_query",
                None
            )

            expected_chat_id = (
                context.user_data.pop(
                    "adult_chat_id",
                    None
                )
            )

            if (
                not search_text
                or not query.message
                or query.message.chat.id
                != expected_chat_id
            ):
                await query.edit_message_text(
                    "❌ This age confirmation has expired."
                )
                return

            await self._send_adult_search_results(
                query,
                context,
                search_text
            )

            return

        # =========================
        # Search result pages
        # =========================

        if data.startswith("sp"):

            await self.change_search_page(
                query,
                context,
                data
            )

            return

        # =========================
        # Force join
        # =========================

        if data != "check_join":

            joined = (
                await self.force_join
                .check_force_join(user.id)
            )

            if not joined:

                reason = ""

                if (
                    self.force_join.last_reason
                    and self.db.is_admin(
                        user.id,
                        self.config.ADMIN_IDS
                    )
                ):
                    reason = (
                        "\n\n<i>"
                        + html.escape(self.force_join.last_reason)
                        + "</i>"
                    )

                await query.edit_message_text(
                    "🔒 <b>Access Denied</b>\n\n"
                    "Join the official channel and "
                    "community group first.\n\n"
                    "Then press <b>I've Joined</b>."
                    + reason,
                    parse_mode=ParseMode.HTML,
                    reply_markup=(
                        Keyboards.force_join_menu(
                            self.config.CHANNEL_USERNAME,
                            self.config.GROUP_USERNAME
                        )
                    )
                )

                return

        # =========================
        # Generate download
        # =========================

        if data.startswith("download_"):

            try:
                movie_id = int(
                    data.split(
                        "_",
                        1
                    )[1]
                )

            except (
                ValueError,
                IndexError
            ):
                await query.edit_message_text(
                    "❌ Invalid movie button."
                )
                return

            await self.handle_download(
                query,
                movie_id,
                context
            )

            return

        # =========================
        # Movie details
        # =========================

        if data.startswith("info_"):

            try:
                movie_id = int(
                    data.split(
                        "_",
                        1
                    )[1]
                )

            except (
                ValueError,
                IndexError
            ):
                await query.edit_message_text(
                    "❌ Invalid movie button."
                )
                return

            await self.handle_movie_info(
                query,
                movie_id
            )

            return

        # =========================
        # Verify membership
        # =========================

        if data == "check_join":

            joined = (
                await self.force_join
                .check_force_join(user.id)
            )

            if joined:

                await query.edit_message_text(
                    "✅ Verification successful.\n\n"
                    "Send /start again to continue."
                )

            else:

                await query.edit_message_text(
                    "❌ You have not joined both "
                    "the channel and group yet.",
                    reply_markup=(
                        Keyboards.force_join_menu(
                            self.config.CHANNEL_USERNAME,
                            self.config.GROUP_USERNAME
                        )
                    )
                )

            return

    async def change_search_page(
        self,
        query,
        context,
        data: str
    ):
        """Show another page of a search inside the same group message."""
        page_text, _, search_text = data[2:].partition("|")

        try:
            page = int(page_text)
        except ValueError:
            logging.warning("Search page button without a page number: %s", data)
            return

        if not search_text or not query.message:
            return

        movies = self.db.search_movies(
            search_text,
            self.config.MAX_MOVIES_PER_SEARCH
        )

        if not movies:

            await query.edit_message_text(
                "❌ <b>This search has no results now.</b>\n\n"
                f"🔎 <b>Search Query</b> — <code>{html.escape(search_text)}</code>",
                parse_mode=ParseMode.HTML
            )

            return

        bot_info = await context.bot.get_me()

        text, keyboard = render_search_results(
            search_text,
            movies,
            page,
            self.config.SEARCH_RESULTS_PER_PAGE,
            bot_info.username or self.config.BOT_USERNAME
        )

        try:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )

        except TelegramError as exc:
            # Telegram rejects pressing the page you are already on, and a
            # stale button on a message the cleanup already deleted.
            logging.info("Search page edit skipped: %s", exc)

    async def _send_adult_search_results(
        self,
        query,
        context,
        text: str
    ):
        movies = self.db.search_movies(
            text,
            self.config.MAX_MOVIES_PER_SEARCH
        )

        if not movies:

            await query.edit_message_text(
                "❌ <b>No movie found</b>\n\n"
                f"🔎 <b>Search Query</b> — <code>{html.escape(text)}</code>",
                parse_mode=ParseMode.HTML
            )

            return

        bot_info = await context.bot.get_me()

        result_text, keyboard = render_search_results(
            text,
            movies,
            1,
            self.config.SEARCH_RESULTS_PER_PAGE,
            bot_info.username or self.config.BOT_USERNAME,
            heading='🔞 <b>18+ Search Result</b>'
        )

        try:
            await query.edit_message_text(
                result_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )

        except TelegramError as exc:
            logging.info("18+ search results edit skipped: %s", exc)

        if query.message:
            self.db.add_message(
                query.message.chat.id,
                query.message.message_id,
                seconds=(
                    self.config.AUTO_DELETE_TIME
                )
            )

    async def handle_movie_info(
        self,
        query,
        movie_id: int
    ):
        movie = self.db.get_movie(
            movie_id
        )

        if not movie:

            await query.edit_message_text(
                "❌ Movie not found or deleted."
            )

            return

        self.db.increment_views(
            movie_id
        )

        updated_movie = (
            self.db.get_movie(movie_id)
            or movie
        )

        text = (
            "🎬 <b>Movie Information</b>\n\n"
            f"<b>Title:</b> "
            f"{html.escape(updated_movie['title'])}\n"
            f"<b>Size:</b> "
            f"{self.format_size(updated_movie.get('file_size'))}\n"
            f"<b>Views:</b> "
            f"{updated_movie.get('views', 0)}\n"
            f"<b>Downloads:</b> "
            f"{updated_movie.get('downloads', 0)}"
        )

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(
                movie_id
            )
        )

    async def handle_download(
        self,
        query,
        movie_id: int,
        context: ContextTypes.DEFAULT_TYPE
    ):
        user = query.from_user

        movie = self.db.get_movie(
            movie_id
        )

        if not movie:

            await query.edit_message_text(
                "❌ Movie not found or deleted."
            )

            return

        # Generate a secure deep-link token.
        token = self.token_manager.generate_token(
            movie_id,
            self.config.LINK_EXPIRE_TIME
        )

        bot_info = await context.bot.get_me()

        bot_username = (
            bot_info.username
            or self.config.BOT_USERNAME
        )

        bot_username = (
            bot_username
            or ""
        ).replace("@", "")

        if not bot_username:

            await query.edit_message_text(
                "❌ BOT_USERNAME is missing."
            )

            return

        deep_link = (
            f"https://t.me/{bot_username}"
            f"?start={token}"
        )

        short_link = await self.shortener.shorten_link(
            deep_link
        )

        logging.info(
            "Final download URL movie=%s url=%s",
            movie_id,
            short_link
        )

        no_ad_page = short_link == deep_link or short_link.startswith(
            (
                "https://t.me/",
                "http://t.me/",
            )
        )

        cause = (
            "SHORTENER_API_KEY is empty."
            if not self.shortener.api_key
            else (
                self.shortener.base_url.split("//")[-1].split("/")[0]
                + " did not return a short link."
            )
        )

        # A direct t.me link hands out the file without the ad page, which is
        # the only thing that pays, so it is refused unless he opts in.
        if no_ad_page and not self.config.ALLOW_DIRECT_LINK:

            self.token_manager.remove_token(
                token
            )

            logging.warning(
                "Download refused for movie %s: %s",
                movie_id,
                cause
            )

            debug = ""

            if self.db.is_admin(
                user.id,
                self.config.ADMIN_IDS
            ):
                debug = (
                    "\n\n<i>"
                    + html.escape(cause)
                    + "\n"
                    + html.escape(self.shortener.describe())
                    + "\nRun /adtest for this check anytime.</i>"
                )

            local_failure = datetime.now(
                ZoneInfo(
                    self.config.LOCAL_TIMEZONE
                )
            ).strftime(
                "%Y-%m-%d %I:%M:%S %p"
            )

            try:
                self.sheet.log_download_status(
                    status="Shortener Failed",
                    movie_name=movie["title"],
                    movie_id=movie_id,
                    user_id=user.id,
                    username=(
                        "@" + user.username
                        if user.username
                        else ""
                    ),
                    event_time=local_failure,
                )

            except Exception as exc:
                logging.warning(
                    "Sheet failure log failed: %s",
                    exc
                )

            await query.edit_message_text(
                "🚫 <b>Download unavailable</b>\n\n"
                "The download service is temporarily down, so this movie "
                "cannot be sent right now.\n\n"
                "🔁 Please try again in a few minutes."
                + debug,
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.movie_button(
                    movie_id
                )
            )

            return

        # The file leaves only through the token inside the shortener link, so
        # nobody can collect it without finishing the ad page first.
        steps = (
            "1️⃣ Press "
            "<b>Click Here To Download Movie</b>.\n"
            "2️⃣ Complete the page that opens.\n"
            "3️⃣ The bot sends the movie file at once.\n"
        )

        status_text = (
            "Direct Link"
            if no_ad_page
            else "Link Generated"
        )

        local_time = datetime.now(
            ZoneInfo(
                self.config.LOCAL_TIMEZONE
            )
        ).strftime(
            "%Y-%m-%d %I:%M:%S %p"
        )

        username_text = (
            "@" + user.username
            if user.username
            else ""
        )

        event_id = self.db.log_link_event(
            event_type=status_text,
            movie_id=movie_id,
            user_id=user.id,
            username=username_text,
            event_time=local_time,
        )

        try:
            self.sheet.log_link_event(
                event_id=event_id,
                event_type=status_text,
                movie_id=movie_id,
                movie_name=movie["title"],
                user_id=user.id,
                username=username_text,
                event_time=local_time,
            )

            self.sheet.log_download_status(
                status=status_text,
                movie_name=movie["title"],
                movie_id=movie_id,
                user_id=user.id,
                username=username_text,
                event_time=local_time,
            )

        except Exception as exc:
            logging.warning(
                "Sheet link log failed: %s",
                exc
            )

        await query.edit_message_text(
            f"🎬 <b>{html.escape(movie['title'])}</b>\n\n"
            f"💾 File Size: "
            f"<b>{self.format_size(movie.get('file_size'))}</b>\n\n"
            "✅ Your download link is ready.\n\n"
            f"{steps}\n"
            "⏳ The link message and movie file "
            "will be removed after 5 minutes.",
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.shortener_button(
                short_link
            ),
            disable_web_page_preview=True
        )

        if query.message:

            self.db.add_message(
                query.message.chat.id,
                query.message.message_id,
                movie_id,
                seconds=(
                    self.config.AUTO_DELETE_TIME
                )
            )

    @staticmethod
    def format_size(size):
        if not size:
            return "Unknown"

        value = float(size)

        for unit in (
            "B",
            "KB",
            "MB",
            "GB",
            "TB"
        ):
            if value < 1024:
                return f"{value:.1f} {unit}"

            value /= 1024

        return f"{value:.1f} PB"