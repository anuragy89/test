"""
NekoMusic — Entry Point
IMPORTANT: The pyrogram monkey-patch MUST happen before any pytgcalls import.
py-tgcalls 2.2.11 requires GroupcallForbidden from pyrogram.errors,
which was removed in pyrogram 2.x. We inject it here as a shim.
"""

import asyncio
import glob
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────────────────────────────────
# PATCH: inject GroupcallForbidden into pyrogram.errors BEFORE pytgcalls loads
# This is required because py-tgcalls 2.2.x was built against pyrogram 1.x
# which had this error class. Pyrogram 2.x removed it.
# ─────────────────────────────────────────────────────────────────────────────
try:
    import pyrogram.errors as _pyro_errors
    if not hasattr(_pyro_errors, "GroupcallForbidden"):
        from pyrogram.errors.exceptions import BadRequest as _BR
        class GroupcallForbidden(_BR):
            ID = "GROUPCALL_FORBIDDEN"
            MESSAGE = "Group call forbidden"
        _pyro_errors.GroupcallForbidden = GroupcallForbidden
        import pyrogram.errors.exceptions
        pyrogram.errors.exceptions.GroupcallForbidden = GroupcallForbidden
except Exception as _e:
    print(f"[WARN] pyrogram patch failed: {_e}")
# ─────────────────────────────────────────────────────────────────────────────

from config import (
    API_ID, API_HASH, BOT_TOKEN, STRING_SESSION,
    MONGO_URI, OWNER_ID, CACHE_DIR, BOT_NAME, BOT_VERSION,
)
from logger import LOGGER as log


def _check_env():
    required = {
        "API_ID": API_ID, "API_HASH": API_HASH,
        "BOT_TOKEN": BOT_TOKEN, "STRING_SESSION": STRING_SESSION,
        "MONGO_URI": MONGO_URI, "OWNER_ID": OWNER_ID,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        log.critical("❌ Missing env vars: %s", ", ".join(missing))
        sys.exit(1)


def _load_plugins():
    loaded = fail = 0
    patterns = [
        "NekoMusic/plugins/user/*.py",
        "NekoMusic/plugins/owner/*.py",
    ]
    for pattern in patterns:
        for filepath in sorted(glob.glob(pattern)):
            filename = os.path.basename(filepath)
            if filename.startswith("_"):
                continue
            module = filepath.replace(os.sep, ".")[:-3]
            try:
                importlib.import_module(module)
                log.info("  ✅ Plugin loaded: %s", module)
                loaded += 1
            except Exception as exc:
                log.error("  ❌ Plugin failed [%s]: %s", module, exc)
                fail += 1
    log.info("📦 Plugins: %d loaded, %d failed", loaded, fail)
    if fail > 0 and loaded == 0:
        log.critical("All plugins failed to load. Exiting.")
        sys.exit(1)


async def main():
    log.info("═" * 56)
    log.info("  %s  v%s  —  Starting up", BOT_NAME, BOT_VERSION)
    log.info("═" * 56)

    _check_env()
    os.makedirs(CACHE_DIR, exist_ok=True)

    from NekoMusic.database.db import db
    await db.connect()

    _load_plugins()

    from NekoMusic.client import start_clients, stop_clients
    await start_clients()

    log.info("🟢  %s is LIVE!", BOT_NAME)

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        log.info("🔴  Shutdown signal received")
    finally:
        await stop_clients()
        await db.close()
        log.info("👋  %s stopped.", BOT_NAME)


if __name__ == "__main__":
    asyncio.run(main())
