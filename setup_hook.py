"""One-off helper for the Telegram webhook.

    python setup_hook.py --make-secret   print a secret token to put in .env
    python setup_hook.py                 register the webhook with Telegram
    python setup_hook.py --status        show what Telegram currently has
    python setup_hook.py --delete        remove the webhook (to go back to polling)

Run this from a PythonAnywhere bash console, inside the project folder, after
WEBHOOK_BASE_URL and WEBHOOK_SECRET_TOKEN are set in .env.
"""

import argparse
import asyncio
import json
import secrets
import sys

from config import Config


def make_secret():
    print(
        "Add this line to your .env file:\n"
        f"\nWEBHOOK_SECRET_TOKEN={secrets.token_urlsafe(32)}\n"
    )
    return 0


async def webhook_action(action):
    config = Config()

    if action != "delete" and not config.WEBHOOK_BASE_URL:
        print("WEBHOOK_BASE_URL is empty. Set it in .env first, for example:")
        print("  WEBHOOK_BASE_URL=https://yourusername.pythonanywhere.com")
        return 1

    if action == "register" and not config.WEBHOOK_SECRET_TOKEN:
        print("WEBHOOK_SECRET_TOKEN is empty. Run: python setup_hook.py --make-secret")
        return 1

    # Imported late so --make-secret works without a token or database.
    from core import CinemaKingdomCore

    core = CinemaKingdomCore()

    await core.application.initialize()
    bot = core.application.bot

    try:
        if action == "register":
            await bot.set_webhook(
                url=config.WEBHOOK_URL,
                secret_token=config.WEBHOOK_SECRET_TOKEN,
                drop_pending_updates=True,
            )
            print(f"Webhook registered: {config.WEBHOOK_URL}")

        elif action == "delete":
            await bot.delete_webhook(drop_pending_updates=True)
            print("Webhook removed. Polling (bot.py) can run again.")

        info = await bot.get_webhook_info()
        print(json.dumps(info.to_dict(), indent=2, ensure_ascii=False))

    finally:
        await core.application.shutdown()

    if action == "register":
        # Only one delivery method may be active, so a second instance would
        # now fail with 409 Conflict.
        print("\nStop the Railway service now, or the two instances will fight for updates.")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Manage the Cinema Kingdom webhook")
    parser.add_argument("--make-secret", action="store_true", help="print a secret token")
    parser.add_argument("--status", action="store_true", help="show current webhook info")
    parser.add_argument("--delete", action="store_true", help="remove the webhook")
    args = parser.parse_args()

    if args.make_secret:
        return make_secret()

    action = "delete" if args.delete else "status" if args.status else "register"
    return asyncio.run(webhook_action(action))


if __name__ == "__main__":
    sys.exit(main())
