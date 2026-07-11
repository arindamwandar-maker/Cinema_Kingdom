import os
from dotenv import load_dotenv

load_dotenv()


def _safe_int(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
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
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip().replace("@", "")

    SUPER_ADMIN_ID = _safe_int(os.getenv("SUPER_ADMIN_ID"), 8946393148)
    ADMIN_IDS = _admin_ids(os.getenv("ADMIN_IDS", ""))
    if SUPER_ADMIN_ID and SUPER_ADMIN_ID not in ADMIN_IDS:
        ADMIN_IDS.insert(0, SUPER_ADMIN_ID)

    GROUP_ID = _safe_int(os.getenv("GROUP_ID"), -1004495714945)
    CHANNEL_ID = _safe_int(os.getenv("CHANNEL_ID"), -1004479223164)
    STORAGE_CHANNEL = _safe_int(os.getenv("STORAGE_CHANNEL"), -1003272548510)

    GROUP_USERNAME = os.getenv("GROUP_USERNAME", "cinema_kingdom_vault1").strip().replace("@", "")
    CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "Cinema_Kingdom_Vault").strip().replace("@", "")
    STORAGE_USERNAME = os.getenv("STORAGE_USERNAME", "mystoragecinema").strip().replace("@", "")

    SHORTENER_API_KEY = os.getenv("SHORTENER_API_KEY", "").strip()
    SHORTENER_BASE_URL = os.getenv("SHORTENER_BASE_URL", "https://adsfly.in/api").strip()
    SHORTENER_ALIAS = os.getenv("SHORTENER_ALIAS", "").strip()

    GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "").strip()
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json").strip()
    GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    GOOGLE_CREDENTIALS_BASE64 = os.getenv("GOOGLE_CREDENTIALS_BASE64", "").strip()

    DB_PATH = os.getenv("DB_PATH", "bot.db").strip() or "bot.db"
    AUTO_DELETE_TIME = _safe_int(os.getenv("AUTO_DELETE_TIME"), 300)
    COOLDOWN_TIME = _safe_int(os.getenv("COOLDOWN_TIME"), 60)
    MAX_MOVIES_PER_SEARCH = _safe_int(os.getenv("MAX_MOVIES_PER_SEARCH"), 10)
    LINK_EXPIRE_TIME = _safe_int(os.getenv("LINK_EXPIRE_TIME"), 300)

    WELCOME_MSG = """
🎬 <b>Welcome to Cinema Kingdom!</b>

Hello {first_name} 👋

Use the buttons below or type a movie name in the group.

⚠️ Download links remain active for 5 minutes.
🍿 Happy watching!
"""

    HELP_MSG = """
📖 <b>Cinema Kingdom Help</b>

🎬 <b>Search Movie</b>
Type a movie name in the Cinema Kingdom group.

🎥 <b>Request Movie</b>
Use <code>/request Movie Name</code>.

🔗 <b>Download</b>
Select a movie, open the bot, then press Generate Download Link.

⏳ <b>Expiry</b>
Search results and download messages are removed after 5 minutes.
"""
