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

    # Display names shown in the group welcome message and the file caption.
    GROUP_NAME = os.getenv(
        "GROUP_NAME",
        "Cinema Kingdom 3.0"
    ).strip()

    CHANNEL_NAME = os.getenv(
        "CHANNEL_NAME",
        "Cinema Kingdom Community"
    ).strip()

    # Your own @username. It is printed as the super admin contact wherever a
    # message has one; leave it blank and those lines disappear.
    SUPER_ADMIN_USERNAME = os.getenv(
        "SUPER_ADMIN_USERNAME",
        ""
    ).strip().replace("@", "")

    # =========================
    # Ad-link shortener (Shrinkme, GPLinks - same API shape)
    # =========================

    SHORTENER_API_KEY = os.getenv(
        "SHORTENER_API_KEY",
        ""
    ).strip()

    SHORTENER_BASE_URL = os.getenv(
        "SHORTENER_BASE_URL",
        "https://shrinkme.io/api"
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

    # True: if the ad site cannot make a short link, still send the movie
    # through the direct Telegram link (users get files, this click earns
    # nothing).  False: refuse the download instead - no ad, no file.
    ALLOW_DIRECT_LINK = os.getenv(
        "ALLOW_DIRECT_LINK",
        "true"
    ).strip().lower() in ("1", "true", "yes", "on")

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
    # Webhook (PythonAnywhere / any WSGI host)
    # =========================

    # Only the site address, no trailing slash and no path.
    # Example: https://yourusername.pythonanywhere.com
    WEBHOOK_BASE_URL = os.getenv(
        "WEBHOOK_BASE_URL",
        ""
    ).strip().rstrip("/")

    WEBHOOK_PATH = "/telegram-webhook"

    WEBHOOK_URL = (
        f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
        if WEBHOOK_BASE_URL
        else ""
    )

    # Long random string, sent by Telegram as a header on every update.
    # Generate one with: python setup_hook.py --make-secret
    # Anybody who knows your site address can otherwise inject fake updates.
    WEBHOOK_SECRET_TOKEN = os.getenv(
        "WEBHOOK_SECRET_TOKEN",
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

    # Seconds a member must wait between messages in the group. Applies to
    # everyone, admins included; /commands are exempt.
    GROUP_MESSAGE_INTERVAL = max(
        0,
        _safe_int(
            os.getenv("GROUP_MESSAGE_INTERVAL"),
            60
        )
    )

    # Delete any file, video, music, photo or sticker a member sends in the
    # group. Admins are exempt so they can post posters.
    GROUP_BLOCK_ATTACHMENTS = os.getenv(
        "GROUP_BLOCK_ATTACHMENTS",
        "true"
    ).strip().lower() in ("1", "true", "yes", "on")

    # Violations a member collects inside GROUP_OFFENCE_WINDOW before the bot
    # bans them instead of only deleting the message. 1 = ban at once.
    GROUP_BAN_STRIKES = max(
        1,
        _safe_int(
            os.getenv("GROUP_BAN_STRIKES"),
            2
        )
    )

    # Seconds a violation counts towards the next one.
    GROUP_OFFENCE_WINDOW = max(
        60,
        _safe_int(
            os.getenv("GROUP_OFFENCE_WINDOW"),
            86400
        )
    )

    # How often the pending movie request list is sent to the admins.
    REQUEST_REMINDER_INTERVAL = max(
        300,
        _safe_int(
            os.getenv("REQUEST_REMINDER_INTERVAL"),
            3600
        )
    )

    # How often joined members are written to the Group Members worksheet.
    MEMBER_SHEET_INTERVAL = max(
        300,
        _safe_int(
            os.getenv("MEMBER_SHEET_INTERVAL"),
            3600
        )
    )

    MAX_MOVIES_PER_SEARCH = max(
        1,
        _safe_int(
            os.getenv("MAX_MOVIES_PER_SEARCH"),
            15
        )
    )

    # Movie buttons shown per search result page.
    SEARCH_RESULTS_PER_PAGE = max(
        1,
        _safe_int(
            os.getenv("SEARCH_RESULTS_PER_PAGE"),
            5
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
            3600
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

    GROUP_WELCOME_MSG = """Hi {first_name} 👋

Welcome To {group_name}
Here you can download your favourite movies."""

    # Shown under the welcome message only when SUPER_ADMIN_USERNAME is set,
    # so the bot never prints an empty @.
    GROUP_WELCOME_ADMIN_LINE = "👑 Want to work with us? Pin @{admin_username}"

    # Printed on every delivered movie file, above the group links.
    FILE_CAPTION_NOTE = os.getenv(
        "FILE_CAPTION_NOTE",
        "📝 Daily movie uploads and requests in our group. Join and stay tuned!"
    ).strip()

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