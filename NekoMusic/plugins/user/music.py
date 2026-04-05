"""
NekoMusic — Music Plugin (ALL-IN-ONE)
py-tgcalls==2.2.11 — correct API:
  from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
  from pytgcalls.types.input_stream.quality import HighQualityAudio, HighQualityVideo
"""

import os
import time

from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

# py-tgcalls 2.2.x EXACT imports (verified from source)
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, HighQualityVideo
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    GroupCallNotFound,
    NoActiveGroupCall,
)

from NekoMusic.client import bot, call
from NekoMusic.database.db import db
from NekoMusic.locales import get_string
from NekoMusic.utils.keyboards import now_playing_kb, queue_card_kb
from NekoMusic.utils.musicapi import resolve
from NekoMusic.utils.queue import (
    Track, add_track, force_front, next_track, current,
    clear, get_queue, get_all_card_msg_ids,
    is_paused, set_paused, get_loop, toggle_loop,
    shuffle_queue, set_now_msg_id, get_now_msg_id,
    set_card_msg_id,
)
from NekoMusic.utils.thumb import generate_thumbnail
from config import E, MAX_DURATION, pe
from logger import get_logger

log = get_logger("music")


async def _lang(chat_id: int) -> str:
    try:
        return await db.get_group_lang(chat_id)
    except Exception:
        return "en"


async def _err(msg: Message, key: str, lang: str, **kw):
    await msg.reply_text(get_string(key, lang, **kw), quote=True)


async def _stream_track(chat_id: int, track: Track):
    url = track.stream_url
    if track.is_video:
        stream = AudioVideoPiped(url, HighQualityAudio(), HighQualityVideo())
    else:
        stream = AudioPiped(url, HighQualityAudio())
    await call.join_group_call(chat_id, stream)


async def _send_now_playing(chat_id: int, track: Track, lang: str,
                             reply_msg: Message = None):
    thumb = await generate_thumbnail(
        title=track.title, artist=track.artist, album=track.album,
        year=track.year, duration=track.duration_str,
        thumb_url=track.thumb_url, video_id=track.video_id,
    )
    caption = (
        f"{E.BULLET}{E.BULLET} <b>Started Streaming</b> "
        f"{pe(E.NOTE, E.NOTE_ID)}\n\n"
        f"{pe(E.SPARKLE, E.SPARKLE_ID)} <b>Title :</b> "
        f"<a href='https://youtu.be/{track.video_id}'>{track.title}</a>\n"
        f"{pe(E.CLOCK, E.CLOCK_ID)} <b>Duration :</b> {track.duration_str}\n"
        f"{pe(E.ARTIST, E.ARTIST_ID)} <b>Requested by :</b> {track.requested_by}"
    )
    try:
        if reply_msg:
            sent = await reply_msg.reply_photo(
                photo=thumb, caption=caption,
                reply_markup=now_playing_kb(chat_id, paused=False, loop=get_loop(chat_id)),
                quote=True,
            )
        else:
            sent = await bot.send_photo(
                chat_id=chat_id, photo=thumb, caption=caption,
                reply_markup=now_playing_kb(chat_id, paused=False, loop=get_loop(chat_id)),
            )
        set_now_msg_id(chat_id, sent.id)
    except Exception as e:
        log.error("now-playing card error [%s]: %s", chat_id, e)
    finally:
        try:
            if os.path.exists(thumb):
                os.remove(thumb)
        except Exception:
            pass


async def _send_queue_card(chat_id: int, track: Track, pos: int,
                            reply_msg: Message = None):
    caption = (
        f"{E.RESTART} <b>Added To Queue At #{pos}</b>\n\n"
        f"{pe(E.SPARKLE, E.SPARKLE_ID)} <b>Title :</b> "
        f"<a href='https://youtu.be/{track.video_id}'>{track.title}</a>\n"
        f"{pe(E.CLOCK, E.CLOCK_ID)} <b>Duration :</b> {track.duration_str} minutes\n"
        f"{pe(E.ARTIST, E.ARTIST_ID)} <b>Requested by :</b> {track.requested_by}"
    )
    try:
        if reply_msg:
            sent = await reply_msg.reply_text(
                caption, reply_markup=queue_card_kb(chat_id, pos), quote=True)
        else:
            sent = await bot.send_message(
                chat_id=chat_id, text=caption,
                reply_markup=queue_card_kb(chat_id, pos))
        set_card_msg_id(chat_id, pos, sent.id)
    except Exception as e:
        log.error("queue card error [%s]: %s", chat_id, e)


