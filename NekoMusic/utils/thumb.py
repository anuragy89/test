"""
NekoMusic — Thumbnail Generator v2
Matches the screenshot design:
  • Dark split-panel card  (art panel left | info panel right)
  • Neon cyan/teal outer glow border
  • Blurred song-cover as background with dominant-colour neon accents
  • Waveform visualiser bars
  • "NOW PLAYING" pill badge
  • Bold title  •  artist · album · year meta
  • Progress bar with glow dot
  • Control icons row

Output: 1280×720 PNG saved to CACHE_DIR — loads fast, web-safe.
"""

import asyncio
import colorsys
import math
import os
import random
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import CACHE_DIR
from logger import get_logger

log = get_logger("thumb")
Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
SPLIT = 500          # x-position where left art panel ends

# ── Font paths ────────────────────────────────────────────────────────────────
_ASSET = Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"
_FONT_BOLD   = str(_ASSET / "NotoSans-Bold.ttf")
_FONT_REG    = str(_ASSET / "NotoSans-Regular.ttf")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _FONT_BOLD if bold else _FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ── Colour helpers ────────────────────────────────────────────────────────────
def _dominant_colours(img: Image.Image) -> Tuple[Tuple, Tuple]:
    """Return (primary, secondary) dominant colours from the image."""
    small = img.convert("RGB").resize((64, 64), Image.LANCZOS)
    pixels = list(small.getdata())
    # Bucket into hue bands, pick top 2 buckets
    buckets: dict = {}
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        if s < 0.15 or v < 0.12:          # skip grays / blacks
            continue
        bucket = int(h * 12)              # 12 hue slices
        buckets[bucket] = buckets.get(bucket, 0) + 1

    if not buckets:
        return (0, 220, 255), (120, 0, 255)   # cyan, purple fallback

    sorted_b = sorted(buckets.items(), key=lambda x: -x[1])
    def hue_to_rgb(hue_bucket, sat=0.9, val=1.0):
        h = hue_bucket / 12
        r, g, b = colorsys.hsv_to_rgb(h, sat, val)
        return int(r*255), int(g*255), int(b*255)

    primary   = hue_to_rgb(sorted_b[0][0])
    secondary = hue_to_rgb(sorted_b[1][0] if len(sorted_b) > 1 else (sorted_b[0][0]+4)%12)
    return primary, secondary


def _neon_gradient_line(draw: ImageDraw.Draw, x0, y0, x1, y1,
                        c1: Tuple, c2: Tuple, width: int = 3):
    """Draw a horizontal gradient line from c1 to c2."""
    steps = abs(x1 - x0) or 1
    for i in range(steps):
        t = i / steps
        r = int(c1[0] + (c2[0]-c1[0]) * t)
        g = int(c1[1] + (c2[1]-c1[1]) * t)
        b = int(c1[2] + (c2[2]-c1[2]) * t)
        draw.line([(x0+i, y0), (x0+i, y0+width)], fill=(r, g, b, 255))


def _draw_glow_rect(img: Image.Image, x, y, w, h, colour: Tuple, radius: int = 24, blur: int = 18):
    """Draw a rounded glow box on an RGBA image."""
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    for i in range(3, 0, -1):
        alpha = 40 * i
        gd.rounded_rectangle([x-i*3, y-i*3, x+w+i*3, y+h+i*3],
                              radius=radius+i*3,
                              outline=(*colour, alpha), width=2)
    glow = glow.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(glow)


