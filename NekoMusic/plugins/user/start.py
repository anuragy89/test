"""NekoMusic — /start  /help  /lang  callbacks"""

import os
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

from NekoMusic.client import bot
from NekoMusic.database.db import db
from NekoMusic.locales import get_string
from NekoMusic.utils.keyboards import start_kb, help_kb, lang_kb
from config import E, pe, BOT_NAME, BOT_VERSION
from logger import get_logger

log = get_logger("start")

_BANNER = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "banner.jpg")

LANG_NAMES = {"en":"🇬🇧 English","hi":"🇮🇳 Hindi","es":"🇪🇸 Español","ar":"🇸🇦 Arabic","ru":"🇷🇺 Russian"}


@bot.on_message(filters.command("start") & filters.private)
async def cmd_start_private(_, msg: Message):
    user = msg.from_user
    await db.add_user(user.id, user.first_name, user.username or "")
    lang = await db.get_user_lang(user.id)

    caption = (
        f"{pe(E.WAVE, E.WAVE_ID)} <b>Hey {user.mention}!</b>\n\n"
        f"{pe(E.NEKO, E.NEKO_ID)} <b>This is {BOT_NAME}</b> — a fast &amp; powerful "
        f"Telegram Voice Chat Music Bot!\n\n"
        f"{E.ARROW} Stream any song in voice chats\n"
        f"{E.ARROW} YouTube search or paste a link\n"
        f"{E.ARROW} Queue, controls &amp; auto-next\n\n"
        f"{pe(E.SPARKLE, E.SPARKLE_ID)} <i>Add me to your group, start voice chat, "
        f"then use</i> <code>/play</code>!\n\n"
        f"{pe(E.DIAMOND, E.DIAMOND_ID)} <b>Powered by {BOT_NAME} v{BOT_VERSION}</b>"
    )
    if os.path.exists(_BANNER):
        await msg.reply_photo(photo=_BANNER, caption=caption, reply_markup=start_kb())
    else:
        await msg.reply_text(caption, reply_markup=start_kb())


@bot.on_message(filters.command("start") & filters.group)
async def cmd_start_group(_, msg: Message):
    await db.add_group(msg.chat.id, msg.chat.title or "")
    await msg.reply_text(
        f"{pe(E.NEKO, E.NEKO_ID)} <b>{BOT_NAME} is here!</b> "
        f"Use /play to stream music in voice chat.",
        reply_markup=start_kb(),
    )


@bot.on_message(filters.command("help"))
async def cmd_help(_, msg: Message):
    await msg.reply_text(
        f"{pe(E.CROWN, E.CROWN_ID)} <b>{BOT_NAME} — Commands</b>\n\n"
        f"{pe(E.MUSIC, E.MUSIC_ID)} <b>Music:</b>\n"
        f"  <code>/play [name/url]</code> — Play audio\n"
        f"  <code>/vplay [name/url]</code> — Play video\n"
        f"  <code>/playforce [name/url]</code> — Skip queue &amp; play\n"
        f"  <code>/pause</code> — Pause playback\n"
        f"  <code>/resume</code> — Resume playback\n"
        f"  <code>/skip</code> — Skip to next\n"
        f"  <code>/end</code> — Stop &amp; clear queue\n"
        f"  <code>/queue</code> — View queue\n\n"
        f"{pe(E.PING, E.PING_ID)} <b>Utility:</b>\n"
        f"  <code>/ping</code> — Latency\n"
        f"  <code>/lang</code> — Change language\n\n"
        f"{pe(E.CROWN, E.CROWN_ID)} <b>Owner:</b>\n"
        f"  <code>/stats</code>  <code>/broadcast</code>  <code>/restart</code>",
        reply_markup=help_kb(),
    )


@bot.on_message(filters.command("lang"))
async def cmd_lang(_, msg: Message):
    chat = msg.chat
    is_grp = chat.type.value in ("group", "supergroup")
    lang = await db.get_group_lang(chat.id) if is_grp else await db.get_user_lang(msg.from_user.id)
    name = LANG_NAMES.get(lang, lang.upper())
    await msg.reply_text(
        f"{pe(E.GLOBE, E.GLOBE_ID)} <b>Language Settings</b>\n\nCurrent: <b>{name}</b>\nChoose new:",
        reply_markup=lang_kb(),
    )


# ── Callbacks ─────────────────────────────────────────────────────────────────
@bot.on_callback_query(filters.regex("^start_back$"))
async def cb_start(_, cq: CallbackQuery):
    await cq.message.edit_reply_markup(start_kb())


@bot.on_callback_query(filters.regex("^help_main$"))
async def cb_help(_, cq: CallbackQuery):
    await cq.message.edit_reply_markup(help_kb())


@bot.on_callback_query(filters.regex("^help_lang$"))
async def cb_lang_menu(_, cq: CallbackQuery):
    await cq.message.edit_reply_markup(lang_kb())


@bot.on_callback_query(filters.regex(r"^setlang_(.+)$"))
async def cb_setlang(_, cq: CallbackQuery):
    code  = cq.matches[0].group(1)
    chat  = cq.message.chat
    is_grp = chat.type.value in ("group", "supergroup")
    if is_grp:
        await db.set_group_lang(chat.id, code)
    else:
        await db.set_user_lang(cq.from_user.id, code)
    await cq.answer(f"✅ Language set to {LANG_NAMES.get(code, code.upper())}", show_alert=True)
    await cq.message.edit_reply_markup(lang_kb())
