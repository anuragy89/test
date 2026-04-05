"""
╔══════════════════════════════════════════════════════════╗
║           NekoMusic Bot  ·  v2.0  ·  Configuration       ║
╚══════════════════════════════════════════════════════════╝
"""

import os
from typing import List


# ════════════════════════════════════════════════════════════
#  CORE CREDENTIALS
# ════════════════════════════════════════════════════════════
API_ID: int         = int(os.environ.get("API_ID", 0))
API_HASH: str       = os.environ.get("API_HASH", "")
BOT_TOKEN: str      = os.environ.get("BOT_TOKEN", "")
STRING_SESSION: str = os.environ.get("STRING_SESSION", "")   # assistant userbot


# ════════════════════════════════════════════════════════════
#  MUSIC API  (music.xbitcode.com)
# ════════════════════════════════════════════════════════════
MUSIC_API_BASE: str  = os.environ.get("MUSIC_API_BASE",  "https://music.xbitcode.com")
# Optional: YouTube Data API v3 key (for richer search results)
YT_API_KEY: str      = os.environ.get("YT_API_KEY",      "")
# Optional: HTTP/HTTPS proxy URL for the music API requests
YT_PROXY_URL: str    = os.environ.get("YT_PROXY_URL",    "")


# ════════════════════════════════════════════════════════════
#  MONGODB
# ════════════════════════════════════════════════════════════
MONGO_URI: str     = os.environ.get("MONGO_URI", "")
DATABASE_NAME: str = os.environ.get("DATABASE_NAME", "NekoMusicDB")


# ════════════════════════════════════════════════════════════
#  OWNER / ADMINS
# ════════════════════════════════════════════════════════════
OWNER_ID: int           = int(os.environ.get("OWNER_ID", 0))
SUDO_USERS: List[int]   = list(
    map(int, filter(None, os.environ.get("SUDO_USERS", "").split()))
)


# ════════════════════════════════════════════════════════════
#  LINKS
# ════════════════════════════════════════════════════════════
SUPPORT_CHAT: str    = os.environ.get("SUPPORT_CHAT",    "https://t.me/YourSupport")
UPDATES_CHANNEL: str = os.environ.get("UPDATES_CHANNEL", "https://t.me/YourChannel")
SOURCE_CODE: str     = os.environ.get("SOURCE_CODE",     "https://github.com/YourRepo")
BOT_USERNAME: str    = os.environ.get("BOT_USERNAME",    "YourMusicBot")


# ════════════════════════════════════════════════════════════
#  HEROKU  (for /restart)
# ════════════════════════════════════════════════════════════
HEROKU_APP_NAME: str = os.environ.get("HEROKU_APP_NAME", "")
HEROKU_API_KEY: str  = os.environ.get("HEROKU_API_KEY",  "")


# ════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════
LOG_GROUP_ID: int = int(os.environ.get("LOG_GROUP_ID", 0))
LOG_LEVEL: str    = os.environ.get("LOG_LEVEL", "INFO")


# ════════════════════════════════════════════════════════════
#  MUSIC SETTINGS
# ════════════════════════════════════════════════════════════
MAX_DURATION: int  = int(os.environ.get("MAX_DURATION", 180))   # minutes
QUEUE_LIMIT: int   = int(os.environ.get("QUEUE_LIMIT",  20))
CACHE_DIR: str     = os.environ.get("CACHE_DIR", "/tmp/neko_cache")


# ════════════════════════════════════════════════════════════
#  LANGUAGE
# ════════════════════════════════════════════════════════════
DEFAULT_LANGUAGE: str = os.environ.get("DEFAULT_LANGUAGE", "en")


# ════════════════════════════════════════════════════════════
#  BOT META
# ════════════════════════════════════════════════════════════
BOT_VERSION: str = "2.0.0"
BOT_NAME: str    = "NekoMusic"


