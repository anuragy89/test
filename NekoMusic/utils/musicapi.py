"""
NekoMusic — Music Resolver
Step 1: yt-search-py  → search YouTube, get video_id + title + thumb + duration
Step 2: music.xbitcode.com  → get streamable audio/video URL from video_id

This two-step approach gives us:
  • Rich metadata & high-res thumbnails from YouTube
  • Fast, reliable stream URLs from the xbitcode API
"""

import asyncio
import re
from typing import Dict, Optional

import aiohttp
from youtubesearchpython import VideosSearch   # yt-search-py

from config import MUSIC_API_BASE, YT_PROXY_URL, MAX_DURATION
from logger import get_logger

log = get_logger("musicapi")

_TIMEOUT = aiohttp.ClientTimeout(total=15)
_YT_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})"
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def is_url(text: str) -> bool:
    return text.strip().startswith(("http://", "https://"))


def extract_video_id(url: str) -> Optional[str]:
    m = _YT_URL_RE.search(url)
    return m.group(1) if m else None


def _fmt_dur(secs: int) -> str:
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _parse_dur(dur_str: str) -> int:
    """Parse 'M:SS' or 'H:MM:SS' string → seconds."""
    if not dur_str:
        return 0
    parts = dur_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0])
    except Exception:
        return 0


def _best_thumb(video_id: str, thumbs: list) -> str:
    """Return highest-res thumbnail URL, fall back to maxresdefault."""
    if thumbs:
        # yt-search-py returns list of {url, width, height}
        try:
            sorted_t = sorted(thumbs, key=lambda x: x.get("width", 0), reverse=True)
            if sorted_t and sorted_t[0].get("url"):
                return sorted_t[0]["url"]
        except Exception:
            pass
    return f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"


# ── Step 1: YouTube search via yt-search-py ───────────────────────────────────
async def search_youtube(query: str) -> Optional[Dict]:
    """
    Search YouTube for query, return first result metadata.
    Returns dict or None.
    """
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, _sync_search, query)
        return result
    except Exception as e:
        log.error("yt-search-py error [%s]: %s", query, e)
        return None


def _sync_search(query: str) -> Optional[Dict]:
    vs = VideosSearch(query, limit=1)
    data = vs.result()
    results = data.get("result", [])
    if not results:
        return None
    item = results[0]

    video_id  = item.get("id", "")
    title     = item.get("title", "Unknown")
    channel   = item.get("channel", {}).get("name", "") if isinstance(item.get("channel"), dict) else item.get("channel", "")
    dur_str   = item.get("duration") or "0:00"
    dur_sec   = _parse_dur(dur_str)
    thumbs    = item.get("thumbnails", [])
    thumb_url = _best_thumb(video_id, thumbs)

    # Try to extract year from publishedTime
    pub = item.get("publishedTime") or ""
    year = ""
    if pub:
        m = re.search(r"\b(20\d{2})\b", pub)
        year = m.group(1) if m else ""

    return {
        "id":           video_id,
        "title":        title,
        "artist":       channel,
        "album":        "",
        "year":         year,
        "duration_sec": dur_sec,
        "duration_str": dur_str,
        "thumb_url":    thumb_url,
        "yt_url":       f"https://www.youtube.com/watch?v={video_id}",
    }


async def get_info_from_url(url: str) -> Optional[Dict]:
    """
    Extract metadata from a direct YouTube URL using yt-search-py.
    Uses the video title as search query after extracting the video ID.
    """
    vid_id = extract_video_id(url)
    if not vid_id:
        return None

    # Search using the video ID as query — yt-search-py handles this
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, _sync_search, vid_id)
        if result:
            return result
    except Exception as e:
        log.error("URL info lookup failed [%s]: %s", url, e)

    # Fallback: return minimal info with just the video ID
    return {
        "id":           vid_id,
        "title":        "Unknown",
        "artist":       "",
        "album":        "",
        "year":         "",
        "duration_sec": 0,
        "duration_str": "0:00",
        "thumb_url":    f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg",
        "yt_url":       url,
    }


# ── Step 2: Get stream URL from music.xbitcode.com ────────────────────────────
async def get_stream_url(video_id: str, media_type: str = "audio") -> Optional[str]:
    """
    Fetch a direct streamable URL for the given YouTube video ID.
    media_type: "audio" | "video"
    """
    base = MUSIC_API_BASE.rstrip("/")
    url  = f"{base}/stream"
    params = {"id": video_id, "type": media_type}

    proxy = YT_PROXY_URL or None

    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as s:
            async with s.get(url, params=params, proxy=proxy) as r:
                if r.status == 200:
                    data = await r.json(content_type=None)
                    stream = (
                        data.get("url") or
                        data.get("stream_url") or
                        data.get("link") or
                        data.get("audio_url") or
                        data.get("video_url") or
                        data.get("download_url")
                    )
                    if stream:
                        log.debug("Stream URL fetched for %s (%s)", video_id, media_type)
                        return stream
                    log.warning("No URL key in xbitcode response: %s", data)
                else:
                    log.warning("xbitcode /stream returned %d for id=%s", r.status, video_id)
    except asyncio.TimeoutError:
        log.error("xbitcode API timeout for video_id=%s", video_id)
    except Exception as e:
        log.error("xbitcode API error [%s]: %s", video_id, e)

    return None


# ── Combined resolve (search OR url → full info + stream URL) ─────────────────
async def resolve(query: str, is_video: bool = False) -> Optional[Dict]:
    """
    Full resolution pipeline:
      1. Get metadata via yt-search-py
      2. Get stream URL via music.xbitcode.com
      3. Return merged dict or None
    Also enforces MAX_DURATION.
    """
    # Step 1: metadata
    if is_url(query):
        info = await get_info_from_url(query)
    else:
        info = await search_youtube(query)

    if not info:
        return None

    # Duration guard
    if info["duration_sec"] > MAX_DURATION * 60:
        return {"_too_long": True, "duration_sec": info["duration_sec"]}

    # Step 2: stream URL
    media_type = "video" if is_video else "audio"
    stream_url = await get_stream_url(info["id"], media_type)

    if not stream_url:
        # Final fallback: use the YouTube URL directly (pytgcalls can handle it)
        stream_url = info["yt_url"]
        log.warning("No xbitcode stream URL, falling back to yt_url for %s", info["id"])

    return {**info, "stream_url": stream_url, "is_video": is_video}
