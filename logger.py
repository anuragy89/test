"""NekoMusic — Logger: coloured console + rotating file + optional Telegram forwarding"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path

import colorlog

from config import LOG_LEVEL, LOG_GROUP_ID, BOT_NAME

Path("logs").mkdir(exist_ok=True)

_CON_FMT  = "%(log_color)s[%(asctime)s] %(levelname)-8s%(reset)s %(cyan)s%(name)-18s%(reset)s %(white)s%(message)s%(reset)s"
_FILE_FMT = "[%(asctime)s] %(levelname)-8s %(name)-18s  %(message)s"
_DATE     = "%Y-%m-%d %H:%M:%S"
_COLORS   = {"DEBUG": "cyan", "INFO": "bold_green", "WARNING": "bold_yellow",
             "ERROR": "bold_red", "CRITICAL": "bold_red,bg_white"}


def _build():
    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    ch = colorlog.StreamHandler(sys.stdout)
    ch.setFormatter(colorlog.ColoredFormatter(_CON_FMT, datefmt=_DATE, log_colors=_COLORS, reset=True))
    root.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(
        f"logs/{BOT_NAME.lower()}.log", maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE))
    root.addHandler(fh)

    for lib in ("pyrogram", "pytgcalls", "motor", "asyncio", "httpx", "urllib3", "aiohttp"):
        logging.getLogger(lib).setLevel(logging.WARNING)
    return root


LOGGER = _build()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class _TgHandler(logging.Handler):
    def __init__(self, client):
        super().__init__(level=logging.ERROR)
        self._bot = client

    def emit(self, record):
        try:
            text = (f"<b>🚨 [{record.levelname}]</b> <code>{record.name}</code>\n"
                    f"<pre>{self.format(record)[:3500]}</pre>\n"
                    f"<i>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</i>")
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._bot.send_message(LOG_GROUP_ID, text, parse_mode="html"))
        except Exception:
            self.handleError(record)


def attach_tg_handler(client):
    if not LOG_GROUP_ID:
        return
    h = _TgHandler(client)
    h.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE))
    logging.getLogger().addHandler(h)
    LOGGER.info("📋 Telegram log handler → chat_id=%s", LOG_GROUP_ID)
