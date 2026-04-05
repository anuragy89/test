"""NekoMusic — Async MongoDB layer (Motor)"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import motor.motor_asyncio
from pymongo import ASCENDING

from config import MONGO_URI, DATABASE_NAME, DEFAULT_LANGUAGE
from logger import get_logger

log = get_logger("db")


class Database:
    def __init__(self):
        self._client = None
        self.db = None

    async def connect(self):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGO_URI, serverSelectionTimeoutMS=5000, maxPoolSize=100, minPoolSize=5)
        self.db = self._client[DATABASE_NAME]
        await self.db.users.create_index([("user_id", ASCENDING)], unique=True)
        await self.db.groups.create_index([("chat_id", ASCENDING)], unique=True)
        log.info("✅ MongoDB connected → %s", DATABASE_NAME)

    async def close(self):
        if self._client:
            self._client.close()

    # ── Users ─────────────────────────────────────────────────────────────────
    async def add_user(self, user_id: int, name: str, username: str = ""):
        await self.db.users.update_one({"user_id": user_id}, {"$setOnInsert": {
            "user_id": user_id, "name": name, "username": username,
            "joined": datetime.utcnow(), "lang": DEFAULT_LANGUAGE, "banned": False,
        }}, upsert=True)

    async def get_user(self, user_id: int) -> Optional[Dict]:
        return await self.db.users.find_one({"user_id": user_id})

    async def get_all_users(self) -> List[Dict]:
        return await self.db.users.find({"banned": False}).to_list(length=None)

    async def total_users(self) -> int:
        return await self.db.users.count_documents({})

    async def set_user_lang(self, user_id: int, lang: str):
        await self.db.users.update_one({"user_id": user_id}, {"$set": {"lang": lang}}, upsert=True)

    async def get_user_lang(self, user_id: int) -> str:
        doc = await self.db.users.find_one({"user_id": user_id}, {"lang": 1})
        return doc.get("lang", DEFAULT_LANGUAGE) if doc else DEFAULT_LANGUAGE

    async def ban_user(self, user_id: int):
        await self.db.users.update_one({"user_id": user_id}, {"$set": {"banned": True}})

    async def unban_user(self, user_id: int):
        await self.db.users.update_one({"user_id": user_id}, {"$set": {"banned": False}})

    # ── Groups ────────────────────────────────────────────────────────────────
    async def add_group(self, chat_id: int, title: str):
        await self.db.groups.update_one({"chat_id": chat_id}, {"$setOnInsert": {
            "chat_id": chat_id, "title": title,
            "joined": datetime.utcnow(), "lang": DEFAULT_LANGUAGE, "banned": False,
        }}, upsert=True)

    async def get_all_groups(self) -> List[Dict]:
        return await self.db.groups.find({"banned": False}).to_list(length=None)

    async def total_groups(self) -> int:
        return await self.db.groups.count_documents({})

    async def set_group_lang(self, chat_id: int, lang: str):
        await self.db.groups.update_one({"chat_id": chat_id}, {"$set": {"lang": lang}}, upsert=True)

    async def get_group_lang(self, chat_id: int) -> str:
        doc = await self.db.groups.find_one({"chat_id": chat_id}, {"lang": 1})
        return doc.get("lang", DEFAULT_LANGUAGE) if doc else DEFAULT_LANGUAGE

    # ── Stats ─────────────────────────────────────────────────────────────────
    async def inc_songs_played(self):
        await self.db.stats.update_one({"key": "global"}, {"$inc": {"songs_played": 1}}, upsert=True)

    async def get_stats(self) -> Dict[str, Any]:
        doc = await self.db.stats.find_one({"key": "global"}) or {}
        return {
            "songs_played":  doc.get("songs_played", 0),
            "total_users":   await self.total_users(),
            "total_groups":  await self.total_groups(),
        }


db = Database()
