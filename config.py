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
        return []
    ids = []
    for item in str(value).split(','):
        item = item.strip()
        if item:
            try:
                ids.append(int(item))
            except ValueError:
                pass
    return ids


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

    # Supports AdsFly, ShrinkEarn, or any API using ?api=KEY&url=DESTINATION&alias=ALIAS
    SHORTENER_API_KEY = os.getenv("SHORTENER_API_KEY", "").strip()
    SHORTENER_BASE_URL = os.getenv("SHORTENER_BASE_URL", "https://adsfly.in/api").strip()
    SHORTENER_ALIAS = os.getenv("SHORTENER_ALIAS", "").strip()

    GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "").strip()
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json").strip()
    GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()

    AUTO_DELETE_TIME = _safe_int(os.getenv("AUTO_DELETE_TIME"), 300)
    COOLDOWN_TIME = _safe_int(os.getenv("COOLDOWN_TIME"), 60)
    MAX_MOVIES_PER_SEARCH = _safe_int(os.getenv("MAX_MOVIES_PER_SEARCH"), 10)
    LINK_EXPIRE_TIME = _safe_int(os.getenv("LINK_EXPIRE_TIME"), 300)

    WELCOME_MSG = """
🎬 <b>Welcome to Cinema Kingdom!</b>

Hello {first_name} 👋

I am your personal movie assistant.

✨ <b>Features</b>
• Search any movie
• Secure shortener download links
• Movie request system
• Fast delivery
• Spam protection

⚠️ <b>Important</b>
• Join our update channel first.
• Download links remain active for only 5 minutes.
• Please do not spam the group.

Happy Watching 🍿
"""

    HELP_MSG = """
📖 <b>Cinema Kingdom Help</b>

🎬 <b>Search</b>
Type any movie name in the group.

🔗 <b>Download</b>
Open the bot and generate your secure download link.

⏳ <b>Link Validity</b>
Links expire after 5 minutes.

🎥 <b>Request</b>
Use <code>/request Movie Name</code> if your movie is not available.

Thank you for using Cinema Kingdom ❤️
"""
