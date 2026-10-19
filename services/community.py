import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram.constants import ParseMode

from config import Config
from database import Database
from keyboards import Keyboards
from services.countries import country_name
from services.google_sheet import GoogleSheetService

MAX_REQUESTS_PER_REMINDER = 25


def render_request_reminder(requests):
    """Pending request list as (message text, keyboard).

    The reminder job sends it, /pending sends the same thing on demand and the
    solve button edits that message, so all three build it here.
    """
    listed = requests[:MAX_REQUESTS_PER_REMINDER]

    lines = [
        '🎬 <b>Cinema Kingdom</b>',
        '━━━━━━━━━━━━━━━━━━━',
        f'📝 <b>Pending Movie Requests</b> — <b>{len(requests)}</b>',
        '',
        'Press ✅ Solved once the movie is uploaded.',
        '',
    ]

    for index, request in enumerate(listed, start=1):
        username = request.get('username') or ''
        requester = f'@{username}' if username else (request.get('first_name') or 'Unknown')

        title = request['movie_title']
        if request.get('year'):
            title = f"{title} ({request['year']})"

        extras = ' · '.join(
            part for part in (request.get('audio_language'), request.get('resolution')) if part
        )

        lines.append(f"{index}. <b>{html.escape(title)}</b>")
        if extras:
            lines.append(f"   🔊 {html.escape(extras)}")
        lines.append(
            f"   👤 {html.escape(requester)} · 📝 <code>#{request['id']}</code>"
        )
        lines.append('')

    if len(requests) > len(listed):
        lines.append(f'… and {len(requests) - len(listed)} more.')

    return '\n'.join(lines), Keyboards.request_reminder(listed)


class CommunityService:
    """Recurring work around requests and members: the hourly admin reminder
    and the Group Members worksheet."""

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)

    def local_time(self) -> str:
        return datetime.now(
            ZoneInfo(self.config.LOCAL_TIMEZONE)
        ).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def format_date(value) -> str:
        if not value:
            return ''
        try:
            return datetime.fromisoformat(str(value)).strftime('%Y-%m-%d %H:%M')
        except ValueError:
            return str(value)

    def recipient_ids(self):
        """Every bot admin: /addadmin people count as much as ADMIN_IDS."""
        return sorted(
            set(self.config.ADMIN_IDS)
            | {self.config.SUPER_ADMIN_ID}
            | set(self.db.get_admin_ids())
        )

    async def send_pending_list(self, bot, chat_id: int) -> int:
        """Send the pending requests with their Solved buttons. Returns the count."""
        requests = self.db.get_pending_requests()
        text, keyboard = render_request_reminder(requests) if requests else (
            '🎬 <b>Cinema Kingdom</b>\n'
            '━━━━━━━━━━━━━━━━━━━\n'
            '✅ <b>No pending movie requests</b>\n\n'
            'Nobody is waiting for a movie right now.',
            None,
        )
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
        return len(requests)

    async def send_request_reminders(self, context):
        requests = self.db.get_pending_requests()
        if not requests:
            return

        text, keyboard = render_request_reminder(requests)

        for admin_id in self.recipient_ids():
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            except Exception as exc:
                # An admin who blocked the bot must not stop the others.
                logging.info('Request reminder not delivered to %s: %s', admin_id, exc)

    def member_rows(self):
        rows = []

        for user in self.db.get_users():
            user_id = user['user_id']

            if user_id == self.config.SUPER_ADMIN_ID:
                role = 'Super Admin'
            elif self.db.is_admin(user_id, self.config.ADMIN_IDS):
                role = 'Admin'
            else:
                role = 'Member'

            name = ' '.join(
                part for part in (user.get('first_name') or '', user.get('last_name') or '') if part
            )
            username = user.get('username') or ''

            rows.append([
                str(user_id),
                f'@{username}' if username else '',
                name,
                role,
                self.format_date(user.get('join_date')),
                self.format_date(user.get('last_active')),
                user.get('total_requests') or 0,
                country_name(user.get('country') or ''),
                user.get('phone_number') or '',
            ])

        return rows

    async def sync_group_members(self, context):
        added = self.sheet.add_group_members(self.member_rows())

        if added:
            logging.info('Group Members sheet: %s new users written', added)
