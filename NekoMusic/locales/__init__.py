import importlib
from typing import Optional
from config import DEFAULT_LANGUAGE
from logger import get_logger
log = get_logger("locales")
_CACHE: dict = {}

def _load(lang: str) -> dict:
    if lang not in _CACHE:
        try:
            _CACHE[lang] = importlib.import_module(f"NekoMusic.locales.{lang}").strings
        except Exception:
            if lang != "en": return _load("en")
            _CACHE["en"] = {}
    return _CACHE.get(lang, {})

def get_string(key: str, lang=None, **kw) -> str:
    lang = lang or DEFAULT_LANGUAGE
    strings = _load(lang)
    if key not in strings: strings = _load("en")
    text = strings.get(key, f"[{key}]")
    try: return text.format(**kw) if kw else text
    except: return text

_ = get_string