# ════════════════════════════════════════════════════════════
#  EMOJI TABLE
#  ┌─────────────────────────────────────────────────────────┐
#  │  Each entry:  UNICODE_FALLBACK  +  PREMIUM_EMOJI_ID     │
#  │  Get premium IDs from @stickers bot (forward animated   │
#  │  emoji → inspect document_id).  Leave ID = "" to use   │
#  │  the plain Unicode fallback automatically.              │
#  └─────────────────────────────────────────────────────────┘
# ════════════════════════════════════════════════════════════
class E:
    # ── Playback ──────────────────────────────────────────────
    PLAY       = "▶️"  ;  PLAY_ID       = os.environ.get("EMOJI_PLAY_ID",       "")
    PAUSE      = "⏸"  ;  PAUSE_ID      = os.environ.get("EMOJI_PAUSE_ID",      "")
    STOP       = "⏹"  ;  STOP_ID       = os.environ.get("EMOJI_STOP_ID",       "")
    SKIP       = "⏭"  ;  SKIP_ID       = os.environ.get("EMOJI_SKIP_ID",       "")
    PREV       = "⏮"  ;  PREV_ID       = os.environ.get("EMOJI_PREV_ID",       "")
    SHUFFLE    = "🔀"  ;  SHUFFLE_ID    = os.environ.get("EMOJI_SHUFFLE_ID",    "")
    REPEAT     = "🔁"  ;  REPEAT_ID     = os.environ.get("EMOJI_REPEAT_ID",     "")
    VOLUME     = "🔊"  ;  VOLUME_ID     = os.environ.get("EMOJI_VOLUME_ID",     "")
    MUTE       = "🔇"  ;  MUTE_ID       = os.environ.get("EMOJI_MUTE_ID",       "")

    # ── Music / Media ─────────────────────────────────────────
    MUSIC      = "🎵"  ;  MUSIC_ID      = os.environ.get("EMOJI_MUSIC_ID",      "")
    HEADPHONE  = "🎧"  ;  HEADPHONE_ID  = os.environ.get("EMOJI_HEADPHONE_ID",  "")
    MIC        = "🎤"  ;  MIC_ID        = os.environ.get("EMOJI_MIC_ID",        "")
    ALBUM      = "💿"  ;  ALBUM_ID      = os.environ.get("EMOJI_ALBUM_ID",      "")
    ARTIST     = "🎨"  ;  ARTIST_ID     = os.environ.get("EMOJI_ARTIST_ID",     "")
    NOTE       = "🎶"  ;  NOTE_ID       = os.environ.get("EMOJI_NOTE_ID",       "")
    RADIO      = "📻"  ;  RADIO_ID      = os.environ.get("EMOJI_RADIO_ID",      "")

    # ── Status ────────────────────────────────────────────────
    SUCCESS    = "✅"  ;  SUCCESS_ID    = os.environ.get("EMOJI_SUCCESS_ID",    "")
    ERROR      = "❌"  ;  ERROR_ID      = os.environ.get("EMOJI_ERROR_ID",      "")
    WARNING    = "⚠️"  ;  WARNING_ID    = os.environ.get("EMOJI_WARNING_ID",    "")
    INFO       = "ℹ️"  ;  INFO_ID       = os.environ.get("EMOJI_INFO_ID",       "")
    LOADING    = "⏳"  ;  LOADING_ID    = os.environ.get("EMOJI_LOADING_ID",    "")

    # ── Social / UI ───────────────────────────────────────────
    CROWN      = "👑"  ;  CROWN_ID      = os.environ.get("EMOJI_CROWN_ID",      "")
    DIAMOND    = "💎"  ;  DIAMOND_ID    = os.environ.get("EMOJI_DIAMOND_ID",    "")
    FIRE       = "🔥"  ;  FIRE_ID       = os.environ.get("EMOJI_FIRE_ID",       "")
    STAR       = "⭐"  ;  STAR_ID       = os.environ.get("EMOJI_STAR_ID",       "")
    SPARKLE    = "✨"  ;  SPARKLE_ID    = os.environ.get("EMOJI_SPARKLE_ID",    "")
    HEART      = "❤️"  ;  HEART_ID      = os.environ.get("EMOJI_HEART_ID",      "")
    NEKO       = "🐱"  ;  NEKO_ID       = os.environ.get("EMOJI_NEKO_ID",       "")
    WAVE       = "👋"  ;  WAVE_ID       = os.environ.get("EMOJI_WAVE_ID",       "")
    ROBOT      = "🤖"  ;  ROBOT_ID      = os.environ.get("EMOJI_ROBOT_ID",      "")
    LIGHTNING  = "⚡"  ;  LIGHTNING_ID  = os.environ.get("EMOJI_LIGHTNING_ID",  "")
    GLOBE      = "🌐"  ;  GLOBE_ID      = os.environ.get("EMOJI_GLOBE_ID",      "")
    BELL       = "🔔"  ;  BELL_ID       = os.environ.get("EMOJI_BELL_ID",       "")
    BROADCAST  = "📢"  ;  BROADCAST_ID  = os.environ.get("EMOJI_BROADCAST_ID",  "")
    SPEAKER    = "📣"  ;  SPEAKER_ID    = os.environ.get("EMOJI_SPEAKER_ID",    "")
    LINK       = "🔗"  ;  LINK_ID       = os.environ.get("EMOJI_LINK_ID",       "")

    # ── Data / System ─────────────────────────────────────────
    STATS      = "📊"  ;  STATS_ID      = os.environ.get("EMOJI_STATS_ID",      "")
    CHART      = "📈"  ;  CHART_ID      = os.environ.get("EMOJI_CHART_ID",      "")
    QUEUE      = "📋"  ;  QUEUE_ID      = os.environ.get("EMOJI_QUEUE_ID",      "")
    SEARCH     = "🔍"  ;  SEARCH_ID     = os.environ.get("EMOJI_SEARCH_ID",     "")
    DOWNLOAD   = "⬇️"  ;  DOWNLOAD_ID   = os.environ.get("EMOJI_DOWNLOAD_ID",   "")
    CLOCK      = "🕐"  ;  CLOCK_ID      = os.environ.get("EMOJI_CLOCK_ID",      "")
    RESTART    = "🔄"  ;  RESTART_ID    = os.environ.get("EMOJI_RESTART_ID",    "")
    PING       = "🏓"  ;  PING_ID       = os.environ.get("EMOJI_PING_ID",       "")
    USER       = "👤"  ;  USER_ID       = os.environ.get("EMOJI_USER_ID",       "")
    GROUP      = "👥"  ;  GROUP_ID      = os.environ.get("EMOJI_GROUP_ID",      "")
    GEAR       = "⚙️"  ;  GEAR_ID       = os.environ.get("EMOJI_GEAR_ID",       "")

    # ── Decorative ────────────────────────────────────────────
    ARROW      = "➤"
    BULLET     = "»"
    DOT        = "•"
    LINE       = "─"


def pe(emoji: str, doc_id: str) -> str:
    """
    Return a <tg-emoji> tag if doc_id is set, else plain emoji.
    Usage: pe(E.MUSIC, E.MUSIC_ID)
    Requires HTML parse mode + bot owner with Telegram Premium.
    """
    if doc_id:
        return f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>'
    return emoji
