import html

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.i18n import t


def render_search_results(
    query_text: str,
    movies,
    page: int,
    page_size: int,
    bot_username: str,
    heading: str = None,
    code: str = 'en'
):
    """Build one page of search results as (message text, keyboard).

    Used for a normal search and for the 18+ confirmation, and again when a
    page button is pressed, so all three always look the same.

    The titles live only on the buttons: the text just states the query, the
    number of matches and the current page.
    """
    total = len(movies)
    page_size = max(1, page_size)
    total_pages = (total + page_size - 1) // page_size

    if not Keyboards.paginates(total_pages, query_text):
        page, total_pages, page_size = 1, 1, max(total, 1)

    page = min(max(page, 1), total_pages)
    start = (page - 1) * page_size
    page_movies = movies[start:start + page_size]

    heading = heading or t(code, 'search_result')

    lines = [
        f'{t(code, "search_query")} — <code>{html.escape(query_text)}</code>',
        '',
        f'{heading} — {t(code, "search_files", count=total)}',
    ]

    if total_pages > 1:
        lines.append(
            f'{t(code, "search_pages")} — <b>{page}/{total_pages}</b>'
        )

    lines.extend([
        '',
        t(code, 'search_select'),
    ])

    keyboard = Keyboards.search_results_keyboard(
        page_movies,
        bot_username,
        page,
        total_pages,
        query_text
    )

    return '\n'.join(lines), keyboard


class SearchHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def is_adult_query(self, text: str) -> bool:
        lowered = (text or '').lower()
        return any(keyword in lowered for keyword in self.config.ADULT_KEYWORDS)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        if not message or not user or not chat or not message.text:
            return

        text = message.text.strip()
        self.db.add_or_update_user(user.id, user.username or '', user.first_name or '', user.last_name or '')
        code = self.db.get_user_language(user.id)

        if chat.id == self.config.GROUP_ID and chat.type in ('group', 'supergroup'):
            self.db.add_message(chat.id, message.message_id, seconds=self.config.AUTO_DELETE_TIME)

        if text == '🎬 Search Movie':
            if chat.type == 'private':
                sent = await message.reply_text(
                    t(code, 'private_search'),
                    parse_mode=ParseMode.HTML,
                    reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME, code),
                )
            else:
                sent = await message.reply_text(
                    f'{t(code, "brand")}\n\n{t(code, "search_hint")}\n'
                    '🎬 <code>Avengers</code>',
                    parse_mode=ParseMode.HTML,
                )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '🎥 Request Movie':
            sent = await message.reply_text(
                t(code, 'request_hint'),
                parse_mode=ParseMode.HTML,
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '📢 Join Channel':
            sent = await message.reply_text(
                f'{t(code, "brand")}\n\n{t(code, "join_channel")}',
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME, code),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == '👥 Join Group':
            sent = await message.reply_text(
                f'{t(code, "brand")}\n\n{t(code, "join_group")}',
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME, code),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if text == 'ℹ️ Help':
            sent = await message.reply_text(
                self.config.HELP_MSG,
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.main_menu(),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if chat.type == 'private':
            sent = await message.reply_text(
                t(code, 'private_search'),
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.promo_buttons(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME, code),
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        if chat.id != self.config.GROUP_ID:
            return

        if not self.db.is_admin(user.id, self.config.ADMIN_IDS) and self.config.COOLDOWN_TIME > 0:
            if not self.db.check_cooldown(user.id, self.config.COOLDOWN_TIME):
                remain = self.db.cooldown_remaining(user.id, self.config.COOLDOWN_TIME)
                warn = await message.reply_text(
                    f'{t(code, "wait")}\n\n' + t(code, 'wait_line', seconds=remain),
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=message.message_id,
                )
                self.db.add_message(warn.chat.id, warn.message_id, seconds=min(remain + 2, self.config.AUTO_DELETE_TIME))
                return

        if self.is_adult_query(text):
            context.user_data['adult_query'] = text
            context.user_data['adult_chat_id'] = chat.id
            confirm = await message.reply_text(
                f'{t(code, "adult_title")}\n\n{t(code, "adult_line")}',
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.adult_confirmation(code),
                reply_to_message_id=message.message_id,
            )
            self.db.add_message(confirm.chat.id, confirm.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        await self.send_search_results(message, context, text, code)

    async def send_search_results(self, message, context, text: str, code: str = 'en'):
        movies = self.db.search_movies(text, self.config.MAX_MOVIES_PER_SEARCH)
        if not movies:
            safe = html.escape(text)
            sent = await message.reply_text(
                f'{t(code, "brand")}\n'
                '━━━━━━━━━━━━━━━━━━━\n'
                f'{t(code, "no_results")}\n\n'
                f'🔎 {t(code, "search_query")} — <code>{safe}</code>\n\n'
                + t(code, 'request_it', command=f'/request {safe}'),
                parse_mode=ParseMode.HTML,
                reply_to_message_id=message.message_id,
            )
            self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)
            return

        bot_info = await context.bot.get_me()
        username = bot_info.username or self.config.BOT_USERNAME

        result_text, keyboard = render_search_results(
            text,
            movies,
            1,
            self.config.SEARCH_RESULTS_PER_PAGE,
            username,
            code=code
        )

        result = await message.reply_text(
            result_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            reply_to_message_id=message.message_id,
        )
        self.db.add_message(result.chat.id, result.message_id, seconds=self.config.AUTO_DELETE_TIME)