def _draw_waveform(draw: ImageDraw.Draw, cx: int, cy: int,
                   c1: Tuple, c2: Tuple, width: int = 300, bars: int = 28):
    """Animated-style waveform bars."""
    bar_w  = 6
    gap    = (width - bars * bar_w) // bars
    x_start = cx - width // 2

    # Random-ish heights that look like audio waveform
    seed_heights = [0.3, 0.6, 0.9, 0.7, 1.0, 0.8, 0.5, 0.4,
                    0.95, 0.75, 0.6, 0.85, 1.0, 0.9, 0.7, 0.5,
                    0.8, 1.0, 0.6, 0.4, 0.7, 0.9, 0.55, 0.3,
                    0.6, 0.8, 0.4, 0.2]

    for i in range(min(bars, len(seed_heights))):
        h_frac = seed_heights[i]
        bar_h  = int(h_frac * 90)
        x      = x_start + i * (bar_w + gap)
        y_top  = cy - bar_h // 2
        y_bot  = cy + bar_h // 2

        # Colour interpolation along bars
        t = i / bars
        r = int(c1[0] + (c2[0]-c1[0]) * t)
        g = int(c1[1] + (c2[1]-c1[1]) * t)
        b = int(c1[2] + (c2[2]-c1[2]) * t)

        draw.rounded_rectangle([x, y_top, x+bar_w, y_bot],
                                radius=bar_w//2, fill=(r, g, b, 230))


def _draw_progress(draw: ImageDraw.Draw, x: int, y: int, total_w: int,
                   progress: float, c1: Tuple, c2: Tuple,
                   dur_str: str = "3:30"):
    """Progress bar with gradient fill + glow dot."""
    track_h = 6
    filled  = int(total_w * progress)

    # Track background
    draw.rounded_rectangle([x, y, x+total_w, y+track_h],
                            radius=3, fill=(60, 70, 85, 200))
    # Gradient fill
    if filled > 0:
        for i in range(filled):
            t = i / max(filled, 1)
            r = int(c1[0] + (c2[0]-c1[0]) * t)
            g = int(c1[1] + (c2[1]-c1[1]) * t)
            b = int(c1[2] + (c2[2]-c1[2]) * t)
            draw.line([(x+i, y), (x+i, y+track_h)], fill=(r, g, b, 255))

    # Glow dot at progress point
    dot_x = x + filled
    dot_y = y + track_h // 2
    dot_r = 10
    for rad in range(dot_r, 0, -2):
        alpha = int(180 * (rad / dot_r))
        draw.ellipse([dot_x-rad, dot_y-rad, dot_x+rad, dot_y+rad],
                     fill=(*c2, alpha))
    draw.ellipse([dot_x-5, dot_y-5, dot_x+5, dot_y+5], fill=(255,255,255,255))

    # Time labels
    tf = _font(26)
    elapsed_secs = int(progress * _parse_dur(dur_str))
    m, s = divmod(elapsed_secs, 60)
    elapsed = f"{m}:{s:02d}"
    draw.text((x, y + track_h + 10), elapsed, font=tf, fill=(160, 180, 200))
    draw.text((x + total_w - 55, y + track_h + 10), dur_str, font=tf, fill=(130, 150, 175))


def _parse_dur(dur: str) -> int:
    parts = dur.split(":")
    try:
        if len(parts) == 2:
            return int(parts[0])*60 + int(parts[1])
        return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
    except Exception:
        return 210


def _draw_controls(draw: ImageDraw.Draw, cx: int, cy: int,
                   c1: Tuple, c2: Tuple, paused: bool = False):
    """Draw control icon row: ⏮  ▶/⏸  ⏭  🔀  🔁"""
    icons = ["⏮", "⏸" if not paused else "▶️", "⏭", "🔀", "🔁"]
    sizes = [34,   58,                             34,   34,   34]
    gap   = 90
    start = cx - gap * 2

    ef = _font(34)
    for i, (icon, sz) in enumerate(zip(icons, sizes)):
        x = start + i * gap
        f = _font(sz)
        if i == 1:   # centre play/pause button with circle bg
            r = 40
            draw.ellipse([x-r, cy-r, x+r, cy+r], fill=(*c1, 230))
            draw.ellipse([x-r+2, cy-r+2, x+r-2, cy+r-2], fill=(*c2, 200))
            draw.text((x-14, cy-18), icon, font=_font(36), fill=(255, 255, 255))
        else:
            draw.text((x-14, cy-14), icon, font=ef, fill=(160, 190, 210))


# ── Main generator ────────────────────────────────────────────────────────────
async def _fetch_image(url: str) -> Optional[Image.Image]:
    try:
        proxy = None
        from config import YT_PROXY_URL
        if YT_PROXY_URL:
            proxy = YT_PROXY_URL
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10), proxy=proxy) as r:
                if r.status == 200:
                    return Image.open(BytesIO(await r.read())).convert("RGBA")
    except Exception as e:
        log.warning("Fetch image failed: %s", e)
    return None


