import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.community import render_request_reminder
from services.google_sheet import GoogleSheetService
from services.shortener import ShortenerService


class AdminHandler:
    def __init__(self, db: Database, config: Config, sheet_sync=None):
        self.db = db
        self.config = config
        self.sheet = GoogleSheetService(config)
        self.sheet_sync = sheet_sync
        self.shortener = ShortenerService(
            config.SHORTENER_API_KEY,
            config.SHORTENER_BASE_URL,
            config.SHORTENER_ALIAS,
            config.SHORTENER_RESPONSE_FORMAT,
        )

    def is_admin(self, user_id: int) -> bool:
        return self.db.is_admin(user_id, self.config.ADMIN_IDS)

    def is_super_admin(self, user_id: int) -> bool:
        return user_id == self.config.SUPER_ADMIN_ID

    def local_time(self) -> str:
        return datetime.now(
            ZoneInfo(self.config.LOCAL_TIMEZONE)
        ).strftime('%Y-%m-%d %I:%M:%S %p')

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        chat = update.effective_chat
        if not message:
            return
        if user:
            if not self.is_admin(user.id):
                return
        elif not chat or chat.id != self.config.STORAGE_CHANNEL:
            # A channel post carries no user, so only accept it from the
            # private MyStorage channel where only he can publish.
            return
        cur = self.db.conn.cursor()
        active = cur.execute("SELECT COUNT(*) FROM movies WHERE status='active'").fetchone()[0]
        deleted = cur.execute("SELECT COUNT(*) FROM movies WHERE status='deleted'").fetchone()[0]
        users = cur.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        pending = cur.execute("SELECT COUNT(*) FROM requests WHERE status='pending'").fetchone()[0]
        downloads = cur.execute("SELECT COALESCE(SUM(downloads),0) FROM movies WHERE status='active'").fetchone()[0]
        link_generated = self.db.count_link_events('Link Generated')
        files_delivered = self.db.count_link_events('File Delivered')
        text = (
            '📊 <b>Cinema Kingdom Statistics</b>\n\n'
            f'🎬 Active Movies: {active}\n🗑 Deleted Movies: {deleted}\n'
            f'👥 Users: {users}\n📥 Pending Requests: {pending}\n'
            f'🔗 Links Generated: {link_generated}\n✅ Files Delivered: {files_delivered}\n⬇ Downloads: {downloads}'
        )
        if chat and chat.type == 'channel':
            # Channels do not allow replying to a post, so send a new post.
            await context.bot.send_message(
                chat_id=chat.id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        else:
            await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """The pending list with a Solved button per request.

        Typed in a group it answers privately, so users never see the admin
        tooling; a DM gets the list straight away. /pending is the same thing.
        """
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return

        rows = self.db.get_pending_requests()

        if rows:
            text, keyboard = render_request_reminder(rows)
        else:
            text = (
                '🎬 <b>Cinema Kingdom</b>\n'
                '━━━━━━━━━━━━━━━━━━━\n'
                '✅ <b>No pending movie requests</b>\n\n'
                'Nobody is waiting for a movie right now.'
            )
            keyboard = None

        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception:
            # The admin never opened /start, so a DM is impossible.
            await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def member_counts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """How big each of our chats is - reported only to the admin who asked."""
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return

        chats = (
            ('👥', self.config.GROUP_NAME, self.config.GROUP_ID),
            ('📢', self.config.CHANNEL_NAME, self.config.CHANNEL_ID),
            ('🗄', 'My Storage', self.config.STORAGE_CHANNEL),
        )

        lines = ['🎬 <b>Cinema Kingdom</b>', '━━━━━━━━━━━━━━━━━━━', '👥 <b>Members</b>', '']

        for emoji, label, chat_id in chats:
            if not chat_id:
                continue
            try:
                count = await context.bot.get_chat_member_count(chat_id)
                lines.append(f'{emoji} <b>{html.escape(label)}</b> — <b>{count}</b> members')
            except Exception as exc:
                lines.append(
                    f'{emoji} <b>{html.escape(label)}</b> — not visible '
                    '(the bot must be a member/admin of that chat)'
                )
                logging.info('Member count unavailable for %s: %s', chat_id, exc)

        lines += ['', f'🕒 {self.local_time()}']
        text = '\n'.join(lines)

        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        if not context.args:
            await message.reply_text('Usage: /broadcast Your Message')
            return
        body = ' '.join(context.args)
        success = 0
        for row in self.db.conn.execute('SELECT user_id FROM users').fetchall():
            try:
                await context.bot.send_message(row[0], body)
                success += 1
            except Exception:
                pass
        await message.reply_text(f'✅ Broadcast completed. Delivered: {success}')

    def _join_buttons(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton('👥 Join Group', url=f'https://t.me/{self.config.GROUP_USERNAME}')],
            [InlineKeyboardButton('📢 Join Channel', url=f'https://t.me/{self.config.CHANNEL_USERNAME}')],
        ])

    @staticmethod
    def _command_body(message, context):
        if context.args:
            return ' '.join(context.args).strip()
        reply = message.reply_to_message if message else None
        if reply:
            return (reply.text or reply.caption or '').strip()
        return ''

    async def _send_destination(self, context, chat_id: int, body: str):
        return await context.bot.send_message(
            chat_id=chat_id,
            text=body,
            reply_markup=self._join_buttons(),
            disable_web_page_preview=True,
        )

    async def send_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        body = self._command_body(message, context)
        if not body:
            await message.reply_text('Usage: /sendgroup Your message\nOr reply to a message with /sendgroup')
            return
        await self._send_destination(context, self.config.GROUP_ID, body)
        await message.reply_text('✅ Message sent to the group.')

    async def send_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        body = self._command_body(message, context)
        if not body:
            await message.reply_text('Usage: /sendchannel Your message\nOr reply to a message with /sendchannel')
            return
        await self._send_destination(context, self.config.CHANNEL_ID, body)
        await message.reply_text('✅ Message sent to the channel.')

    async def send_both(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        body = self._command_body(message, context)
        if not body:
            await message.reply_text('Usage: /sendboth Your message\nOr reply to a message with /sendboth')
            return
        sent = 0
        for chat_id in (self.config.GROUP_ID, self.config.CHANNEL_ID):
            try:
                await self._send_destination(context, chat_id, body)
                sent += 1
            except Exception:
                pass
        await message.reply_text(f'✅ Message sent to {sent}/2 destinations.')

    async def delete_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        if not message or not chat:
            return

        if chat.id != self.config.STORAGE_CHANNEL:
            await message.reply_text('❌ Use this command only in MyStorage: <code>/delete MovieID</code>', parse_mode=ParseMode.HTML)
            return

        # In a channel post Telegram may not provide effective_user. The private storage channel itself is the gate.
        if user and not self.is_admin(user.id):
            await message.reply_text('❌ Only bot admins can delete movies.')
            return

        text = (message.text or message.caption or '').strip()
        parts = text.split()
        if len(parts) < 2:
            await message.reply_text('Usage: <code>/delete 12</code>', parse_mode=ParseMode.HTML)
            return
        try:
            movie_id = int(parts[1])
        except (ValueError, TypeError):
            await message.reply_text('❌ Movie ID must be a number.')
            return

        movie = self.db.get_movie(movie_id)
        if not movie:
            old = self.db.get_movie(movie_id, include_deleted=True)
            await message.reply_text('⚠️ Movie already deleted.' if old else '❌ Movie not found.')
            return

        deleted_by_id = user.id if user else self.config.SUPER_ADMIN_ID
        deleted_by = f'@{user.username}' if user and user.username else str(deleted_by_id)
        deleted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not self.db.delete_movie(movie_id, deleted_by_id):
            await message.reply_text('❌ Delete failed.')
            return

        # Remove the original storage post when possible.
        if movie.get('source_chat_id') and movie.get('source_message_id'):
            try:
                await context.bot.delete_message(movie['source_chat_id'], movie['source_message_id'])
            except Exception:
                pass

        sheet_ok = self.sheet.mark_movie_deleted(movie_id, deleted_by, deleted_time)
        await message.reply_text(
            '🗑 <b>Movie Deleted Successfully</b>\n\n'
            f"🎬 {html.escape(movie['title'])}\n🆔 <code>{movie_id}</code>\n"
            f'👤 {html.escape(deleted_by)}\n🕒 {deleted_time}\n\n'
            f'{"✅ Google Sheet updated" if sheet_ok else "⚠️ Google Sheet not updated"}',
            parse_mode=ParseMode.HTML,
        )

    async def restore_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message, chat = update.effective_user, update.effective_message, update.effective_chat
        if not message or not chat or chat.id != self.config.STORAGE_CHANNEL:
            return
        if user and not self.is_admin(user.id):
            return
        parts = (message.text or '').split()
        if len(parts) < 2:
            await message.reply_text('Usage: /restore MovieID')
            return
        try:
            movie_id = int(parts[1])
        except ValueError:
            await message.reply_text('❌ Invalid Movie ID.')
            return
        if self.db.restore_movie(movie_id):
            self.sheet.mark_movie_active(movie_id)
            await message.reply_text(f'✅ Movie restored: {movie_id}')
        else:
            await message.reply_text('❌ Restore failed.')

    async def rename_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message, chat, user = update.effective_message, update.effective_chat, update.effective_user
        if not message or not chat:
            return

        if chat.id != self.config.STORAGE_CHANNEL:
            await message.reply_text(
                '❌ Use this command only in MyStorage: <code>/rn MovieID New Name</code>',
                parse_mode=ParseMode.HTML
            )
            return

        # In a channel post Telegram may not provide effective_user. The private
        # storage channel itself is the gate.
        if user and not self.is_admin(user.id):
            await message.reply_text('❌ Only bot admins can rename movies.')
            return

        parts = (message.text or message.caption or '').strip().split(None, 2)
        if len(parts) < 3:
            await message.reply_text(
                'Usage: <code>/rn 12 Movie Name</code>',
                parse_mode=ParseMode.HTML
            )
            return

        try:
            movie_id = int(parts[1])
        except ValueError:
            await message.reply_text('❌ Movie ID must be a number.')
            return

        new_name = parts[2].strip()[:200]
        movie = self.db.get_movie(movie_id)

        if not movie:
            await message.reply_text(
                f'❌ No active movie with ID <code>{movie_id}</code>. '
                'Check the Movie ID column in the Storage Uploads sheet, '
                'or restore a deleted movie with /rst.',
                parse_mode=ParseMode.HTML
            )
            return

        if not self.db.update_movie_title(movie_id, new_name):
            await message.reply_text('❌ Rename failed.')
            return

        caption_updated = False

        if self.sheet_sync is not None:
            caption_updated = await self.sheet_sync.sync_caption(context, movie, new_name)

        sheet_ok = self.sheet.set_storage_movie_name(movie_id, new_name)

        text = (
            '✏️ <b>Movie Renamed</b>\n\n'
            f"📝 Old Name: {html.escape(movie['title'])}\n"
            f"🎬 New Name: <b>{html.escape(new_name)}</b>\n"
            f'🆔 Movie ID: <code>{movie_id}</code>\n\n'
            '✅ Search and download pages now use the new name.\n'
            + ('✅ Storage file caption renamed.\n' if caption_updated else
               '⚠️ File caption not renamed — give the bot <b>Edit Messages</b> permission in MyStorage.\n')
            + ('✅ Google Sheet updated.' if sheet_ok else
               '⚠️ Google Sheet not updated — the sheet still shows the old name, '
               'so correct its Movie Name cell yourself.')
        )
        await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        if not context.args:
            await message.reply_text('Usage: /addadmin TelegramUserID')
            return
        try:
            admin_id = int(context.args[0])
        except ValueError:
            await message.reply_text('❌ Invalid admin ID.')
            return
        self.db.add_admin(admin_id, user.id)
        await message.reply_text(f'✅ Admin added: {admin_id}')

    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        if not context.args:
            await message.reply_text('Usage: /removeadmin TelegramUserID')
            return
        try:
            admin_id = int(context.args[0])
        except ValueError:
            await message.reply_text('❌ Invalid admin ID.')
            return
        if admin_id == self.config.SUPER_ADMIN_ID:
            await message.reply_text('❌ Super admin cannot be removed.')
            return
        await message.reply_text('✅ Admin removed.' if self.db.remove_admin(admin_id) else '⚠️ Admin not found.')

    async def list_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_super_admin(user.id):
            return
        admins = sorted(set(self.config.ADMIN_IDS + self.db.get_admin_ids()))
        text = '👑 <b>Bot Admins</b>\n\n' + '\n'.join(
            f"• <code>{aid}</code> — {'Super Admin' if aid == self.config.SUPER_ADMIN_ID else 'Admin'}" for aid in admins
        )
        await message.reply_text(text, parse_mode=ParseMode.HTML)

    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Undo a group ban handed out by the moderation rules."""
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        if not context.args:
            await message.reply_text('Usage: <code>/unban UserID</code>', parse_mode=ParseMode.HTML)
            return
        try:
            target = int(context.args[0])
        except ValueError:
            await message.reply_text('❌ Invalid user ID.')
            return
        try:
            await context.bot.unban_chat_member(self.config.GROUP_ID, target, only_if_banned=True)
        except Exception as exc:
            await message.reply_text(
                f'❌ Could not unban <code>{target}</code>: {html.escape(str(exc))}',
                parse_mode=ParseMode.HTML,
            )
            return
        self.db.clear_offenses(target)
        await message.reply_text(
            f'✅ <code>{target}</code> is allowed in {html.escape(self.config.GROUP_NAME)} again '
            'and their violations are cleared.\n'
            '⚠️ They have to rejoin the group themselves, and only members may invite them '
            'while group invites are locked.',
            parse_mode=ParseMode.HTML,
        )

    async def sheet_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return
        ok, result = self.sheet.test_connection()
        await message.reply_text(('✅ ' if ok else '❌ ') + result)

    async def ad_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return

        probe = 'https://t.me/Cinema_Valut_bot?start=adtest'
        result = await self.shortener.shorten_link(probe)

        if result == probe:
            head = '❌ No ad link was created. The movie would be blocked.\n\n'
        else:
            head = '✅ Ad link works: ' + result + '\n\n'

        await message.reply_text(head + self.shortener.describe())

    async def sync_names(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user, message = update.effective_user, update.effective_message
        if not user or not message or not self.is_admin(user.id):
            return

        if self.sheet_sync is None:
            await message.reply_text('❌ Name sync is not wired up.')
            return

        results = await self.sheet_sync.sync_movie_names(context)

        if not results:
            await message.reply_text(
                '✅ No name edit found.\n\n'
                'Open the <b>Storage Uploads</b> tab, change the <b>Movie Name</b> column, '
                'then run /syncnames again.',
                parse_mode=ParseMode.HTML
            )
            return

        text = '🎬 <b>Movie names from Google Sheet</b>\n\n'

        for item in results[:20]:
            if item['error']:
                text += (
                    f"❌ Row {item['row_number']}: ID <code>{item['movie_id']}</code> "
                    f"— {item['error']}.\n"
                )
            elif item['renamed']:
                mark = '✅' if item['caption_updated'] else '⚠️'
                text += (
                    f"{mark} <code>{item['movie_id']}</code> "
                    f"{html.escape(item['old_name'])}\n"
                    f"   → <b>{html.escape(item['new_name'])}</b>\n"
                )
            else:
                text += (
                    f"• <code>{item['movie_id']}</code> already had the name "
                    f"<b>{html.escape(item['new_name'])}</b>, nothing to change.\n"
                )

        if len(results) > 20:
            text += f"… and {len(results) - 20} more rows.\n"

        text += (
            '\n✅ = bot name and the file caption in MyStorage both renamed.\n'
            '⚠️ = search/downloads use the new name, but the file caption could not be '
            'edited — give the bot <b>Edit Messages</b> permission in MyStorage.'
        )
        await message.reply_text(text, parse_mode=ParseMode.HTML)
