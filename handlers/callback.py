import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import Config
from database import Database
from keyboards import Keyboards
from services.force_join import ForceJoinService
from services.shortener import ShortenerService
from services.token_manager import TokenManager


class CallbackHandler:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.shortener = ShortenerService(config.SHORTENER_API_KEY, config.SHORTENER_BASE_URL)
        self.force_join = ForceJoinService(config)
        self.token_manager = TokenManager()

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        await query.answer()
        data = query.data or ""
        user = query.from_user

        if data != "check_join":
            joined = await self.force_join.check_force_join(user.id)
            if not joined:
                await query.edit_message_text(
                    text=(
                        "🔒 **Access Denied**\n\n"
                        "Before using Cinema Kingdom you must join:\n\n"
                        "📢 Official Channel\n"
                        "👥 Community Group\n\n"
                        "After joining press **I've Joined**."
                    ),
                    parse_mode="Markdown",
                    reply_markup=Keyboards.force_join_menu(),
                )
                return

        try:
            if data.startswith("movie_"):
                await self.handle_movie_detail(query, int(data.replace("movie_", "")))
                return
            if data.startswith("download_"):
                await self.handle_download(query, int(data.replace("download_", "")))
                return
            if data.startswith("info_"):
                await self.handle_movie_info(query, int(data.replace("info_", "")))
                return
        except ValueError:
            await query.edit_message_text("❌ Invalid button data.")
            return

        if data == "request":
            await query.edit_message_text(
                "🎬 **Movie Request**\n\nUse:\n`/request Movie Name`\n\nExample:\n`/request Avatar 2`",
                parse_mode="Markdown",
            )
            return

        if data == "search":
            await query.edit_message_text("🔎 Send any movie name to search.\n\nExample: `Avengers Endgame`", parse_mode="Markdown")
            return

        if data == "check_join":
            if await self.force_join.check_force_join(user.id):
                await query.edit_message_text("✅ Verification successful!\n\nYou can now use Cinema Kingdom.")
            else:
                await query.edit_message_text(
                    "❌ You have not joined yet. Please join both Channel and Group first.",
                    reply_markup=Keyboards.force_join_menu(),
                )
            return

        if data == "admin_requests":
            await self.handle_admin_requests(query)
            return
        if data == "admin_stats":
            await self.handle_admin_stats(query)
            return
        if data == "admin_users":
            await self.handle_admin_users(query)
            return
        if data == "back":
            try:
                await query.message.delete()
            except Exception as exc:
                logging.warning("Back delete failed: %s", exc)

    async def handle_movie_detail(self, query, movie_id: int):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return
        self.db.increment_views(movie_id)
        text = f"🎬 **{movie['title']}**\n\n"
        if movie.get("description"):
            text += f"📝 {movie['description']}\n\n"
        text += (
            f"👀 Views : {movie['views'] + 1}\n"
            f"⬇ Downloads : {movie['downloads']}\n"
            f"💾 Size : {self.format_size(movie['file_size'])}\n\n"
            "👇 Click below to generate your secure download link."
        )
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=Keyboards.movie_button(movie_id))

    async def handle_movie_info(self, query, movie_id: int):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return
        text = (
            "🎬 **Movie Information**\n\n"
            f"**Title:** {movie['title']}\n"
            f"**Size:** {self.format_size(movie['file_size'])}\n"
            f"**Views:** {movie['views']}\n"
            f"**Downloads:** {movie['downloads']}\n\n"
        )
        if movie.get("description"):
            text += f"📝 {movie['description']}\n\n"
        text += "⬇ Press **Generate Download Link** to receive your secure download link."
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=Keyboards.movie_button(movie_id))

    async def handle_download(self, query, movie_id: int):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return
        token = self.token_manager.generate_token(movie_id, self.config.LINK_EXPIRE_TIME)
        deep_link = f"https://t.me/{self.config.BOT_USERNAME}?start={token}"
        short_link = await self.shortener.shorten_link(deep_link)
        text = (
            f"🎬 **{movie['title']}**\n\n"
            "✅ Your secure download link is ready.\n\n"
            f"🔗 {short_link}\n\n"
            "⏳ **Important:**\n"
            "• Link expires in **5 minutes**.\n"
            "• After expiry, generate a new link.\n"
            "• Do not share this link with others.\n\n"
            "🍿 Enjoy your movie!"
        )
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Open ShrinkEarn Link", url=short_link)]
            ]),
        )
        self.db.add_message(query.message.chat.id, query.message.message_id, movie_id, self.config.AUTO_DELETE_TIME)

    async def handle_admin_requests(self, query):
        if query.from_user.id not in self.config.ADMIN_IDS:
            await query.answer("Unauthorized", show_alert=True)
            return
        requests = self.db.get_pending_requests()
        if not requests:
            await query.edit_message_text("📭 No pending movie requests.")
            return
        text = "🎬 **Pending Movie Requests**\n\n"
        for req in requests[:20]:
            text += (
                f"🆔 #{req['id']}\n"
                f"👤 {req.get('first_name') or 'Unknown'}\n"
                f"🔹 @{req.get('username') or 'No Username'}\n"
                f"🎥 {req['movie_title']}\n"
                f"📅 {req['request_date']}\n\n"
            )
        await query.edit_message_text(text, parse_mode="Markdown")

    async def handle_admin_stats(self, query):
        if query.from_user.id not in self.config.ADMIN_IDS:
            await query.answer("Unauthorized", show_alert=True)
            return
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movies")
        total_movies = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status='pending'")
        pending_requests = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(downloads) FROM movies")
        total_downloads = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(views) FROM movies")
        total_views = cursor.fetchone()[0] or 0
        text = (
            "📊 **Cinema Kingdom Statistics**\n\n"
            f"🎬 Movies : {total_movies}\n"
            f"👥 Users : {total_users}\n"
            f"📥 Pending Requests : {pending_requests}\n"
            f"👀 Total Views : {total_views}\n"
            f"⬇ Total Downloads : {total_downloads}"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    async def handle_admin_users(self, query):
        if query.from_user.id not in self.config.ADMIN_IDS:
            await query.answer("Unauthorized", show_alert=True)
            return
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT first_name, username, last_active FROM users ORDER BY last_active DESC LIMIT 20")
        rows = cursor.fetchall()
        if not rows:
            await query.edit_message_text("No users found.")
            return
        text = "👥 **Latest Active Users**\n\n"
        for row in rows:
            text += f"👤 {row[0] or 'Unknown'}\n🔹 @{row[1] or 'None'}\n🕒 {row[2] or '-'}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    @staticmethod
    def format_size(size):
        if not size:
            return "Unknown"
        size = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
