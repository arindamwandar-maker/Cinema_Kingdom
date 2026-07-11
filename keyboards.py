from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


class Keyboards:
    @staticmethod
    def main_menu():
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton('🎬 Search Movie')],
                [KeyboardButton('🎥 Request Movie')],
                [KeyboardButton('📢 Join Channel'), KeyboardButton('👥 Join Group')],
                [KeyboardButton('ℹ️ Help')],
            ],
            resize_keyboard=True,
            is_persistent=True,
        )

    @staticmethod
    def movie_buttons(movies, bot_username: str):
        username = (bot_username or '').replace('@', '')
        rows = [[InlineKeyboardButton(f"🎬 {m['title']}", url=f'https://t.me/{username}?start=movie_{m["id"]}')]
                for m in movies]
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def movie_button(movie_id: int):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton('🔗 Generate Download Link', callback_data=f'download_{movie_id}')],
            [InlineKeyboardButton('ℹ️ Movie Details', callback_data=f'info_{movie_id}')],
        ])

    @staticmethod
    def force_join_menu(channel_username: str, group_username: str):
        channel = (channel_username or '').replace('@', '')
        group = (group_username or '').replace('@', '')
        return InlineKeyboardMarkup([
            [InlineKeyboardButton('📢 Join Channel', url=f'https://t.me/{channel}')],
            [InlineKeyboardButton('👥 Join Group', url=f'https://t.me/{group}')],
            [InlineKeyboardButton("✅ I've Joined", callback_data='check_join')],
        ])
