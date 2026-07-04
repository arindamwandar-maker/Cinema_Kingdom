import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
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
        self.shortener = ShortenerService(config.SHORTENER_API_KEY, config.SHORTENER_BASE_URL, config.SHORTENER_ALIAS)
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
                        "🔒 <b>Access Denied</b>\n\n"
                        "Before using Cinema Kingdom you must join:\n\n"
                        "📢 Official Channel\n"
                        "👥 Community Group\n\n"
                        "After joining press <b>I've Joined</b>."
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=Keyboards.force_join_menu(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
                )
                return

        try:
            if data.startswith("movie_"):
                await self.handle_movie_detail(query, int(data.replace("movie_", "", 1)))
                return
            if data.startswith("download_"):
                await self.handle_download(query, int(data.replace("download_", "", 1)), context)
                return
            if data.startswith("info_"):
                await self.handle_movie_info(query, int(data.replace("info_", "", 1)))
                return
            if data.startswith("delete_"):
                await self.handle_delete_prompt(query, int(data.replace("delete_", "", 1)))
                return
            if data.startswith("confirm_delete_"):
                await self.handle_delete_confirm(query, int(data.replace("confirm_delete_", "", 1)))
                return
        except ValueError:
            await query.edit_message_text("❌ Invalid button data.")
            return

        if data == "request":
            await query.edit_message_text(
                "🎬 <b>Movie Request</b>\n\nUse:\n<code>/request Movie Name</code>\n\nExample:\n<code>/request Avatar 2</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        if data == "search":
            await query.edit_message_text(
                "🔎 Send any movie name to search.\n\nExample: <code>Avengers Endgame</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        if data == "check_join":
            if await self.force_join.check_force_join(user.id):
                await query.edit_message_text("✅ Verification successful!\n\nYou can now use Cinema Kingdom.")
            else:
                await query.edit_message_text(
                    "❌ You have not joined yet. Please join both Channel and Group first.",
                    reply_markup=Keyboards.force_join_menu(self.config.CHANNEL_USERNAME, self.config.GROUP_USERNAME),
                )
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
        is_admin = query.from_user.id in self.config.ADMIN_IDS
        title = html.escape(movie["title"])
        desc = html.escape(movie.get("description") or "")
        text = f"🎬 <b>{title}</b>\n\n"
        if desc:
            text += f"📝 {desc}\n\n"
        text += (
            f"👀 Views : {movie['views'] + 1}\n"
            f"⬇ Downloads : {movie['downloads']}\n"
            f"💾 Size : {self.format_size(movie['file_size'])}\n\n"
            "👇 Click below to generate your secure download link."
        )
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(movie_id, is_admin=is_admin),
        )

    async def handle_movie_info(self, query, movie_id: int):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return
        is_admin = query.from_user.id in self.config.ADMIN_IDS
        title = html.escape(movie["title"])
        desc = html.escape(movie.get("description") or "")
        text = (
            "🎬 <b>Movie Information</b>\n\n"
            f"<b>Title:</b> {title}\n"
            f"<b>Size:</b> {self.format_size(movie['file_size'])}\n"
            f"<b>Views:</b> {movie['views']}\n"
            f"<b>Downloads:</b> {movie['downloads']}\n\n"
        )
        if desc:
            text += f"📝 {desc}\n\n"
        text += "⬇ Press <b>Generate Download Link</b> to receive your secure download link."
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.movie_button(movie_id, is_admin=is_admin),
        )

    async def handle_download(self, query, movie_id: int, context: ContextTypes.DEFAULT_TYPE):
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return

        token = self.token_manager.generate_token(movie_id, self.config.LINK_EXPIRE_TIME)
        bot_username = (context.bot.username or self.config.BOT_USERNAME).replace("@", "")
        deep_link = f"https://t.me/{bot_username}?start={token}"
        short_link = await self.shortener.shorten_link(deep_link)
        title = html.escape(movie["title"])
        safe_link = html.escape(short_link)
        text = (
            f"🎬 <b>{title}</b>\n\n"
            "✅ Your secure download link is ready.\n\n"
            f"🔗 {safe_link}\n\n"
            "⏳ <b>Important:</b>\n"
            "• Link expires in <b>5 minutes</b>.\n"
            "• After expiry, generate a new link.\n"
            "• Complete ShrinkEarn, then the bot will send the file.\n\n"
            "🍿 Enjoy your movie!"
        )
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Open ShrinkEarn Link", url=short_link)]
            ]),
        )
        self.db.add_message(query.message.chat.id, query.message.message_id, movie_id, self.config.AUTO_DELETE_TIME)

    async def handle_delete_prompt(self, query, movie_id: int):
        if query.from_user.id not in self.config.ADMIN_IDS:
            await query.answer("Only admin can delete movies.", show_alert=True)
            return
        movie = self.db.get_movie(movie_id)
        if not movie:
            await query.edit_message_text("❌ Movie not found.")
            return
        title = html.escape(movie["title"])
        await query.edit_message_text(
            f"⚠️ Delete this movie?\n\n🎬 <b>{title}</b>\n🆔 #{movie_id}",
            parse_mode=ParseMode.HTML,
            reply_markup=Keyboards.delete_confirm(movie_id),
        )

    async def handle_delete_confirm(self, query, movie_id: int):
        if query.from_user.id not in self.config.ADMIN_IDS:
            await query.answer("Only admin can delete movies.", show_alert=True)
            return
        movie = self.db.get_movie(movie_id)
        deleted = self.db.delete_movie(movie_id)
        if deleted:
            title = html.escape(movie["title"] if movie else str(movie_id))
            await query.edit_message_text(f"✅ Movie deleted successfully.\n\n🎬 <b>{title}</b>\n🆔 #{movie_id}", parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text("❌ Movie delete failed or movie not found.")

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