async def _delete_queue_cards(chat_id: int):
    ids = get_all_card_msg_ids(chat_id)
    if ids:
        try:
            await bot.delete_messages(chat_id, ids)
        except Exception:
            pass


async def _do_end(chat_id: int):
    mid = get_now_msg_id(chat_id)
    if mid:
        try:
            await bot.delete_messages(chat_id, [mid])
        except Exception:
            pass
    await _delete_queue_cards(chat_id)
    try:
        await call.leave_group_call(chat_id)
    except Exception:
        pass
    clear(chat_id)


async def _do_skip(chat_id: int, lang: str, reply_msg: Message = None):
    mid = get_now_msg_id(chat_id)
    if mid:
        try:
            await bot.delete_messages(chat_id, [mid])
        except Exception:
            pass
        set_now_msg_id(chat_id, 0)

    nxt = next_track(chat_id)
    if nxt:
        try:
            await _stream_track(chat_id, nxt)
            await db.inc_songs_played()
            if nxt.card_msg_id:
                try:
                    await bot.delete_messages(chat_id, [nxt.card_msg_id])
                except Exception:
                    pass
            await _send_now_playing(chat_id, nxt, lang, reply_msg=reply_msg)
        except (NoActiveGroupCall, GroupCallNotFound):
            clear(chat_id)
            if reply_msg:
                await _err(reply_msg, "err_vc_not_started", lang)
        except Exception as e:
            log.error("skip error [%s]: %s", chat_id, e)
            clear(chat_id)
    else:
        await _do_end(chat_id)
        if reply_msg:
            await reply_msg.reply_text(get_string("ended", lang))


async def _core_play(msg: Message, query: str,
                     is_video: bool = False, force: bool = False):
    chat_id = msg.chat.id
    user    = msg.from_user
    lang    = await _lang(chat_id)
    query   = query.strip()

    if not query:
        return await _err(msg, "err_no_url", lang)

    await db.add_group(chat_id, msg.chat.title or "")

    status = await msg.reply_text(
        f"{pe(E.LOADING, E.LOADING_ID)} "
        f"{get_string('play_searching', lang, query=query[:50])}",
        quote=True,
    )

    info = await resolve(query, is_video=is_video)

    if not info:
        await status.delete()
        return await _err(msg, "err_not_found", lang)

    if info.get("_too_long"):
        await status.delete()
        return await _err(msg, "err_too_long", lang, max=MAX_DURATION)

    await status.edit_text(
        f"{pe(E.DOWNLOAD, E.DOWNLOAD_ID)} "
        f"{get_string('play_downloading', lang, title=info['title'][:40])}"
    )

    track = Track(
        title=info["title"], stream_url=info["stream_url"],
        duration_sec=info["duration_sec"], duration_str=info["duration_str"],
        thumb_url=info.get("thumb_url", ""), video_id=info.get("id", ""),
        artist=info.get("artist", ""), album=info.get("album", ""),
        year=info.get("year", ""), requested_by=user.mention,
        requested_id=user.id, is_video=is_video,
    )

    if force:
        force_front(chat_id, track)
        pos = 0
    else:
        pos = add_track(chat_id, track)

    await status.delete()

    if pos == -1:
        return await _err(msg, "err_queue_full", lang, limit=20)

    if pos == 0:
        try:
            await _stream_track(chat_id, track)
        except (NoActiveGroupCall, GroupCallNotFound):
            clear(chat_id)
            return await _err(msg, "err_vc_not_started", lang)
        except AlreadyJoinedError:
            pass
        except Exception as e:
            log.error("Stream error [%s]: %s", chat_id, e)
            clear(chat_id)
            return await _err(msg, "err_join_vc", lang)
        await db.inc_songs_played()
        await _send_now_playing(chat_id, track, lang, reply_msg=msg)
    else:
        await _send_queue_card(chat_id, track, pos, reply_msg=msg)


@bot.on_message(filters.command("play") & filters.group)
async def cmd_play(_, msg: Message):
    q = " ".join(msg.command[1:])
    if not q and msg.reply_to_message:
        rp = msg.reply_to_message
        q  = (rp.text or (rp.audio and (rp.audio.title or rp.audio.file_name)) or "").strip()
    await _core_play(msg, q)


