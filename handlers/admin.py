import html
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database
from services.google_sheet import GoogleSheetService


class AdminHandler:

    def __init__(
        self,
        db: Database,
        config: Config
    ):

        self.db = db
        self.config = config

        self.sheet = GoogleSheetService(
            config
        )

    def is_admin(
        self,
        user_id: int
    ) -> bool:

        return self.db.is_admin(
            user_id,
            self.config.ADMIN_IDS
        )

    def is_super_admin(
        self,
        user_id: int
    ) -> bool:

        return (
            user_id
            == self.config.SUPER_ADMIN_ID
        )

    async def stats(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message

        if (
            not user
            or not message
            or not self.is_admin(user.id)
        ):
            return

        cursor = self.db.conn.cursor()

        active_movies = cursor.execute("""
        SELECT COUNT(*)
        FROM movies
        WHERE status='active'
        """).fetchone()[0]

        deleted_movies = cursor.execute("""
        SELECT COUNT(*)
        FROM movies
        WHERE status='deleted'
        """).fetchone()[0]

        users = cursor.execute("""
        SELECT COUNT(*)
        FROM users
        """).fetchone()[0]

        pending = cursor.execute("""
        SELECT COUNT(*)
        FROM requests
        WHERE status='pending'
        """).fetchone()[0]

        downloads = cursor.execute("""
        SELECT COALESCE(SUM(downloads),0)
        FROM movies
        WHERE status='active'
        """).fetchone()[0]

        await message.reply_text(
            "ߓ <b>Cinema Kingdom Statistics</b>\n\n"
            f"ߎ Active Movies: {active_movies}\n"
            f"ߗ Deleted Movies: {deleted_movies}\n"
            f"ߑ Users: {users}\n"
            f"ߓ Pending Requests: {pending}\n"
            f"⬇ Downloads: {downloads}",
            parse_mode=ParseMode.HTML
        )

    async def requests(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message

        if (
            not user
            or not message
            or not self.is_admin(user.id)
        ):
            return

        requests = self.db.get_pending_requests()

        if not requests:

            await message.reply_text(
                "✅ No pending movie requests."
            )

            return

        text = (
            "ߎ <b>Pending Requests</b>\n\n"
        )

        for request in requests[:20]:

            first_name = html.escape(
                request.get(
                    "first_name"
                )
                or "Unknown"
            )

            movie_title = html.escape(
                request.get(
                    "movie_title"
                )
                or "Unknown"
            )

            text += (
                f"߆ #{request['id']}\n"
                f"ߑ {first_name}\n"
                f"ߎ {movie_title}\n\n"
            )

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML
        )

    async def broadcast(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message

        if (
            not user
            or not message
            or not self.is_admin(user.id)
        ):
            return

        if not context.args:

            await message.reply_text(
                "Usage:\n"
                "/broadcast Your Message"
            )

            return

        body = " ".join(
            context.args
        )

        rows = self.db.conn.execute(
            "SELECT user_id FROM users"
        ).fetchall()

        success = 0
        failed = 0

        for row in rows:

            try:

                await context.bot.send_message(
                    chat_id=row[0],
                    text=body
                )

                success += 1

            except Exception:
                failed += 1

        await message.reply_text(
            "✅ Broadcast completed.\n\n"
            f"Delivered: {success}\n"
            f"Failed: {failed}"
        )

    async def delete_movie(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message
        chat = update.effective_chat

        if not message or not chat:
            return

        # শুধু MyStorage channel/group

        if chat.id != self.config.STORAGE_CHANNEL:

            await message.reply_text(
                "❌ এই command শুধু MyStorage channel-এ "
                "ব্যবহার করা যাবে.\n\n"
                "Example:\n"
                "/delete 12"
            )

            return

        # Channel post হলে effective_user None হতে পারে।
        # User available থাকলে admin check করবে।

        if user and not self.is_admin(
            user.id
        ):

            await message.reply_text(
                "❌ Only bot admins can delete movies."
            )

            return

        if not context.args:

            await message.reply_text(
                "ߗ <b>Delete Movie</b>\n\n"
                "Usage:\n"
                "<code>/delete MovieID</code>\n\n"
                "Example:\n"
                "<code>/delete 12</code>",
                parse_mode=ParseMode.HTML
            )

            return

        try:

            movie_id = int(
                context.args[0]
            )

        except (
            ValueError,
            TypeError
        ):

            await message.reply_text(
                "❌ Invalid Movie ID.\n\n"
                "Example:\n"
                "<code>/delete 12</code>",
                parse_mode=ParseMode.HTML
            )

            return

        movie = self.db.get_movie(
            movie_id
        )

        if not movie:

            old_movie = self.db.get_movie(
                movie_id,
                include_deleted=True
            )

            if (
                old_movie
                and old_movie.get("status")
                == "deleted"
            ):

                await message.reply_text(
                    "⚠️ This movie is already deleted."
                )

            else:

                await message.reply_text(
                    "❌ Movie not found."
                )

            return

        deleted_by_id = (
            user.id
            if user
            else self.config.SUPER_ADMIN_ID
        )

        deleted_by_name = (
            f"@{user.username}"
            if user and user.username
            else str(deleted_by_id)
        )

        deleted_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        deleted = self.db.delete_movie(
            movie_id=movie_id,
            deleted_by=deleted_by_id
        )

        if not deleted:

            await message.reply_text(
                "❌ Delete failed or movie already deleted."
            )

            return

        # Original storage message delete করার চেষ্টা

        if (
            movie.get("source_chat_id")
            and movie.get("source_message_id")
        ):

            try:

                await context.bot.delete_message(
                    chat_id=movie["source_chat_id"],
                    message_id=movie["source_message_id"]
                )

            except Exception:
                pass

        sheet_updated = self.sheet.mark_movie_deleted(
            movie_id=movie_id,
            deleted_by=deleted_by_name,
            deleted_time=deleted_time
        )

        sheet_status = (
            "✅ Google Sheet updated"
            if sheet_updated
            else "⚠️ Google Sheet update failed"
        )

        await message.reply_text(
            "ߗ <b>Movie Deleted Successfully</b>\n\n"
            f"ߎ Movie: <b>{html.escape(movie['title'])}</b>\n"
            f"߆ Movie ID: <code>{movie_id}</code>\n"
            f"ߑ Deleted By: {html.escape(deleted_by_name)}\n"
            f"ߕ Time: {deleted_time}\n\n"
            f"{sheet_status}\n\n"
            "The movie record is preserved in the database "
            "with status: <b>deleted</b>.",
            parse_mode=ParseMode.HTML
        )

    async def add_admin(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message

        if (
            not user
            or not message
            or not self.is_super_admin(user.id)
        ):
            return

        if not context.args:

            await message.reply_text(
                "Usage:\n"
                "/addadmin TelegramUserID"
            )

            return

        try:

            admin_id = int(
                context.args[0]
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid admin ID."
            )

            return

        self.db.add_admin(
            admin_id,
            user.id
        )

        await message.reply_text(
            f"✅ Admin added: {admin_id}"
        )

    async def remove_admin(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message

        if (
            not user
            or not message
            or not self.is_super_admin(user.id)
        ):
            return

        if not context.args:

            await message.reply_text(
                "Usage:\n"
                "/removeadmin TelegramUserID"
            )

            return

        try:

            admin_id = int(
                context.args[0]
            )

        except ValueError:

            await message.reply_text(
                "❌ Invalid admin ID."
            )

            return

        if admin_id == self.config.SUPER_ADMIN_ID:

            await message.reply_text(
                "❌ Super admin cannot be removed."
            )

            return

        removed = self.db.remove_admin(
            admin_id
        )

        if removed:

            await message.reply_text(
                f"✅ Admin removed: {admin_id}"
            )

        else:

            await message.reply_text(
                "⚠️ Admin not found."
            )

    async def list_admins(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message

        if (
            not user
            or not message
            or not self.is_super_admin(user.id)
        ):
            return

        admins = sorted(
            set(
                self.config.ADMIN_IDS
                + self.db.get_admin_ids()
            )
        )

        text = (
            "ߑ <b>Bot Admins</b>\n\n"
        )

        for admin_id in admins:

            role = (
                "Super Admin"
                if admin_id
                == self.config.SUPER_ADMIN_ID
                else "Admin"
            )

            text += (
                f"• <code>{admin_id}</code> — "
                f"{role}\n"
            )

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML
        )

    async def sheet_test(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user
        message = update.effective_message

        if (
            not user
            or not message
            or not self.is_admin(user.id)
        ):
            return

        ok, result = self.sheet.test_connection()

        await message.reply_text(
            (
                "✅ "
                if ok
                else "❌ "
            )
            + result
        )
