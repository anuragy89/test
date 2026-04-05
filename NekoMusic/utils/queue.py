"""
NekoMusic — Per-chat Queue Manager
Supports up to 20 queued songs per group (configurable via QUEUE_LIMIT).
Each track stores its own Telegram message_id so its card can be edited/deleted.
"""

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

from config import QUEUE_LIMIT
from logger import get_logger

log = get_logger("queue")


@dataclass
class Track:
    # Core
    title:        str
    stream_url:   str
    duration_sec: int
    duration_str: str   = "0:00"
    # Metadata (for thumbnail + card)
    thumb_url:    str   = ""
    video_id:     str   = ""
    artist:       str   = ""
    album:        str   = ""
    year:         str   = ""
    # Who requested
    requested_by: str   = "Unknown"
    requested_id: int   = 0
    # Media type
    is_video:     bool  = False
    # Telegram message id of this track's queue card (set after send)
    card_msg_id:  int   = 0
    # Queue position (1-based, 0 = currently playing)
    queue_pos:    int   = 0


@dataclass
class ChatState:
    queue:      Deque[Track] = field(default_factory=deque)
    current:    Optional[Track] = None
    paused:     bool = False
    loop:       bool = False
    # message id of the "now playing" card
    now_msg_id: int  = 0


# Global state dict  {chat_id: ChatState}
_states: Dict[int, ChatState] = {}


def _state(chat_id: int) -> ChatState:
    if chat_id not in _states:
        _states[chat_id] = ChatState()
    return _states[chat_id]


# ── Write ops ─────────────────────────────────────────────────────────────────

def add_track(chat_id: int, track: Track) -> int:
    """
    Add track to this chat's queue.
    Returns:
      0   → no current track, play immediately
      1-N → queue position (1 = first in queue)
      -1  → queue full
    """
    st = _state(chat_id)
    if st.current is None:
        track.queue_pos = 0
        st.current = track
        return 0
    if len(st.queue) >= QUEUE_LIMIT:
        return -1
    pos = len(st.queue) + 1
    track.queue_pos = pos
    st.queue.append(track)
    return pos


def force_front(chat_id: int, track: Track):
    """Insert track at the front of queue (playforce — plays next)."""
    st = _state(chat_id)
    track.queue_pos = 1
    st.queue.appendleft(track)
    _renumber(chat_id)


def next_track(chat_id: int) -> Optional[Track]:
    """Pop next track from queue and set as current. Returns None if queue empty."""
    st = _state(chat_id)
    if st.loop and st.current:
        return st.current   # repeat same track
    if st.queue:
        st.current = st.queue.popleft()
        st.current.queue_pos = 0
        _renumber(chat_id)
        return st.current
    st.current = None
    return None


def clear(chat_id: int):
    st = _state(chat_id)
    st.queue.clear()
    st.current  = None
    st.paused   = False
    st.now_msg_id = 0


def shuffle_queue(chat_id: int) -> bool:
    st = _state(chat_id)
    if len(st.queue) < 2:
        return False
    lst = list(st.queue)
    random.shuffle(lst)
    st.queue = deque(lst)
    _renumber(chat_id)
    return True


def toggle_loop(chat_id: int) -> bool:
    st = _state(chat_id)
    st.loop = not st.loop
    return st.loop


# ── Read ops ──────────────────────────────────────────────────────────────────

def current(chat_id: int) -> Optional[Track]:
    return _state(chat_id).current


def get_queue(chat_id: int) -> List[Track]:
    return list(_state(chat_id).queue)


def queue_len(chat_id: int) -> int:
    return len(_state(chat_id).queue)


def is_paused(chat_id: int) -> bool:
    return _state(chat_id).paused


def get_loop(chat_id: int) -> bool:
    return _state(chat_id).loop


# ── State setters ─────────────────────────────────────────────────────────────

def set_paused(chat_id: int, val: bool):
    _state(chat_id).paused = val


def set_now_msg_id(chat_id: int, mid: int):
    _state(chat_id).now_msg_id = mid


def get_now_msg_id(chat_id: int) -> int:
    return _state(chat_id).now_msg_id


def set_card_msg_id(chat_id: int, pos: int, mid: int):
    """Store the Telegram message id for a queued track's card."""
    for t in _state(chat_id).queue:
        if t.queue_pos == pos:
            t.card_msg_id = mid
            return


def get_all_card_msg_ids(chat_id: int) -> List[int]:
    """Return all queue-card message ids (for bulk delete on /end)."""
    return [t.card_msg_id for t in _state(chat_id).queue if t.card_msg_id]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _renumber(chat_id: int):
    """Re-assign queue_pos after shuffle / pop."""
    for i, t in enumerate(_state(chat_id).queue, 1):
        t.queue_pos = i