@bot.on_message(filters.command("vplay") & filters.group)
async def cmd_vplay(_, msg: Message):
    await _core_play(msg, " ".join(msg.command[1:]), is_video=True)


@bot.on_message(filters.command("playforce") & filters.group)
async def cmd_playforce(_, msg: Message):
    await _core_play(msg, " ".join(msg.command[1:]), force=True)


@bot.on_message(filters.command("pause") & filters.group)
async def cmd_pause(_, msg: Message):
    chat_id = msg.chat.id
    lang    = await _lang(chat_id)
    if not current(chat_id):
        return await _err(msg, "err_no_active", lang)
    if is_paused(chat_id):
        return await _err(msg, "err_already_paused", lang)
    try:
        await call.pause_stream(chat_id)
        set_paused(chat_id, True)
        await msg.reply_text(get_string("paused", lang))
        mid = get_now_msg_id(chat_id)
        if mid:
            try:
                await bot.edit_message_reply_markup(
                    chat_id, mid,
                    now_playing_kb(chat_id, paused=True, loop=get_loop(chat_id)))
            except Exception:
                pass
    except Exception as e:
        log.error("pause error: %s", e)


@bot.on_message(filters.command("resume") & filters.group)
async def cmd_resume(_, msg: Message):
    chat_id = msg.chat.id
    lang    = await _lang(chat_id)
    if not current(chat_id):
        return await _err(msg, "err_no_active", lang)
    if not is_paused(chat_id):
        return await _err(msg, "err_already_playing", lang)
    try:
        await call.resume_stream(chat_id)
        set_paused(chat_id, False)
        await msg.reply_text(get_string("resumed", lang))
        mid = get_now_msg_id(chat_id)
        if mid:
            try:
                await bot.edit_message_reply_markup(
                    chat_id, mid,
                    now_playing_kb(chat_id, paused=False, loop=get_loop(chat_id)))
            except Exception:
                pass
    except Exception as e:
        log.error("resume error: %s", e)


@bot.on_message(filters.command("skip") & filters.group)
async def cmd_skip(_, msg: Message):
    chat_id = msg.chat.id
    lang    = await _lang(chat_id)
    if not current(chat_id):
        return await _err(msg, "err_no_active", lang)
    await _do_skip(chat_id, lang, reply_msg=msg)


@bot.on_message(filters.command("end") & filters.group)
async def cmd_end(_, msg: Message):
    chat_id = msg.chat.id
    lang    = await _lang(chat_id)
    if not current(chat_id):
        return await _err(msg, "err_no_active", lang)
    await _do_end(chat_id)
    await msg.reply_text(get_string("ended", lang))


@bot.on_message(filters.command("queue") & filters.group)
async def cmd_queue(_, msg: Message):
    chat_id = msg.chat.id
    lang    = await _lang(chat_id)
    cur     = current(chat_id)
    q       = get_queue(chat_id)
    if not cur and not q:
        return await _err(msg, "err_no_active", lang)
    lines = []
    if cur:
        lines.append(
            f"{pe(E.PLAY, E.PLAY_ID)} <b>Now Playing:</b> {cur.title} [{cur.duration_str}]")
    for t in q:
        lines.append(f"  {t.queue_pos}. {t.title} [{t.duration_str}]")
    await msg.reply_text("\n".join(lines))


@bot.on_message(filters.command("ping"))
async def cmd_ping(_, msg: Message):
    chat_id = msg.chat.id
    is_grp  = msg.chat.type.value in ("group", "supergroup")
    lang    = (await db.get_group_lang(chat_id) if is_grp
               else await db.get_user_lang(msg.from_user.id))
    t0      = time.monotonic()
    sent    = await msg.reply_text(f"{pe(E.PING, E.PING_ID)} Pinging...")
    ms      = round((time.monotonic() - t0) * 1000, 2)
    await sent.edit_text(get_string("ping", lang, latency=ms))


