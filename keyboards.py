from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)


class Keyboards:

    @staticmethod
    def main_menu():
        return ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(
                        "🎬 Search Movie"
                    )
                ],
                [
                    KeyboardButton(
                        "🎥 Request Movie"
                    )
                ],
                [
                    KeyboardButton(
                        "📢 Join Channel"
                    ),
                    KeyboardButton(
                        "👥 Join Group"
                    )
                ],
                [
                    KeyboardButton(
                        "ℹ️ Help"
                    )
                ]
            ],
            resize_keyboard=True,
            is_persistent=True
        )

    @staticmethod
    def format_size(size):
        if not size:
            return "Unknown"

        value = float(size)

        for unit in (
            "B",
            "KB",
            "MB",
            "GB",
            "TB"
        ):
            if value < 1024:
                return f"{value:.1f} {unit}"

            value /= 1024

        return f"{value:.1f} PB"

    @classmethod
    def movie_buttons(
        cls,
        movies,
        bot_username: str
    ):
        username = (
            bot_username
            or ""
        ).replace("@", "")

        rows = []

        for movie in movies:
            size_text = cls.format_size(
                movie.get("file_size")
            )

            rows.append([
                InlineKeyboardButton(
                    text=(
                        f"🎬 {movie['title']} "
                        f"• {size_text}"
                    ),
                    url=(
                        f"https://t.me/{username}"
                        f"?start=movie_{movie['id']}"
                    )
                )
            ])

        return InlineKeyboardMarkup(rows)

    @staticmethod
    def movie_button(movie_id: int):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔗 Generate Download Link",
                    callback_data=(
                        f"download_{movie_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "ℹ️ Movie Details",
                    callback_data=(
                        f"info_{movie_id}"
                    )
                )
            ]
        ])

    @staticmethod
    def shortener_button(
        short_url: str
    ):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎬 Click Here To Download Movie",
                    url=short_url
                )
            ]
        ])

    @staticmethod
    def force_join_menu(
        channel_username: str,
        group_username: str
    ):
        channel = (
            channel_username
            or ""
        ).replace("@", "")

        group = (
            group_username
            or ""
        ).replace("@", "")

        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=(
                        f"https://t.me/{channel}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 Join Group",
                    url=(
                        f"https://t.me/{group}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ I've Joined",
                    callback_data="check_join"
                )
            ]
        ])

    @staticmethod
    def promo_buttons(
        channel_username: str,
        group_username: str
    ):
        channel = (
            channel_username
            or ""
        ).replace("@", "")

        group = (
            group_username
            or ""
        ).replace("@", "")

        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "👥 Join Group",
                    url=(
                        f"https://t.me/{group}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=(
                        f"https://t.me/{channel}"
                    )
                )
            ]
        ])

    @staticmethod
    def adult_confirmation():
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ I am 18 or above",
                    callback_data="adult_yes"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ I am under 18",
                    callback_data="adult_no"
                )
            ]
        ])

    @staticmethod
    def duplicate_confirmation(
        token: str
    ):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Save Anyway",
                    callback_data=(
                        f"dup_save_{token}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel Upload",
                    callback_data=(
                        f"dup_cancel_{token}"
                    )
                )
            ]
        ])