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
from handlers.country import CountryHandler
from handlers.language import LanguageHandler
from services.community import render_request_reminder
from services.force_join import ForceJoinService
from services.google_sheet import GoogleSheetService
from services.i18n import t
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

        self.language = LanguageHandler(
            db,
            config
        )

        self.country = CountryHandler(
            db,
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
        code = self.db.get_user_language(user.id) if user else 'en'

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
                t(code, 'adult_blocked'),
                parse_mode=ParseMode.HTML,
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
                    t(code, 'expired_confirm'),
                    parse_mode=ParseMode.HTML,
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

        if data.startswith("lang_"):

            await self.language.save(
                query,
                context,
                data
            )

            return

        if data.startswith("country_"):

            await self.country.save(
                query,
                context,
                data
            )

            return

        # =========================
        # Solve a movie request
        # =========================

        if data.startswith("solved_"):

            await self.solve_request(
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
                    f'{t(code, "access_title")}\n\n{t(code, "access_line")}'
                    + reason,
                    parse_mode=ParseMode.HTML,
                    reply_markup=(
                        Keyboards.force_join_menu(
                            self.config.CHANNEL_USERNAME,
                            self.config.GROUP_USERNAME,
                            code
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
                    t(code, 'invalid_link'),
                    parse_mode=ParseMode.HTML,
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
                    t(code, 'invalid_link'),
                    parse_mode=ParseMode.HTML,
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
                    t(code, 'join_ok'),
                    parse_mode=ParseMode.HTML,
                )

            else:

                await query.edit_message_text(
                    t(code, 'join_pending'),
                    parse_mode=ParseMode.HTML,
                    reply_markup=(
                        Keyboards.force_join_menu(
                            self.config.CHANNEL_USERNAME,
                            self.config.GROUP_USERNAME,
                            code
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

        user = query.from_user
        code = self.db.get_user_language(user.id) if user else 'en'

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
                f'{t(code, "brand")}\n'
                '━━━━━━━━━━━━━━━━━━━\n'
                f'{t(code, "no_results")}\n\n'
                f'{t(code, "search_query")} — <code>{html.escape(search_text)}</code>',
                parse_mode=ParseMode.HTML
            )

            return

        bot_info = await context.bot.get_me()

        text, keyboard = render_search_results(
            search_text,
            movies,
            page,
            self.config.SEARCH_RESULTS_PER_PAGE,
            bot_info.username or self.config.BOT_USERNAME,
            code=code
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

    async def solve_request(
        self,
        query,
        context,
        data: str
    ):
        """Mark a pending movie request as solved from the admin reminder."""
        user = query.from_user

        if not user or not self.db.is_admin(
            user.id,
            self.config.ADMIN_IDS
        ):
            await query.answer(
                "Only bot admins can solve requests.",
                show_alert=True
            )

            return

        try:
            request_id = int(data.split("_", 1)[1])
        except (ValueError, IndexError):
            await query.answer(
                "This button is out of date.",
                show_alert=True
            )

            return

        request = self.db.get_request(request_id)

        if not request:
            await query.answer(
                "This request is not in the bot.",
                show_alert=True
            )

            return

        if request["status"] != "pending":
            await query.answer(
                "This request is already solved.",
                show_alert=True
            )

            return

        solved_time = datetime.now(
            ZoneInfo(self.config.LOCAL_TIMEZONE)
        ).strftime("%Y-%m-%d %H:%M:%S")

        self.db.complete_request(
            request_id,
            user.id
        )

        sheet_ok = self.sheet.mark_request_solved(
            request_id,
            f"@{user.username}" if user.username else str(user.id),
            solved_time
        )

        remaining = self.db.get_pending_requests()

        if query.message:
            if remaining:
                text, keyboard = render_request_reminder(remaining)
            else:
                text = (
                    "✅ <b>All movie requests are solved</b>\n\n"
                    "Nobody is waiting for a movie right now."
                )
                keyboard = None

            try:
                await query.edit_message_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )

            except TelegramError as exc:
                logging.info(
                    "Request reminder edit skipped: %s",
                    exc
                )

        await query.answer(
            "Solved ✅"
            if sheet_ok
            else "Solved in the bot, but the Google Sheet row was not found."
        )

        requester_id = request.get("user_id")

        if requester_id:
            try:
                await context.bot.send_message(
                    chat_id=requester_id,
                    text=(
                        "✅ <b>Your request is solved</b>\n\n"
                        f"🎥 <b>{html.escape(request['movie_title'])}</b>\n\n"
                        "Search it in the group: "
                        f"<code>{html.escape(request['movie_title'])}</code>"
                    ),
                    parse_mode=ParseMode.HTML
                )

            except Exception as exc:
                # A user who never opened the bot cannot be messaged.
                logging.info(
                    "Could not notify requester %s: %s",
                    requester_id,
                    exc
                )

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

        user = query.from_user
        code = self.db.get_user_language(user.id) if user else 'en'

        if not movies:

            await query.edit_message_text(
                f'{t(code, "brand")}\n'
                '━━━━━━━━━━━━━━━━━━━\n'
                f'{t(code, "no_results")}\n\n'
                f'{t(code, "search_query")} — <code>{html.escape(text)}</code>',
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
            heading=f'🔞 {t(code, "search_result")}',
            code=code
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

        user = query.from_user
        code = self.db.get_user_language(user.id) if user else 'en'

        if not movie:

            await query.edit_message_text(
                t(code, 'not_found'),
                parse_mode=ParseMode.HTML,
            )

            return

        self.db.increment_views(
            movie_id
        )

        updated_movie = (
            self.db.get_movie(movie_id)
            or movie
        )

        lines = [
            t(code, 'brand'),
            '━━━━━━━━━━━━━━━━━━━',
            f"🎬 <b>{html.escape(updated_movie['title'])}</b>",
            f"💾 <b>{self.format_size(updated_movie.get('file_size'))}</b>",
            f"👁 <b>{updated_movie.get('views', 0)}</b>"
            f" · ⬇️ <b>{updated_movie.get('downloads', 0)}</b>",
        ]

        uploader = (updated_movie.get('uploaded_by_name') or '').strip()

        if uploader:
            lines.append(
                f'{t(code, "uploader")}: <b>{html.escape(uploader)}</b>'
            )

        text = '\n'.join(lines)

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(
                movie_id,
                code
            )
        )

    async def handle_download(
        self,
        query,
        movie_id: int,
        context: ContextTypes.DEFAULT_TYPE
    ):
        user = query.from_user
        code = self.db.get_user_language(user.id) if user else 'en'

        movie = self.db.get_movie(
            movie_id
        )

        if not movie:

            await query.edit_message_text(
                t(code, 'not_found'),
                parse_mode=ParseMode.HTML,
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
                t(code, 'dl_unavailable') + debug,
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.movie_button(
                    movie_id,
                    code
                )
            )

            return

        # The file leaves only through the token inside the shortener link, so
        # nobody can collect it without finishing the ad page first.
        steps = t(
            code,
            'steps',
            button=t(code, 'download_button')
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
            f'{t(code, "brand")}\n'
            '━━━━━━━━━━━━━━━━━━━\n'
            f"🎬 <b>{html.escape(movie['title'])}</b>\n\n"
            f"💾 {self.format_size(movie.get('file_size'))}\n\n"
            f"{t(code, 'link_ready')}\n\n"
            f"{steps}\n\n"
            f"{t(code, 'validity')}",
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.shortener_button(
                short_link,
                code
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