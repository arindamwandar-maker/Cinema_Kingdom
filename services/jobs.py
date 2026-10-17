"""Timed jobs for webhook mode.

bot.py registers these with the JobQueue, which needs one process that stays
alive. A WSGI host has no such process, so the jobs are instead run when
something already wakes the app:

  * after every Telegram update (web.py piggybacks a check)
  * on GET /tick, called by the GitHub Actions keep-alive workflow

Each job keeps its own "last run" timestamp in a JSON file next to the
database, so the intervals survive worker reloads.
"""

import asyncio
import json
import logging
import os
import time

CLEANUP_INTERVAL = 30


class JobContext:
    """Stands in for the Context object the JobQueue normally passes to jobs."""

    def __init__(self, bot, bot_data):
        self.bot = bot
        self.bot_data = bot_data


def state_path_for(db_path):
    folder = os.path.dirname(os.path.abspath(db_path))
    return os.path.join(folder, "tick_state.json")


def restore_chat_ids(state):
    """JSON turns the chat id keys into strings.

    PromotionService looks the previous message up by int chat id, so without
    this it never finds the old promotion message and stops deleting it.
    """
    previous = state["bot_data"].get("promo_messages")

    if not isinstance(previous, dict):
        return

    restored = {}

    for key, message_id in previous.items():
        try:
            restored[int(key)] = message_id
        except ValueError:
            continue

    state["bot_data"]["promo_messages"] = restored


class JobRunner:
    def __init__(self, core):
        self.core = core
        self.config = core.config
        self.path = state_path_for(core.config.DB_PATH)
        self.state = self._load()
        self.context = JobContext(None, self.state["bot_data"])
        self._lock = asyncio.Lock()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as handle:
                data = json.load(handle)

        except (FileNotFoundError, ValueError):
            return {"last": {}, "bot_data": {}}

        if not isinstance(data, dict):
            return {"last": {}, "bot_data": {}}

        data.setdefault("last", {})
        data.setdefault("bot_data", {})
        restore_chat_ids(data)
        return data

    def _save(self):
        temp = f"{self.path}.tmp"

        try:
            self.state["bot_data"] = self.context.bot_data

            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(self.state, handle)

            os.replace(temp, self.path)

        except OSError as exc:
            logging.warning("Could not save job state: %s", exc)

    def _jobs(self):
        return (
            ("cleanup", self.core.auto_delete.cleanup, CLEANUP_INTERVAL),
            ("sheet_sync", self.core.sheet_sync.sync_movie_names, self.config.SHEET_SYNC_INTERVAL),
            ("promotion", self.core.promotion.send_promotion, self.config.PROMO_INTERVAL),
        )

    def due_jobs(self):
        now = time.time()
        return [
            name
            for name, _, interval in self._jobs()
            if now - self.state["last"].get(name, 0) >= interval
        ]

    async def run_due(self):
        """Run every job that has reached its interval.

        Returns the names of the jobs that ran. Calls serialize on the lock,
        so a second tick right after the first finds nothing due.
        """
        async with self._lock:
            if self.context.bot is None:
                self.context.bot = self.core.application.bot

            now = time.time()
            ran = []

            for name, method, interval in self._jobs():
                if now - self.state["last"].get(name, 0) < interval:
                    continue

                try:
                    await method(self.context)

                except Exception as exc:
                    # A failing job must not stop the other two.
                    logging.exception("%s failed: %s", name, exc)

                # Recorded even on failure, so a permanently broken job does
                # not spin through every request.
                self.state["last"][name] = time.time()
                ran.append(name)

            if ran:
                self._save()

            return ran
