import os
from dotenv import load_dotenv

load_dotenv()


def _safe_int(value, default=0):
    try:
        value = str(value or "").strip()
        return int(value) if value else default
    except (TypeError, ValueError):
        return default


def _admin_ids(value):
    result = []

    for item in str(value or "").split(","):
        item = item.strip()

        if not item:
            continue

        try:
            result.append(int(item))
        except ValueError:
            continue

    return result


class Config:
    # =========================
    # Telegram
    # =========================

    BOT_TOKEN = os.getenv(
        "BOT_TOKEN",
        ""
    ).strip()

    BOT_USERNAME = os.getenv(
        "BOT_USERNAME",
        ""
    ).strip().replace("@", "")

    SUPER_ADMIN_ID = _safe_int(
        os.getenv("SUPER_ADMIN_ID"),
        8946393148
    )

    ADMIN_IDS = _admin_ids(
        os.getenv("ADMIN_IDS", "")
    )

    if SUPER_ADMIN_ID and SUPER_ADMIN_ID not in ADMIN_IDS:
        ADMIN_IDS.insert(0, SUPER_ADMIN_ID)

    GROUP_ID = _safe_int(
        os.getenv("GROUP_ID"),
        -1004495714945
    )

    CHANNEL_ID = _safe_int(
        os.getenv("CHANNEL_ID"),
        -1004479223164
    )

    STORAGE_CHANNEL = _safe_int(
        os.getenv("STORAGE_CHANNEL"),
        -1003272548510
    )

    GROUP_USERNAME = os.getenv(
        "GROUP_USERNAME",
        "cinema_kingdom_vault1"
    ).strip().replace("@", "")

    CHANNEL_USERNAME = os.getenv(
        "CHANNEL_USERNAME",
        "Cinema_Kingdom_Vault"
    ).strip().replace("@", "")

    STORAGE_USERNAME = os.getenv(
        "STORAGE_USERNAME",
        "mystoragecinema"
    ).strip().replace("@", "")

    # =========================
    # GPLinks Shortener
    # =========================

    SHORTENER_API_KEY = os.getenv(
        "SHORTENER_API_KEY",
        ""
    ).strip()

    SHORTENER_BASE_URL = os.getenv(
        "SHORTENER_BASE_URL",
        "https://api.gplinks.com/api"
    ).strip()

    # Keep blank if you do not need custom alias.
    # A unique suffix will automatically be added.
    SHORTENER_ALIAS = os.getenv(
        "SHORTENER_ALIAS",
        ""
    ).strip()

    # json or text
    SHORTENER_RESPONSE_FORMAT = os.getenv(
        "SHORTENER_RESPONSE_FORMAT",
        "json"
    ).strip().lower() or "json"

    # =========================
    # Google Sheet
    # =========================

    GOOGLE_SHEET_URL = os.getenv(
        "GOOGLE_SHEET_URL",
        ""
    ).strip()

    GOOGLE_CREDENTIALS_FILE = os.getenv(
        "GOOGLE_CREDENTIALS_FILE",
        "credentials.json"
    ).strip()

    GOOGLE_CREDENTIALS_JSON = os.getenv(
        "GOOGLE_CREDENTIALS_JSON",
        ""
    ).strip()

    GOOGLE_CREDENTIALS_BASE64 = os.getenv(
        "GOOGLE_CREDENTIALS_BASE64",
        ""
    ).strip()

    # =========================
    # Database / Settings
    # =========================

    DB_PATH = os.getenv(
        "DB_PATH",
        "bot.db"
    ).strip() or "bot.db"

    AUTO_DELETE_TIME = max(
        30,
        _safe_int(
            os.getenv("AUTO_DELETE_TIME"),
            300
        )
    )

    COOLDOWN_TIME = max(
        0,
        _safe_int(
            os.getenv("COOLDOWN_TIME"),
            60
        )
    )

    MAX_MOVIES_PER_SEARCH = max(
        1,
        _safe_int(
            os.getenv("MAX_MOVIES_PER_SEARCH"),
            10
        )
    )

    LINK_EXPIRE_TIME = max(
        60,
        _safe_int(
            os.getenv("LINK_EXPIRE_TIME"),
            300
        )
    )

    # Option 2 automatic delivery delay
    AUTO_FILE_DELAY = max(
        1,
        _safe_int(
            os.getenv("AUTO_FILE_DELAY"),
            5
        )
    )

    SHEET_SYNC_INTERVAL = max(
        60,
        _safe_int(
            os.getenv("SHEET_SYNC_INTERVAL"),
            60
        )
    )

    PROMO_INTERVAL = max(
        120,
        _safe_int(
            os.getenv("PROMO_INTERVAL"),
            120
        )
    )

    LOCAL_TIMEZONE = os.getenv(
        "LOCAL_TIMEZONE",
        "Asia/Kolkata"
    ).strip() or "Asia/Kolkata"

    ADULT_KEYWORDS = (
        "18+",
        "adult",
        "xxx",
        "porn",
        "erotic",
        "uncut adult",
        "mature 18"
    )

    WELCOME_MSG = """
🎬 <b>Welcome to Cinema Kingdom!</b>

Hello {first_name} 👋

Movie search is available only inside the Cinema Kingdom group.

Choose an option using the buttons below.

⏳ Download links, movie files and temporary messages are removed after 5 minutes.
"""

    HELP_MSG = """
📖 <b>Cinema Kingdom Help</b>

🎬 <b>Search Movie</b>
Type the movie name inside the Cinema Kingdom group.

🎥 <b>Request Movie</b>
Use:
<code>/request Movie Name</code>

🔗 <b>Download</b>
Select a movie, open the bot and press Generate Download Link.

⏱ <b>Automatic Delivery</b>
After the short link is generated, the movie will arrive automatically after a few seconds.

⚠️ <b>Expiry</b>
Download messages and movie files are removed after 5 minutes.
"""