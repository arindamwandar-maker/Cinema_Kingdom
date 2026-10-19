from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)

from services.i18n import t


class Keyboards:

    # handlers/search.py matches these exact strings, so keep them in sync.
    MENU_ROWS = [
        ["🎬 Search Movie"],
        ["🎥 Request Movie"],
        ["📢 Join Channel", "👥 Join Group"],
        ["ℹ️ Help"],
    ]

    @staticmethod
    def reply_rows(rows):
        return [[KeyboardButton(label) for label in row] for row in rows]

    @classmethod
    def main_menu(cls):
        return ReplyKeyboardMarkup(
            cls.reply_rows(cls.MENU_ROWS),
            resize_keyboard=True,
            is_persistent=True
        )

    @classmethod
    def contact_menu(cls, code: str = 'en'):
        """Ask for the number, then the usual menu stays underneath it."""
        rows = [
            [
                KeyboardButton(
                    cls.button_label(t(code, 'share_number')),
                    request_contact=True
                )
            ]
        ]
        rows += cls.reply_rows(cls.MENU_ROWS)

        return ReplyKeyboardMarkup(
            rows,
            resize_keyboard=True,
            is_persistent=True
        )

    @staticmethod
    def inline(text, callback_data):
        return InlineKeyboardButton(
            Keyboards.button_label(text),
            callback_data=callback_data
        )

    @staticmethod
    def inline_markup(rows):
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def profile_links(bot_username: str, code: str = 'en'):
        """Group welcome buttons: they open the bot privately."""
        username = (bot_username or '').replace('@', '')
        if not username:
            return None

        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    Keyboards.button_label(t(code, 'select_country')),
                    url=f"https://t.me/{username}?start=country"
                )
            ],
            [
                InlineKeyboardButton(
                    Keyboards.button_label(t(code, 'share_number')),
                    url=f"https://t.me/{username}?start=share_number"
                )
            ]
        ])

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
                    text=cls.button_label(
                        f"{size_text} - {movie['title']}"
                    ),
                    url=(
                        f"https://t.me/{username}"
                        f"?start=movie_{movie['id']}"
                    )
                )
            ])

        return InlineKeyboardMarkup(rows)

    @staticmethod
    def button_label(text, limit=64):
        """Keep labels inside Telegram's 64 byte button limit."""
        label = " ".join((text or "").split())

        while len(label.encode("utf-8")) > limit:
            label = label[:-1].rstrip()

        return label

    @staticmethod
    def paginates(total_pages: int, query: str) -> bool:
        """Whether page buttons can carry this search text.

        The query travels inside callback_data, which Telegram caps at 64
        bytes, so a very long search stays on a single page.
        """
        if total_pages <= 1:
            return False

        return len(f"sp{total_pages}|{query}".encode("utf-8")) <= 64

    @classmethod
    def search_pages(
        cls,
        page: int,
        total_pages: int,
        query: str
    ):
        """Number buttons for a group search result message."""
        if not cls.paginates(total_pages, query):
            return None

        numbers = [
            InlineKeyboardButton(
                text=(
                    f"[{candidate}]"
                    if candidate == page
                    else str(candidate)
                ),
                callback_data=f"sp{candidate}|{query}"
            )
            for candidate in range(1, min(total_pages, 10) + 1)
        ]

        rows = [numbers]

        movers = []

        if page > 1:
            movers.append(
                InlineKeyboardButton(
                    text="◀️ Prev",
                    callback_data=f"sp{page - 1}|{query}"
                )
            )

        if page < total_pages:
            movers.append(
                InlineKeyboardButton(
                    text="Next ▶️",
                    callback_data=f"sp{page + 1}|{query}"
                )
            )

        if movers:
            rows.append(movers)

        return InlineKeyboardMarkup(rows)

    @classmethod
    def search_results_keyboard(
        cls,
        movies,
        bot_username: str,
        page: int,
        total_pages: int,
        query: str
    ):
        keyboard = cls.movie_buttons(movies, bot_username)
        pages = cls.search_pages(page, total_pages, query)

        if pages is None:
            return keyboard

        return InlineKeyboardMarkup(
            list(keyboard.inline_keyboard)
            + list(pages.inline_keyboard)
        )

    @classmethod
    def movie_button(cls, movie_id: int, code: str = 'en'):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'download_link')),
                    callback_data=(
                        f"download_{movie_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'movie_details')),
                    callback_data=(
                        f"info_{movie_id}"
                    )
                )
            ]
        ])

    @classmethod
    def shortener_button(
        cls,
        short_url: str,
        code: str = 'en'
    ):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'download_button')),
                    url=short_url
                )
            ]
        ])

    @classmethod
    def force_join_menu(
        cls,
        channel_username: str,
        group_username: str,
        code: str = 'en'
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
                    cls.button_label(t(code, 'join_channel')),
                    url=(
                        f"https://t.me/{channel}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'join_group')),
                    url=(
                        f"https://t.me/{group}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'joined_yes')),
                    callback_data="check_join"
                )
            ]
        ])

    @classmethod
    def promo_buttons(
        cls,
        channel_username: str,
        group_username: str,
        code: str = 'en'
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
                    cls.button_label(t(code, 'join_group')),
                    url=(
                        f"https://t.me/{group}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'join_channel')),
                    url=(
                        f"https://t.me/{channel}"
                    )
                )
            ]
        ])

    @classmethod
    def request_reminder(cls, requests):
        rows = []

        for request in requests:
            rows.append([
                InlineKeyboardButton(
                    text=cls.button_label(
                        f"✅ Solved — {request['movie_title']}"
                    ),
                    callback_data=f"solved_{request['id']}"
                )
            ])

        return InlineKeyboardMarkup(rows)

    @classmethod
    def adult_confirmation(cls, code: str = 'en'):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'adult_yes')),
                    callback_data="adult_yes"
                )
            ],
            [
                InlineKeyboardButton(
                    cls.button_label(t(code, 'adult_no')),
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