@bot.on_callback_query(filters.regex(r"^vc_pause_(-?\d+)$"))
async def cb_pause(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    lang    = await _lang(chat_id)
    if is_paused(chat_id):
        return await cq.answer(get_string("err_already_paused", lang), show_alert=True)
    try:
        await call.pause_stream(chat_id)
        set_paused(chat_id, True)
        await cq.message.edit_reply_markup(
            now_playing_kb(chat_id, paused=True, loop=get_loop(chat_id)))
        await cq.answer(get_string("paused", lang))
    except Exception as e:
        await cq.answer(str(e)[:200], show_alert=True)


@bot.on_callback_query(filters.regex(r"^vc_resume_(-?\d+)$"))
async def cb_resume(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    lang    = await _lang(chat_id)
    if not is_paused(chat_id):
        return await cq.answer(get_string("err_already_playing", lang), show_alert=True)
    try:
        await call.resume_stream(chat_id)
        set_paused(chat_id, False)
        await cq.message.edit_reply_markup(
            now_playing_kb(chat_id, paused=False, loop=get_loop(chat_id)))
        await cq.answer(get_string("resumed", lang))
    except Exception as e:
        await cq.answer(str(e)[:200], show_alert=True)


@bot.on_callback_query(filters.regex(r"^vc_skip_(-?\d+)$"))
async def cb_skip(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    lang    = await _lang(chat_id)
    await cq.answer(get_string("skipped", lang))
    await _do_skip(chat_id, lang)


@bot.on_callback_query(filters.regex(r"^vc_end_(-?\d+)$"))
async def cb_end(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    lang    = await _lang(chat_id)
    await _do_end(chat_id)
    await cq.answer(get_string("ended", lang))


@bot.on_callback_query(filters.regex(r"^vc_shuf_(-?\d+)$"))
async def cb_shuffle(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    lang    = await _lang(chat_id)
    ok      = shuffle_queue(chat_id)
    await cq.answer(
        get_string("shuffled", lang) if ok else "Need 2+ songs to shuffle.",
        show_alert=not ok)


@bot.on_callback_query(filters.regex(r"^vc_loop_(-?\d+)$"))
async def cb_loop(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    state   = toggle_loop(chat_id)
    await cq.message.edit_reply_markup(
        now_playing_kb(chat_id, paused=is_paused(chat_id), loop=state))
    await cq.answer(f"Loop {'enabled ✅' if state else 'disabled ❌'}")


@bot.on_callback_query(filters.regex(r"^q_playnow_(-?\d+)_(\d+)$"))
async def cb_q_playnow(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    lang    = await _lang(chat_id)
    await cq.answer("▶ Playing now...")
    await _do_skip(chat_id, lang)


@bot.on_callback_query(filters.regex(r"^q_skipto_(-?\d+)_(\d+)$"))
async def cb_q_skipto(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    lang    = await _lang(chat_id)
    await cq.answer(get_string("skipped", lang))
    await _do_skip(chat_id, lang)


@bot.on_callback_query(filters.regex(r"^q_remove_(-?\d+)_(\d+)$"))
async def cb_q_remove(_, cq: CallbackQuery):
    chat_id = int(cq.matches[0].group(1))
    pos     = int(cq.matches[0].group(2))
    removed = False
    for t in get_queue(chat_id):
        if t.queue_pos == pos:
            from NekoMusic.utils.queue import _state, _renumber
            _state(chat_id).queue.remove(t)
            _renumber(chat_id)
            removed = True
            break
    if removed:
        await cq.answer("🗑 Removed from queue.")
        try:
            await cq.message.delete()
        except Exception:
            pass
    else:
        await cq.answer("Song not found in queue.", show_alert=True)


@call.on_stream_end()
async def on_stream_end(client: PyTgCalls, update: Update):
    chat_id = update.chat_id
    log.debug("Stream ended: %s", chat_id)

    mid = get_now_msg_id(chat_id)
    if mid:
        try:
            await bot.delete_messages(chat_id, [mid])
        except Exception:
            pass
        set_now_msg_id(chat_id, 0)

    nxt = next_track(chat_id)
    if not nxt:
        clear(chat_id)
        try:
            await client.leave_group_call(chat_id)
        except Exception:
            pass
        return

    try:
        await _stream_track(chat_id, nxt)
        await db.inc_songs_played()
        if nxt.card_msg_id:
            try:
                await bot.delete_messages(chat_id, [nxt.card_msg_id])
            except Exception:
                pass
        lang = await db.get_group_lang(chat_id)
        await _send_now_playing(chat_id, nxt, lang)
    except Exception as e:
        log.error("auto-next error [%s]: %s", chat_id, e)
        clear(chat_id)
        try:
            await client.leave_group_call(chat_id)
        except Exception:
            pass
