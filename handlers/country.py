"""The /country picker and the optional /number share.

Telegram never gives a bot a member's phone number. The only way to get one is
the request_contact button, which sends the number because the member pressed
it - so a member who ignores both questions simply stays blank in the sheet.
"""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.countries import (
    NAMES,
    country_name,
    country_pages,
    country_rows,
    country_from_phone,
)
from services.i18n import t


class CountryHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config

    def keyboard(self, page: int = 0):
        rows = country_rows(page)

        if page == 0:
            if country_pages() > 1:
                rows.append([Keyboards.inline(t('en', 'country_more'), 'country_page_1')])
        else:
            nav = []
            if page > 1:
                nav.append(Keyboards.inline('⬅️', f'country_page_{page - 1}'))
            nav.append(Keyboards.inline('🔝', 'country_page_0'))
            if page + 1 < country_pages():
                nav.append(Keyboards.inline('➡️', f'country_page_{page + 1}'))
            rows.append(nav)

        rows.append([Keyboards.inline(t('en', 'share_number'), 'country_number')])

        return Keyboards.inline_markup(rows)

    def title(self, code: str) -> str:
        return (
            f'{t(code, "brand")}\n'
            '━━━━━━━━━━━━━━━━━━━\n'
            f'{t(code, "country_title")}'
        )

    def number_text(self, code: str) -> str:
        return (
            f'{t(code, "brand")}\n'
            '━━━━━━━━━━━━━━━━━━━\n'
            f'{t(code, "number_title")}'
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

    async def ask_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the reply keyboard that asks Telegram for the contact."""
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return

        code = self.db.get_user_language(user.id)
        await message.reply_text(
            self.number_text(code),
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.contact_menu(code),
        )

    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Store the number a member just volunteered."""
        message = update.effective_message
        user = update.effective_user
        if not message or not user or not message.contact:
            return

        contact = message.contact
        phone = (contact.phone_number or '').strip()

        self.db.add_or_update_user(
            user.id, user.username or '', user.first_name or '', user.last_name or ''
        )
        code = self.db.get_user_language(user.id)

        if not phone:
            await message.reply_text(
                t(code, 'number_failed'),
                parse_mode=ParseMode.HTML,
                reply_markup=Keyboards.main_menu(),
            )
            return

        country = country_from_phone(phone)
        self.db.set_user_phone(user.id, phone, country)

        lines = [
            t(code, 'brand'),
            '━━━━━━━━━━━━━━━━━━━',
            t(code, 'number_shared', phone=phone),
        ]

        name = country_name(country)
        if name:
            lines.append(f'🌍 {name}')

        await message.reply_text(
            '\n'.join(lines),
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.main_menu(),
        )

    async def save(self, query, context: ContextTypes.DEFAULT_TYPE, data: str):
        """country_<CODE> stores a country, country_page_<n> turns the picker."""
        value = data.split('_', 1)[1] if '_' in data else ''
        user = query.from_user

        if not user:
            await query.answer()
            return

        code = self.db.get_user_language(user.id)

        if value == 'number':
            chat = query.message.chat if query.message else None
            if chat and chat.type != 'private':
                # A reply keyboard in a group is shown to every member there,
                # so the contact button only makes sense in a private chat.
                await query.answer(t(code, 'number_private'), show_alert=True)
                return

            try:
                await query.edit_message_text(
                    self.number_text(code),
                    parse_mode=ParseMode.HTML,
                    reply_markup=Keyboards.contact_menu(code),
                )
            except Exception as exc:
                logging.info('Number ask not shown: %s', exc)

            await query.answer()
            return

        if value.startswith('page_'):
            try:
                page = int(value.split('_', 1)[1])
            except ValueError:
                page = 0

            page = max(0, min(page, country_pages() - 1))

            try:
                await query.edit_message_text(
                    self.title(code),
                    parse_mode=ParseMode.HTML,
                    reply_markup=self.keyboard(page),
                )
            except Exception as exc:
                logging.info('Country picker page edit skipped: %s', exc)

            await query.answer()
            return

        selected = value[:8].upper()
        if selected not in NAMES:
            await query.answer(t(code, 'country_unknown'), show_alert=True)
            return

        self.db.add_or_update_user(user.id, user.username or '', user.first_name or '', user.last_name or '')
        self.db.set_user_country(user.id, selected)
        name = country_name(selected)

        try:
            await query.edit_message_text(
                f'{t(code, "brand")}\n'
                '━━━━━━━━━━━━━━━━━━━\n'
                + t(code, 'country_saved', name=name),
                parse_mode=ParseMode.HTML,
            )
        except Exception as exc:
            logging.info('Country confirmation edit skipped: %s', exc)

        await query.answer(f'✅ {name}')
