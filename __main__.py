"""
NekoMusic — Entry Point
Run: python -m NekoMusic  OR  python __main__.py
"""

import asyncio
import glob
import importlib
import os
import sys

# Ensure project root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    API_ID, API_HASH, BOT_TOKEN, STRING_SESSION,
    MONGO_URI, OWNER_ID, CACHE_DIR, BOT_NAME, BOT_VERSION,
)
from logger import LOGGER as log


def _check_env():
    required = {
        "API_ID": API_ID,
        "API_HASH": API_HASH,
        "BOT_TOKEN": BOT_TOKEN,
        "STRING_SESSION": STRING_SESSION,
        "MONGO_URI": MONGO_URI,
        "OWNER_ID": OWNER_ID,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        log.critical("❌ Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)


def _load_plugins():
    """Auto-import every plugin module from plugins/user and plugins/owner."""
    loaded, failed = 0, 0
    patterns = [
        "NekoMusic/plugins/user/*.py",
        "NekoMusic/plugins/owner/*.py",
    ]
    for pattern in patterns:
        for filepath in sorted(glob.glob(pattern)):
            filename = os.path.basename(filepath)
            if filename.startswith("_"):
                continue
            # Convert path to dotted module name
            module = filepath.replace(os.sep, ".")[:-3]
            try:
                importlib.import_module(module)
                log.info("  ✅ Plugin loaded: %s", module)
                loaded += 1
            except Exception as exc:
                log.error("  ❌ Plugin failed [%s]: %s", module, exc)
                failed += 1
    log.info("📦 Plugins: %d loaded, %d failed", loaded, failed)


async def main():
    log.info("═" * 56)
    log.info("  %s  v%s  —  Starting up", BOT_NAME, BOT_VERSION)
    log.info("═" * 56)

    _check_env()
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Connect MongoDB
    from NekoMusic.database.db import db
    await db.connect()

    # Load all plugins BEFORE starting clients
    # (plugins register handlers at import time)
    _load_plugins()

    # Start Pyrogram bot + assistant + PyTgCalls
    from NekoMusic.client import start_clients, stop_clients
    await start_clients()

    log.info("🟢  %s is LIVE — Press Ctrl+C to stop", BOT_NAME)

    try:
        await asyncio.Event().wait()          # run forever
    except (KeyboardInterrupt, SystemExit):
        log.info("🔴  Shutdown signal received")
    finally:
        await stop_clients()
        await db.close()
        log.info("👋  %s stopped cleanly", BOT_NAME)


if __name__ == "__main__":
    asyncio.run(main())
