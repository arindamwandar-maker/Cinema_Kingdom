import logging

from telegram import Update

from core import CinemaKingdomCore
from services.logger import setup_logger


class CinemaKingdomBot:
    """Polling entry point, for a host that keeps one process alive
    (Railway, Termux). PythonAnywhere free cannot do this, so use
    web.py plus tick.py instead.
    """

    def __init__(self):
        setup_logger()
        self.core = CinemaKingdomCore()

    def run(self):
        app = self.core.application
        config = self.core.config

        app.job_queue.run_repeating(
            self.core.auto_delete.cleanup,
            interval=30,
            first=10
        )

        app.job_queue.run_repeating(
            self.core.sheet_sync.sync_movie_names,
            interval=config.SHEET_SYNC_INTERVAL,
            first=20
        )

        app.job_queue.run_repeating(
            self.core.promotion.send_promotion,
            interval=config.PROMO_INTERVAL,
            first=30
        )

        logging.info(
            "Cinema Kingdom Bot started in polling mode | Promotion every %ss",
            config.PROMO_INTERVAL
        )

        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


if __name__ == "__main__":
    CinemaKingdomBot().run()
