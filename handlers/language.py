"""The /language menu.

A user picks once and every private reply - search results, request
confirmation, notices, the delivered file - comes back in that language.
Group notices use the language of the member they are aimed at.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.i18n import (
    CATALOG,
    language_name,
    language_pages,
    language_rows,
    t,
)


class LanguageHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def keyboard(self, page: int = 0) -> InlineKeyboardMarkup:
        rows = language_rows(page)

        if page == 0:
            if language_pages() > 1:
                rows.append([
                    InlineKeyboardButton(
                        t('en', 'language_more'), callback_data='lang_page_1'
                    )
                ])
        else:
            nav = []
            if page > 1:
                nav.append(InlineKeyboardButton('⬅️', callback_data=f'lang_page_{page - 1}'))
            nav.append(InlineKeyboardButton('🔝', callback_data='lang_page_0'))
            if page + 1 < language_pages():
                nav.append(InlineKeyboardButton('➡️', callback_data=f'lang_page_{page + 1}'))
            rows.append(nav)

        return InlineKeyboardMarkup(rows)

    def title(self, code: str) -> str:
        written = ', '.join(language_name(available) for available in sorted(CATALOG))
        return (
            f'{t(code, "brand")}\n'
            '━━━━━━━━━━━━━━━━━━━\n'
            f'{t(code, "language_title")}\n\n'
            f'🗣 {written}'
        )

    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return

        await message.reply_text(
            self.title(self.db.get_user_language(user.id)),
            parse_mode=ParseMode.HTML,
            reply_markup=self.keyboard(0),
        )

    async def save(self, query, context: ContextTypes.DEFAULT_TYPE, data: str):
        """lang_<code> saves a language, lang_page_<n> turns the menu."""
        value = data.split('_', 1)[1] if '_' in data else ''
        user = query.from_user

        if not user:
            await query.answer()
            return

        if value.startswith('page_'):
            try:
                page = int(value.split('_', 1)[1])
            except ValueError:
                page = 0

            page = max(0, min(page, language_pages() - 1))

            try:
                await query.edit_message_text(
                    self.title(self.db.get_user_language(user.id)),
                    parse_mode=ParseMode.HTML,
                    reply_markup=self.keyboard(page),
                )
            except Exception as exc:
                logging.info('Language menu page edit skipped: %s', exc)

            await query.answer()
            return

        code = value[:8]
        self.db.set_user_language(user.id, code)
        name = language_name(code)

        try:
            await query.edit_message_text(
                f'{t(code, "brand")}\n'
                '━━━━━━━━━━━━━━━━━━━\n'
                + t(code, 'language_saved', name=name),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logging.info('Language confirmation edit skipped: %s', exc)

        await query.answer(f'✅ {name}')
