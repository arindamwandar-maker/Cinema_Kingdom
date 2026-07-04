from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


class Keyboards:
    @staticmethod
    def main_menu():
        keyboard = [
            [KeyboardButton("🎬 Search Movie")],
            [KeyboardButton("🎥 Request Movie")],
            [KeyboardButton("📢 Join Channel"), KeyboardButton("👥 Join Group")],
            [KeyboardButton("ℹ️ Help")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

    @staticmethod
    def movie_buttons(movies, bot_username: str):
        """Search result buttons open private bot chat."""
        bot_username = (bot_username or "").replace("@", "")
        keyboard = []
        for movie in movies:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎬 {movie['title']}",
                    url=f"https://t.me/{bot_username}?start=movie_{movie['id']}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton("🎥 Request Movie", callback_data="request"),
            InlineKeyboardButton("🔎 Search Again", callback_data="search"),
        ])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def movie_button(movie_id: int, is_admin: bool = False):
        rows = [
            [InlineKeyboardButton("🔗 Generate Download Link", callback_data=f"download_{movie_id}")],
            [InlineKeyboardButton("ℹ️ Movie Details", callback_data=f"info_{movie_id}")],
        ]
        if is_admin:
            rows.append([InlineKeyboardButton("🗑 Delete Movie", callback_data=f"delete_{movie_id}")])
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def delete_confirm(movie_id: int):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{movie_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"movie_{movie_id}")],
        ])

    @staticmethod
    def force_join_menu(channel_username: str, group_username: str):
        channel = (channel_username or "").replace("@", "")
        group = (group_username or "").replace("@", "")
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel}")],
            [InlineKeyboardButton("👥 Join Group", url=f"https://t.me/{group}")],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")],
        ])

    @staticmethod
    def request_button():
        return InlineKeyboardMarkup([[InlineKeyboardButton("🎥 Request Movie", callback_data="request")]])

    @staticmethod
    def back_button():
        return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
