"""
NekoMusic — Keyboard Builder
Now-playing card + per-queue-item card buttons (matching screenshot)
Bot API 9.4 style= for coloured buttons
"""

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import E, pe, SUPPORT_CHAT, UPDATES_CHANNEL, SOURCE_CODE, BOT_USERNAME


def _b(text, cb=None, url=None, style=None) -> InlineKeyboardButton:
    kw = {"text": text}
    if cb:    kw["callback_data"] = cb
    if url:   kw["url"]           = url
    if style: kw["style"]         = style
    return InlineKeyboardButton(**kw)


# ── Start keyboard ─────────────────────────────────────────────────────────────
def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [_b(f"{pe(E.MUSIC, E.MUSIC_ID)} Help Commands", cb="help_main")],
        [_b(f"{pe(E.GROUP, E.GROUP_ID)} Add Me To Group",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true", style="default")],
        [
            _b(f"{pe(E.BELL, E.BELL_ID)} Updates",   url=UPDATES_CHANNEL),
            _b(f"{pe(E.HEART, E.HEART_ID)} Support",  url=SUPPORT_CHAT),
        ],
        [_b(f"{pe(E.LINK, E.LINK_ID)} Source Code",   url=SOURCE_CODE)],
    ])


# ── Help keyboard ──────────────────────────────────────────────────────────────
def help_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _b(f"{pe(E.PLAY, E.PLAY_ID)} Music Cmds",   cb="help_music", style="default"),
            _b(f"{pe(E.CROWN, E.CROWN_ID)} Owner Cmds", cb="help_owner"),
        ],
        [
            _b(f"{pe(E.GLOBE, E.GLOBE_ID)} Language",   cb="help_lang"),
            _b(f"{pe(E.PING, E.PING_ID)} Ping",          cb="help_misc"),
        ],
        [_b(f"{E.ARROW} Back", cb="start_back")],
    ])


# ── NOW PLAYING card keyboard ──────────────────────────────────────────────────
# Matches the screenshot: ⏸  ADD IT  ⏭  (with colour on main actions)
def now_playing_kb(chat_id: int, paused: bool = False, loop: bool = False) -> InlineKeyboardMarkup:
    play_pause_btn = (
        _b(f"{pe(E.PLAY,  E.PLAY_ID)}",  cb=f"vc_resume_{chat_id}", style="default")
        if paused else
        _b(f"{pe(E.PAUSE, E.PAUSE_ID)}", cb=f"vc_pause_{chat_id}",  style="default")
    )
    loop_text = f"{pe(E.REPEAT, E.REPEAT_ID)} {'ON ✅' if loop else 'OFF'}"
    return InlineKeyboardMarkup([
        [
            play_pause_btn,
            _b(f"{pe(E.STOP, E.STOP_ID)}",       cb=f"vc_end_{chat_id}"),
            _b(f"{pe(E.SKIP, E.SKIP_ID)}",        cb=f"vc_skip_{chat_id}", style="default"),
            _b(f"{pe(E.SHUFFLE, E.SHUFFLE_ID)}",  cb=f"vc_shuf_{chat_id}"),
            _b(loop_text,                          cb=f"vc_loop_{chat_id}"),
        ],
        [
            _b(f"{pe(E.GROUP, E.GROUP_ID)} Add Me",
               url=f"https://t.me/{BOT_USERNAME}?startgroup=true"),
        ],
    ])


# ── QUEUE CARD keyboard ────────────────────────────────────────────────────────
# Each queued song gets its own card with: ▶  ⏸  ⏭  ☐
# Matches exactly what's in the screenshot
def queue_card_kb(chat_id: int, pos: int) -> InlineKeyboardMarkup:
    """
    pos = queue position (1-based).
    Buttons: Play-now | Pause | Skip-to | Remove
    """
    return InlineKeyboardMarkup([
        [
            _b(f"{pe(E.PLAY,  E.PLAY_ID)}",  cb=f"q_playnow_{chat_id}_{pos}", style="default"),
            _b(f"{pe(E.PAUSE, E.PAUSE_ID)}", cb=f"vc_pause_{chat_id}"),
            _b(f"{pe(E.SKIP,  E.SKIP_ID)}",  cb=f"q_skipto_{chat_id}_{pos}"),
            _b("☐",                           cb=f"q_remove_{chat_id}_{pos}"),
        ],
    ])


# ── Language keyboard ──────────────────────────────────────────────────────────
def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _b("🇬🇧 English",  cb="setlang_en", style="default"),
            _b("🇮🇳 हिन्दी",  cb="setlang_hi"),
        ],
        [
            _b("🇪🇸 Español",  cb="setlang_es"),
            _b("🇸🇦 العربية", cb="setlang_ar"),
        ],
        [_b("🇷🇺 Русский",     cb="setlang_ru")],
        [_b(f"{E.ARROW} Back",  cb="help_main")],
    ])
