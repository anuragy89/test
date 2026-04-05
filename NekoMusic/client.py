"""NekoMusic — Pyrogram bot + assistant + PyTgCalls (GitHub master / NTgCalls)"""

import uvloop
uvloop.install()

from pyrogram import Client
from pytgcalls import PyTgCalls

from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, BOT_NAME, BOT_VERSION
from logger import get_logger, attach_tg_handler

log = get_logger("client")

bot = Client(
    "NekoMusicBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=30,
    max_concurrent_transmissions=10,
)

assistant = Client(
    "NekoMusicAssistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
    sleep_threshold=30,
)

# PyTgCalls wraps the assistant client
call = PyTgCalls(assistant)


async def start_clients():
    log.info("🚀 Starting %s v%s", BOT_NAME, BOT_VERSION)
    await bot.start()
    await assistant.start()
    await call.start()
    attach_tg_handler(bot)
    me   = await bot.get_me()
    asst = await assistant.get_me()
    log.info("✅ Bot       → @%s", me.username)
    log.info("✅ Assistant → @%s", asst.username)


async def stop_clients():
    try:
        await call.stop()
    except Exception:
        pass
    try:
        await assistant.stop()
    except Exception:
        pass
    try:
        await bot.stop()
    except Exception:
        pass
    log.info("🛑 Stopped cleanly.")
