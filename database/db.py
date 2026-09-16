import motor.motor_asyncio
import datetime
from config import DB_NAME, DB_URI, ADMINS
from logger import LOGGER

logger = LOGGER(__name__)

class Database:
    def __init__(self, uri: str, database_name: str):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self._indexes_created = False

    async def ensure_indexes(self):
        """Creates indexes for fast queries if not already created."""
        if not self._indexes_created:
            try:
                await self.col.create_index("id", unique=True)
                self._indexes_created = True
                logger.info("Database index on 'id' verified.")
            except Exception as e:
                logger.warning(f"Failed to create index on 'id': {e}")

    def new_user(self, user_id: int, name: str) -> dict:
        return {
            "id": int(user_id),
            "name": name,
            "session": None,
            "daily_usage": 0,
            "limit_reset_time": None,
            "is_premium": False,
            "premium_expiry": None,
            "is_banned": False,
            "dump_chat": None,
            "caption": None,
            "thumbnail": None,
            "delete_words": [],
            "replace_words": {}
        }

    async def add_user(self, user_id: int, name: str):
        await self.ensure_indexes()
        user = self.new_user(user_id, name)
        try:
            await self.col.update_one(
                {"id": int(user_id)},
                {"$setOnInsert": user},
                upsert=True
            )
            logger.info(f"User synced in DB: {user_id} - {name}")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")

    async def is_user_exist(self, user_id: int) -> bool:
        try:
            user = await self.col.find_one({"id": int(user_id)})
            return bool(user)
        except Exception as e:
            logger.error(f"Error checking user existence {user_id}: {e}")
            return False

    async def total_users_count(self) -> int:
        try:
            return await self.col.count_documents({})
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id: int):
        try:
            await self.col.delete_many({"id": int(user_id)})
            logger.info(f"User deleted from DB: {user_id}")
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")

    async def set_session(self, user_id: int, session: str | None):
        try:
            await self.col.update_one({"id": int(user_id)}, {"$set": {"session": session}})
        except Exception as e:
            logger.error(f"Error setting session for {user_id}: {e}")

    async def get_session(self, user_id: int) -> str | None:
        try:
            user = await self.col.find_one({"id": int(user_id)})
            return user.get("session") if user else None
        except Exception as e:
            logger.error(f"Error getting session for {user_id}: {e}")
            return None

    # Caption Support
    async def set_caption(self, user_id: int, caption: str):
        await self.col.update_one({"id": int(user_id)}, {"$set": {"caption": caption}})

    async def get_caption(self, user_id: int) -> str | None:
        user = await self.col.find_one({"id": int(user_id)})
        return user.get("caption") if user else None

    async def del_caption(self, user_id: int):
        await self.col.update_one({"id": int(user_id)}, {"$unset": {"caption": ""}})

    # Thumbnail Support
    async def set_thumbnail(self, user_id: int, thumbnail: str):
        await self.col.update_one({"id": int(user_id)}, {"$set": {"thumbnail": thumbnail}})

    async def get_thumbnail(self, user_id: int) -> str | None:
        user = await self.col.find_one({"id": int(user_id)})
        return user.get("thumbnail") if user else None

    async def del_thumbnail(self, user_id: int):
        await self.col.update_one({"id": int(user_id)}, {"$unset": {"thumbnail": ""}})

    # Premium Support
    async def add_premium(self, user_id: int, expiry_date: str | None):
        await self.col.update_one(
            {"id": int(user_id)},
            {
                "$set": {
                    "is_premium": True,
                    "premium_expiry": expiry_date,
                    "daily_usage": 0,
                    "limit_reset_time": None
                }
            }
        )
        logger.info(f"User {user_id} granted premium until {expiry_date}")

    async def remove_premium(self, user_id: int):
        await self.col.update_one(
            {"id": int(user_id)},
            {"$set": {"is_premium": False, "premium_expiry": None}}
        )
        logger.info(f"User {user_id} removed from premium")

    async def check_premium(self, user_id: int):
        if int(user_id) in ADMINS:
            return True
        user = await self.col.find_one({"id": int(user_id)})
        if user and user.get("is_premium"):
            expiry = user.get("premium_expiry")
            if expiry:
                try:
                    if isinstance(expiry, (datetime.date, datetime.datetime)):
                        exp_date = expiry.date() if isinstance(expiry, datetime.datetime) else expiry
                    else:
                        exp_date = datetime.date.fromisoformat(str(expiry))
                    if datetime.date.today() > exp_date:
                        await self.remove_premium(user_id)
                        return None
                except Exception as e:
                    logger.error(f"Error checking premium expiry for {user_id}: {e}")
            return user.get("premium_expiry") or True
        return None

    async def get_premium_users(self):
        return self.col.find({"is_premium": True})

    # Ban Support
    async def ban_user(self, user_id: int):
        await self.col.update_one({"id": int(user_id)}, {"$set": {"is_banned": True}})
        logger.warning(f"User banned: {user_id}")

    async def unban_user(self, user_id: int):
        await self.col.update_one({"id": int(user_id)}, {"$set": {"is_banned": False}})
        logger.info(f"User unbanned: {user_id}")

    async def is_banned(self, user_id: int) -> bool:
        user = await self.col.find_one({"id": int(user_id)})
        return bool(user.get("is_banned", False)) if user else False

    # Dump Chat Support
    async def set_dump_chat(self, user_id: int, chat_id: int | None):
        await self.col.update_one(
            {"id": int(user_id)},
            {"$set": {"dump_chat": int(chat_id) if chat_id is not None else None}}
        )

    async def get_dump_chat(self, user_id: int) -> int | None:
        user = await self.col.find_one({"id": int(user_id)})
        return user.get("dump_chat") if user else None

    # Delete/Replace Words Support
    async def set_delete_words(self, user_id: int, words: list[str]):
        await self.col.update_one(
            {"id": int(user_id)},
            {"$addToSet": {"delete_words": {"$each": words}}}
        )

    async def get_delete_words(self, user_id: int) -> list[str]:
        user = await self.col.find_one({"id": int(user_id)})
        return user.get("delete_words", []) if user else []

    async def remove_delete_words(self, user_id: int, words: list[str]):
        await self.col.update_one(
            {"id": int(user_id)},
            {"$pull": {"delete_words": {"$in": words}}}
        )

    async def set_replace_words(self, user_id: int, repl_dict: dict[str, str]):
        user = await self.col.find_one({"id": int(user_id)})
        current_repl = user.get("replace_words", {}) if user else {}
        current_repl.update(repl_dict)
        await self.col.update_one({"id": int(user_id)}, {"$set": {"replace_words": current_repl}})

    async def get_replace_words(self, user_id: int) -> dict[str, str]:
        user = await self.col.find_one({"id": int(user_id)})
        return user.get("replace_words", {}) if user else {}

    async def remove_replace_words(self, user_id: int, words: list[str]):
        user = await self.col.find_one({"id": int(user_id)})
        current_repl = user.get("replace_words", {}) if user else {}
        for w in words:
            current_repl.pop(w, None)
        await self.col.update_one({"id": int(user_id)}, {"$set": {"replace_words": current_repl}})

    # Daily Limits
    async def check_limit(self, user_id: int) -> bool:
        """
        Returns: True if BLOCKED (limit reached), False if ALLOWED.
        """
        if int(user_id) in ADMINS:
            return False

        if await self.check_premium(user_id):
            return False

        user = await self.col.find_one({"id": int(user_id)})
        if not user:
            return False

        now = datetime.datetime.now()
        reset_time = user.get("limit_reset_time")

        if reset_time is None or now >= reset_time:
            await self.col.update_one(
                {"id": int(user_id)},
                {"$set": {"daily_usage": 0, "limit_reset_time": None}}
            )
            return False

        usage = user.get("daily_usage", 0)
        return usage >= 10

    async def add_traffic(self, user_id: int):
        if int(user_id) in ADMINS or await self.check_premium(user_id):
            return

        user = await self.col.find_one({"id": int(user_id)})
        if not user:
            return

        now = datetime.datetime.now()
        reset_time = user.get("limit_reset_time")

        if reset_time is None:
            new_reset_time = now + datetime.timedelta(hours=24)
            await self.col.update_one(
                {"id": int(user_id)},
                {"$set": {"daily_usage": 1, "limit_reset_time": new_reset_time}}
            )
        else:
            await self.col.update_one(
                {"id": int(user_id)},
                {"$inc": {"daily_usage": 1}}
            )

    # Force Subscribe (FSub 2.0) Methods
    async def get_fsub_channels(self) -> list[dict]:
        """Returns list of all configured FSub channels: [{'channel': str, 'title': str, 'invite_link': str, 'is_join_request': bool}]"""
        try:
            doc = await self.db.settings.find_one({"_id": "fsub_channels"})
            if doc and "channels" in doc:
                return doc["channels"]
            # Fallback legacy single fsub check
            legacy = await self.db.settings.find_one({"_id": "fsub"})
            if legacy and legacy.get("channel"):
                return [{"channel": legacy["channel"], "title": "Updates Channel", "invite_link": legacy.get("invite_link"), "is_join_request": True}]
            return []
        except Exception as e:
            logger.error(f"Error getting fsub channels: {e}")
            return []

    async def add_fsub_channel(self, channel: str | int, title: str = "Updates Channel", invite_link: str | None = None, is_join_request: bool = True):
        try:
            channel_str = str(channel)
            # Remove existing if present to avoid duplicates
            await self.db.settings.update_one(
                {"_id": "fsub_channels"},
                {"$pull": {"channels": {"channel": channel_str}}},
                upsert=True
            )
            # Add new channel configuration
            new_item = {
                "channel": channel_str,
                "title": title,
                "invite_link": invite_link,
                "is_join_request": is_join_request
            }
            await self.db.settings.update_one(
                {"_id": "fsub_channels"},
                {"$push": {"channels": new_item}},
                upsert=True
            )
            logger.info(f"Added FSub channel: {channel_str} ({title})")
        except Exception as e:
            logger.error(f"Error adding fsub channel: {e}")

    async def remove_fsub_channel(self, channel: str | int) -> bool:
        try:
            channel_str = str(channel)
            res = await self.db.settings.update_one(
                {"_id": "fsub_channels"},
                {"$pull": {"channels": {"channel": channel_str}}}
            )
            await self.db.settings.delete_one({"_id": "fsub"})
            return res.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing fsub channel: {e}")
            return False

    async def clear_fsub_channels(self):
        try:
            await self.db.settings.delete_one({"_id": "fsub_channels"})
            await self.db.settings.delete_one({"_id": "fsub"})
            logger.info("All FSub channels cleared")
        except Exception as e:
            logger.error(f"Error clearing fsub channels: {e}")

    async def record_join_request(self, user_id: int, chat_id: int | str):
        try:
            await self.db.join_requests.update_one(
                {"user_id": int(user_id), "chat_id": str(chat_id)},
                {"$set": {"timestamp": datetime.datetime.now()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error recording join request: {e}")

    async def is_join_requested(self, user_id: int, chat_id: int | str) -> bool:
        try:
            doc = await self.db.join_requests.find_one({"user_id": int(user_id), "chat_id": str(chat_id)})
            return bool(doc)
        except Exception as e:
            logger.error(f"Error checking join request: {e}")
            return False

    # Auto Approve Toggle
    async def get_auto_approve(self) -> bool:
        try:
            doc = await self.db.settings.find_one({"_id": "auto_approve"})
            if doc and "enabled" in doc:
                return bool(doc["enabled"])
            from config import FSUB_AUTO_APPROVE
            return FSUB_AUTO_APPROVE
        except Exception as e:
            logger.error(f"Error getting auto approve setting: {e}")
            return True

    async def set_auto_approve(self, enabled: bool):
        try:
            await self.db.settings.update_one(
                {"_id": "auto_approve"},
                {"$set": {"enabled": bool(enabled)}},
                upsert=True
            )
            logger.info(f"Auto-Approve set to: {enabled}")
        except Exception as e:
            logger.error(f"Error setting auto approve: {e}")

db = Database(DB_URI, DB_NAME)
