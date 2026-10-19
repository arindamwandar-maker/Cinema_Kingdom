import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.google_sheet import GoogleSheetService
from services.i18n import t
from services.request_format import parse_request


class RequestHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)

    def usage(self, code: str) -> str:
        return f'{t(code, "brand")}\n━━━━━━━━━━━━━━━━━━━\n{t(code, "request_hint")}'

    async def request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        user = update.effective_user
        if not message or not user:
            return
        text = (message.text or '').strip()
        chat = update.effective_chat
        if chat and chat.id == self.config.GROUP_ID:
            self.db.add_message(chat.id, message.message_id, seconds=self.config.AUTO_DELETE_TIME)

        self.db.add_or_update_user(user.id, user.username or '', user.first_name or '', user.last_name or '')
        code = self.db.get_user_language(user.id)
        body = text.split(maxsplit=1)[1].strip() if len(text.split(maxsplit=1)) > 1 else ''
        if not body:
            await message.reply_text(self.usage(code), parse_mode=ParseMode.HTML)
            return

        parsed = parse_request(body)
        request_id = self.db.add_request(
            user.id,
            parsed['title'],
            year=parsed['year'],
            audio_language=parsed['audio_language'],
            resolution=parsed['resolution'],
        )
        self.db.increment_user_requests(user.id)

        # The sheet row carries the whole request so an admin can find the file
        # by name. Whether the sheet accepted it stays between the bot and the
        # admins - users are not told about the spreadsheet.
        sheet_ok = self.sheet.add_request(
            request_id,
            user.id,
            user.username or '',
            user.first_name or '',
            parsed['display'],
            datetime.now(),
        )

        local_time = datetime.now(ZoneInfo(self.config.LOCAL_TIMEZONE)).strftime('%Y-%m-%d %I:%M:%S %p')
        self.sheet.log_download_status(
            status='Requested',
            movie_name=parsed['display'],
            movie_id='',
            user_id=user.id,
            username=f'@{user.username}' if user.username else '',
            event_time=local_time,
        )

        if not sheet_ok:
            logging.info('Request %s not written to the Google Sheet', request_id)

        for admin in self.admin_ids():
            try:
                await context.bot.send_message(
                    admin,
                    self.admin_notification(user, parsed, request_id),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                pass

        sent = await message.reply_text(
            self.confirmation(parsed, request_id, code),
            parse_mode=ParseMode.HTML,
        )
        self.db.add_message(sent.chat.id, sent.message_id, seconds=self.config.AUTO_DELETE_TIME)

    @staticmethod
    def confirmation(parsed: dict, request_id: int, code: str = 'en') -> str:
        lines = [
            t(code, 'brand'),
            '━━━━━━━━━━━━━━━━━━━',
            t(code, 'request_ok'),
            '',
            f"{t(code, 'lbl_movie')}: <b>{html.escape(parsed['title'])}</b>",
        ]
        if parsed['year']:
            lines.append(f"{t(code, 'lbl_year')}: <b>{html.escape(parsed['year'])}</b>")
        if parsed['audio_language']:
            lines.append(f"{t(code, 'lbl_audio')}: <b>{html.escape(parsed['audio_language'])}</b>")
        if parsed['resolution']:
            lines.append(f"{t(code, 'lbl_quality')}: <b>{html.escape(parsed['resolution'])}</b>")
        lines += [
            '',
            f"{t(code, 'lbl_request_id')}: <code>{request_id}</code>",
            t(code, 'notify_line'),
        ]
        return '\n'.join(lines)

    @staticmethod
    def admin_notification(user, parsed: dict, request_id: int) -> str:
        requester = html.escape(user.first_name or 'Unknown')
        username = f"@{user.username}" if user.username else 'no username'
        return (
            '🎬 <b>New Movie Request</b>\n'
            '━━━━━━━━━━━━━━━━━━━\n'
            f"🎥 <b>{html.escape(parsed['display'])}</b>\n"
            f'👤 {requester} — <code>{html.escape(username)}</code>\n'
            f'🆔 <code>{user.id}</code> · 📝 Request <code>#{request_id}</code>'
        )

    def admin_ids(self):
        return sorted(
            set(self.config.ADMIN_IDS)
            | {self.config.SUPER_ADMIN_ID}
            | set(self.db.get_admin_ids())
        )
