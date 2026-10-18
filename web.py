"""Webhook entry point for a WSGI host (PythonAnywhere free tier).

PythonAnywhere free cannot keep a process listening on a port and gives free
accounts no scheduled tasks, so the bot cannot poll and cannot cron. Instead
Telegram pushes each update to WEBHOOK_PATH here, and the timed jobs run when
something already wakes the app: right after an update, and on GET /tick from
the keep-alive workflow.

For a host that does keep one process alive (Railway, Termux), use bot.py.
"""

import asyncio
import concurrent.futures
import hmac
import logging
import threading
import time

from flask import Flask, jsonify, request
from telegram import Update

from config import Config
from core import CinemaKingdomCore
from services.jobs import JobRunner
from services.logger import setup_logger

setup_logger()

CONFIG = Config()

# Telegram waits for a 2xx answer; handlers normally finish in a couple of
# seconds, so 25s leaves headroom before Telegram retries the delivery.
PROCESS_TIMEOUT = 25

# Startup makes one getMe call, but a slow reload should not hang a request.
STARTUP_WAIT = 30


class _WebhookRunner:
    """Owns one asyncio loop for the whole web worker.

    The Telegram Application must live on a single loop, but WSGI calls the
    Flask view from worker threads, so the loop runs in its own thread and
    updates are handed to it with run_coroutine_threadsafe.
    """

    def __init__(self):
        self.loop = None
        self.core = None
        self.jobs = None
        self.started_at = None
        self.updates_handled = 0
        self.ticks = 0
        self.last_jobs_ran = []
        self.boot_error = None
        self._lock = threading.Lock()
        self._ready = threading.Event()

    @property
    def ready(self):
        return self.core is not None

    def start(self):
        with self._lock:
            self._ready.clear()

            if self.loop is None:
                threading.Thread(
                    target=self._thread_main,
                    name="telegram-loop",
                    daemon=True,
                ).start()
            elif self.core is None:
                # Retry after a failed startup, for example when Telegram was
                # unreachable while the web worker reloaded.
                asyncio.run_coroutine_threadsafe(
                    self._boot(),
                    self.loop,
                )

            self._ready.wait(STARTUP_WAIT)

    def _thread_main(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop

        loop.run_until_complete(self._boot())
        loop.run_forever()

    async def _boot(self):
        try:
            core = CinemaKingdomCore()
            await core.application.initialize()
            await core.application.start()

            # PTB only runs post_init from run_polling/run_webhook, so this
            # startup path applies the / command menus and group rules by hand.
            await core.prepare_bot(core.application)

            self.core = core
            self.jobs = JobRunner(core)
            self.boot_error = None
            self.started_at = time.time()

            logging.info(
                "Cinema Kingdom webhook ready | %s",
                CONFIG.WEBHOOK_URL or "WEBHOOK_BASE_URL not set"
            )

        except Exception as exc:
            self.boot_error = repr(exc)
            logging.exception("Webhook startup failed")

        finally:
            self._ready.set()

    def process(self, payload):
        future = asyncio.run_coroutine_threadsafe(
            self._process(payload),
            self.loop,
        )
        return future.result(timeout=PROCESS_TIMEOUT)

    async def _process(self, payload):
        update = Update.de_json(payload, self.core.application.bot)
        await self.core.application.process_update(update)
        self.updates_handled += 1

        # Traffic is a free chance to run the timed jobs, so expired messages
        # get deleted while the group is busy instead of waiting for a tick.
        if self.jobs:
            self.loop.create_task(self.jobs.run_due())

    def run_jobs(self):
        future = asyncio.run_coroutine_threadsafe(
            self._run_jobs(),
            self.loop,
        )
        return future.result(timeout=PROCESS_TIMEOUT)

    async def _run_jobs(self):
        ran = await self.jobs.run_due()

        self.ticks += 1
        self.last_jobs_ran = ran

        return ran


runner = _WebhookRunner()

app = Flask(__name__)


if not CONFIG.WEBHOOK_SECRET_TOKEN:
    logging.warning(
        "WEBHOOK_SECRET_TOKEN is empty - create one with: python setup_hook.py --make-secret"
    )


@app.route("/healthz")
def healthz():
    return jsonify(
        {
            "ready": runner.ready,
            "uptime_seconds": (
                round(time.time() - runner.started_at, 1)
                if runner.started_at
                else None
            ),
            "updates_handled": runner.updates_handled,
            "ticks": runner.ticks,
            "last_jobs_ran": runner.last_jobs_ran,
            "jobs_due": runner.jobs.due_jobs() if runner.jobs else None,
            "boot_error": runner.boot_error,
            "webhook_url": CONFIG.WEBHOOK_URL or None,
            "secret_configured": bool(CONFIG.WEBHOOK_SECRET_TOKEN),
        }
    )


@app.route("/tick")
def tick():
    """Run the timed jobs on demand.

    The chat goes quiet at night, and without a scheduled task nothing would
    trigger auto-delete or the promotion message then.
    """
    if not CONFIG.WEBHOOK_SECRET_TOKEN:
        return "WEBHOOK_SECRET_TOKEN missing", 500

    sent_token = request.headers.get("X-Keep-Alive-Token", "")

    if not hmac.compare_digest(sent_token, CONFIG.WEBHOOK_SECRET_TOKEN):
        logging.warning("Rejected tick call with wrong token")
        return "forbidden", 403

    if not runner.ready:
        runner.start()
        if not runner.ready:
            return "bot starting up", 503

    try:
        ran = runner.run_jobs()

    except concurrent.futures.TimeoutError:
        return jsonify(status="running", jobs_ran=[]), 200

    return jsonify(status="ok", jobs_ran=ran), 200


@app.route(Config.WEBHOOK_PATH, methods=["POST"])
def webhook():
    if not CONFIG.WEBHOOK_SECRET_TOKEN:
        logging.error("WEBHOOK_SECRET_TOKEN is empty, refusing updates")
        return "WEBHOOK_SECRET_TOKEN missing", 500

    sent_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        "",
    )
    if not hmac.compare_digest(sent_secret, CONFIG.WEBHOOK_SECRET_TOKEN):
        logging.warning("Rejected webhook call with wrong secret token")
        return "forbidden", 403

    payload = request.get_json(force=True, silent=True)
    if not isinstance(payload, dict):
        return "bad payload", 400

    if not runner.ready:
        runner.start()
        if not runner.ready:
            logging.error("Webhook not ready: %s", runner.boot_error)
            # 5xx makes Telegram redeliver instead of dropping the update.
            return "bot starting up", 503

    try:
        runner.process(payload)

    except concurrent.futures.TimeoutError:
        logging.warning("Handler exceeded %ss, update left running", PROCESS_TIMEOUT)

    except Exception:
        logging.exception("Webhook processing failed")

    # 200 even on failure: the error handler has already logged it, and
    # Telegram redelivering would repeat the same failure in a loop.
    return "", 200
