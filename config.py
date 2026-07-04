import os
from dotenv import load_dotenv

load_dotenv()


def _safe_int(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(value)
    except Exception:
        return default


def _admin_ids(value):
    if not value:
        return [8946393148]
    ids = []
    for item in str(value).split(','):
        item = item.strip()
        if item:
            try:
                ids.append(int(item))
            except ValueError:
                pass
    return ids or [8946393148]


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
    BOT_USERNAME = os.getenv("BOT_USERNAME", "Cinema_Kingdom_Bot").strip().replace("@", "")

    ADMIN_IDS = _admin_ids(os.getenv("ADMIN_IDS", "8946393148"))

    GROUP_ID = _safe_int(os.getenv("GROUP_ID"), -1004495714945)
    CHANNEL_ID = _safe_int(os.getenv("CHANNEL_ID"), -1004479223164)
    STORAGE_CHANNEL = _safe_int(os.getenv("STORAGE_CHANNEL"), -1003272548510)

    GROUP_USERNAME = os.getenv("GROUP_USERNAME", "@cinema_kingdom_vault1").strip()
    CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@Cinema_Kingdom_Vault").strip()
    STORAGE_USERNAME = os.getenv("STORAGE_USERNAME", "@mystoragecinema").strip()

    SHORTENER_API_KEY = os.getenv("SHORTENER_API_KEY", "").strip()
    SHORTENER_BASE_URL = os.getenv("SHORTENER_BASE_URL", "https://shrinkearn.com/api").strip()
    SHORTENER_ALIAS = os.getenv("SHORTENER_ALIAS", "").strip()

    GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "").strip()
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json").strip()

    AUTO_DELETE_TIME = _safe_int(os.getenv("AUTO_DELETE_TIME"), 300)
    COOLDOWN_TIME = _safe_int(os.getenv("COOLDOWN_TIME"), 60)
    MAX_MOVIES_PER_SEARCH = _safe_int(os.getenv("MAX_MOVIES_PER_SEARCH"), 10)
    LINK_EXPIRE_TIME = _safe_int(os.getenv("LINK_EXPIRE_TIME"), 300)

    WELCOME_MSG = """
🎬 **Welcome to Cinema Kingdom!**

Hello {first_name} 👋

I am your personal movie assistant.

✨ **Features**
• Search any movie
• Secure download links
• Movie request system
• Fast delivery
• Spam protection

⚠️ **Important**
• Join our update channel first.
• Download links remain active for only 5 minutes.
• Please do not spam the group.

Happy Watching 🍿
"""

    HELP_MSG = """
📖 **Cinema Kingdom Help**

🎬 **Search**
Type any movie name in the group.

🔗 **Download**
Open the bot and generate your secure download link.

⏳ **Link Validity**
Links expire after 5 minutes.

🎥 **Request**
Use `/request Movie Name` if your movie is not available.

Thank you for using Cinema Kingdom ❤️
"""