async def generate_thumbnail(
    title: str,
    artist: str = "",
    album: str = "",
    year: str = "",
    duration: str = "3:00",
    thumb_url: str = "",
    video_id: str = "",
    paused: bool = False,
    progress: float = 0.55,
) -> str:
    """
    Returns path to generated PNG thumbnail.
    Matches the Blue Horizon / neon music card screenshot.
    """
    safe_id  = (video_id or title[:20]).replace("/", "_").replace(" ", "_")
    out_path = os.path.join(CACHE_DIR, f"card_{safe_id}.png")

    try:
        # ── Fetch album art ──────────────────────────────────────────────────
        art: Optional[Image.Image] = None
        if thumb_url:
            art = await _fetch_image(thumb_url)

        # ── Dominant neon colours from art ───────────────────────────────────
        c1, c2 = ((0, 210, 240), (80, 0, 240))   # defaults: cyan, purple
        if art:
            try:
                c1, c2 = _dominant_colours(art)
            except Exception:
                pass

        # ── Base canvas — very dark navy ──────────────────────────────────────
        canvas = Image.new("RGBA", (W, H), (8, 14, 22, 255))
        draw   = ImageDraw.Draw(canvas)

        # ── Blurred art as global background (low opacity) ────────────────────
        if art:
            bg = art.convert("RGBA").resize((W, H), Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(40))
            # Dark overlay so text remains readable
            ov = Image.new("RGBA", (W, H), (8, 14, 22, 185))
            canvas.alpha_composite(bg)
            canvas.alpha_composite(ov)
            draw = ImageDraw.Draw(canvas)

        # ── Outer neon glow border ────────────────────────────────────────────
        border_img = Image.new("RGBA", (W, H), (0,0,0,0))
        bd = ImageDraw.Draw(border_img)
        for i in range(6, 0, -2):
            alpha = 60 * (7-i)
            bd.rounded_rectangle([i, i, W-i, H-i], radius=32,
                                  outline=(*c1, alpha), width=2)
        border_img = border_img.filter(ImageFilter.GaussianBlur(6))
        canvas.alpha_composite(border_img)
        draw = ImageDraw.Draw(canvas)

        # Solid thin border on top
        draw.rounded_rectangle([4, 4, W-4, H-4], radius=28,
                                outline=(*c1, 180), width=2)

        # ── LEFT PANEL — art ──────────────────────────────────────────────────
        # Semi-transparent dark panel
        lp = Image.new("RGBA", (W, H), (0,0,0,0))
        lpd = ImageDraw.Draw(lp)
        lpd.rounded_rectangle([10, 10, SPLIT-10, H-10], radius=20,
                               fill=(15, 22, 32, 180))
        canvas.alpha_composite(lp)
        draw = ImageDraw.Draw(canvas)

        # Art centred in left panel
        art_size = 320
        ax = (SPLIT - art_size) // 2
        ay = (H - art_size) // 2

        if art:
            art_sq = art.convert("RGBA").resize((art_size, art_size), Image.LANCZOS)
            # Soft rounded mask
            mask = Image.new("L", (art_size, art_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_size, art_size],
                                                   radius=20, fill=255)
            art_sq.putalpha(mask)
            canvas.alpha_composite(art_sq, (ax, ay))
        else:
            # Placeholder circle with music emoji
            draw.rounded_rectangle([ax, ay, ax+art_size, ay+art_size],
                                    radius=20, fill=(25, 35, 50, 220))
            draw.text((ax + art_size//2 - 50, ay + art_size//2 - 60),
                      "🎵", font=_font(100), fill=(100, 180, 220))

        # Neon glow around art
        _draw_glow_rect(canvas, ax-6, ay-6, art_size+12, art_size+12,
                        colour=c1, radius=26, blur=20)
        draw = ImageDraw.Draw(canvas)

        # ── RIGHT PANEL ───────────────────────────────────────────────────────
        rx = SPLIT + 50          # content start x
        ry = 80                  # content start y

        # "NOW PLAYING" pill
        pill_w, pill_h = 220, 38
        pill_x = rx
        pill_y = ry
        draw.rounded_rectangle([pill_x, pill_y, pill_x+pill_w, pill_y+pill_h],
                                radius=pill_h//2, outline=(*c1, 200), width=2,
                                fill=(0, 0, 0, 0))
        # Dot
        draw.ellipse([pill_x+14, pill_y+13, pill_x+26, pill_y+25],
                     fill=(*c1, 255))
        draw.text((pill_x+36, pill_y+8), "NOW PLAYING",
                  font=_font(18, bold=True), fill=(*c1, 230))

        # Waveform bars
        wf_y = pill_y + pill_h + 24
        _draw_waveform(draw, rx + 200, wf_y + 45, c1, c2, width=380, bars=28)

        # Title
        title_y = wf_y + 115
        title_disp = title[:28] + ("…" if len(title) > 28 else "")
        draw.text((rx, title_y), title_disp,
                  font=_font(72, bold=True), fill=(240, 245, 255))

        # Meta line: artist · album · year
        meta_y = title_y + 85
        meta_parts = [p for p in [artist, album, year] if p]
        meta_str   = " · ".join(meta_parts) if meta_parts else "Unknown Artist"
        draw.text((rx, meta_y), meta_str[:55],
                  font=_font(32), fill=(140, 165, 195))

        # Gradient separator line
        sep_y = meta_y + 52
        _neon_gradient_line(draw, rx, sep_y, W-50, sep_y, c1, c2, width=2)

        # Progress bar
        pb_y = sep_y + 22
        _draw_progress(draw, rx, pb_y, W-rx-60, progress, c1, c2, duration)

        # Controls
        ctrl_y = pb_y + 90
        _draw_controls(draw, rx + (W-rx-50)//2, ctrl_y + 30, c1, c2, paused)

        # ── NekoMusic watermark ───────────────────────────────────────────────
        wm = f"NekoMusic 🐱"
        draw.text((W - 190, H - 44), wm, font=_font(24), fill=(*c1, 140))

        # ── Save ──────────────────────────────────────────────────────────────
        final = canvas.convert("RGB")
        final.save(out_path, "PNG", optimize=True, quality=92)
        log.debug("Thumbnail saved: %s", out_path)
        return out_path

    except Exception as e:
        log.error("Thumbnail generation failed: %s", e)
        return _fallback(out_path, c1 if 'c1' in dir() else (0,210,240))


def _fallback(path: str, c1=(0,210,240)) -> str:
    img  = Image.new("RGB", (W, H), (8, 14, 22))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 4, W-4, H-4], radius=28, outline=c1, width=3)
    draw.text((W//2-120, H//2-30), "🎵 NekoMusic", font=_font(60, True), fill=c1)
    img.save(path, "PNG")
    return path
