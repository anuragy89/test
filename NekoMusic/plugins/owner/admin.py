"""NekoMusic — Owner Commands: /stats /broadcast /restart /ban /unban"""

import asyncio
import os
import time

import psutil
from pyrogram import filters
from pyrogram.types import Message

from NekoMusic.client import bot
from NekoMusic.database.db import db
from config import (
    E, pe, OWNER_ID, SUDO_USERS,
    HEROKU_APP_NAME, HEROKU_API_KEY,
    BOT_VERSION, BOT_NAME,
)
from logger import get_logger

log = get_logger("owner")
_START = time.time()


def _uptime() -> str:
    s = int(time.time() - _START)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def _is_owner(_, __, msg: Message) -> bool:
    uid = msg.from_user.id if msg.from_user else 0
    return uid == OWNER_ID or uid in SUDO_USERS


_owner = filters.create(_is_owner)


@bot.on_message(filters.command("stats") & _owner)
async def cmd_stats(_, msg: Message):
    stats = await db.get_stats()
    ram   = round(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024, 2)
    cpu   = psutil.cpu_percent(interval=0.5)
    await msg.reply_text(
        f"{pe(E.CROWN, E.CROWN_ID)} <b>{BOT_NAME} Statistics</b>\n\n"
        f"{pe(E.USER, E.USER_ID)}  <b>Users :</b>         <code>{stats['total_users']}</code>\n"
        f"{pe(E.GROUP, E.GROUP_ID)} <b>Groups :</b>       <code>{stats['total_groups']}</code>\n"
        f"{pe(E.MUSIC, E.MUSIC_ID)} <b>Songs Played :</b> <code>{stats['songs_played']}</code>\n\n"
        f"{pe(E.LIGHTNING, E.LIGHTNING_ID)} <b>Uptime :</b>  <code>{_uptime()}</code>\n"
        f"{pe(E.STATS, E.STATS_ID)} <b>RAM :</b>          <code>{ram} MB</code>\n"
        f"⚙️  <b>CPU :</b>          <code>{cpu}%</code>\n"
        f"{pe(E.ROBOT, E.ROBOT_ID)} <b>Version :</b>     <code>v{BOT_VERSION}</code>"
    )


@bot.on_message(filters.command("broadcast") & _owner)
async def cmd_broadcast(_, msg: Message):
    args = msg.command[1:]
    mode = "both"
    if args and args[0] in ("-user", "-group"):
        mode = args[0][1:]
        args = args[1:]

    if msg.reply_to_message:
        bcast, forward = msg.reply_to_message, True
    elif args:
        bcast, forward = " ".join(args), False
    else:
        return await msg.reply_text(
            f"{E.WARNING} <b>Usage:</b>\n"
            f"<code>/broadcast -user text</code>\n"
            f"<code>/broadcast -group text</code>\n"
            f"<i>Or reply to a message.</i>"
        )

    targets = []
    if mode in ("user", "both"):
        targets += [("u", u["user_id"]) for u in await db.get_all_users()]
    if mode in ("group", "both"):
        targets += [("g", g["chat_id"]) for g in await db.get_all_groups()]

    status = await msg.reply_text(
        f"{pe(E.BROADCAST, E.BROADCAST_ID)} Broadcasting to <b>{len(targets)}</b> chats..."
    )
    ok = fail = 0
    for i, (_, cid) in enumerate(targets):
        try:
            if forward:
                await bcast.forward(cid)
            else:
                await bot.send_message(cid, bcast)
            ok += 1
        except Exception as e:
            log.warning("Broadcast fail %s: %s", cid, e)
            fail += 1
        if (i + 1) % 25 == 0:
            await asyncio.sleep(1)

    await status.edit_text(
        f"{pe(E.SUCCESS, E.SUCCESS_ID)} <b>Broadcast Done!</b>\n\n"
        f"✅ Sent: <code>{ok}</code>\n"
        f"❌ Failed: <code>{fail}</code>"
    )


@bot.on_message(filters.command("restart") & _owner)
async def cmd_restart(_, msg: Message):
    if not HEROKU_APP_NAME or not HEROKU_API_KEY:
        return await msg.reply_text(
            f"{E.WARNING} <code>HEROKU_APP_NAME</code> or <code>HEROKU_API_KEY</code> not set."
        )
    await msg.reply_text(
        f"{pe(E.RESTART, E.RESTART_ID)} <b>Restarting {BOT_NAME}...</b>\n"
        f"<i>Back in a moment! 🐱</i>"
    )
    try:
        import heroku3
        heroku3.from_key(HEROKU_API_KEY).app(HEROKU_APP_NAME).restart()
        log.info("Heroku restart issued: %s", HEROKU_APP_NAME)
    except Exception as e:
        await msg.reply_text(f"{E.ERROR} Restart failed: <code>{e}</code>")


@bot.on_message(filters.command("ban") & _owner)
async def cmd_ban(_, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply_text(f"{E.ERROR} Provide a user ID.")
    try:
        uid = int(msg.command[1])
        await db.ban_user(uid)
        await msg.reply_text(f"{pe(E.SUCCESS, E.SUCCESS_ID)} User <code>{uid}</code> banned.")
    except ValueError:
        await msg.reply_text(f"{E.ERROR} Invalid user ID.")


@bot.on_message(filters.command("unban") & _owner)
async def cmd_unban(_, msg: Message):
    if len(msg.command) < 2:
        return await msg.reply_text(f"{E.ERROR} Provide a user ID.")
    try:
        uid = int(msg.command[1])
        await db.unban_user(uid)
        await msg.reply_text(f"{pe(E.SUCCESS, E.SUCCESS_ID)} User <code>{uid}</code> unbanned.")
    except ValueError:
        await msg.reply_text(f"{E.ERROR} Invalid user ID.")
