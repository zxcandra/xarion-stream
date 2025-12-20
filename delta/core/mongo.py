# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from random import randint
from time import time

from motor.motor_asyncio import AsyncIOMotorClient

from delta import config, logger, userbot


class MongoDB:
    def __init__(self):
        """
        Initialize the MongoDB connection.
        """
        self.mongo = AsyncIOMotorClient(config.MONGO_URL, serverSelectionTimeoutMS=12500)
        self.db = self.mongo.Anon

        self.admin_list = {}
        self.active_callsdb = self.db.active_calls
        self.admin_play = []
        self.blacklisted = []
        self.cmd_delete = []
        self.notified = []
        self.cache = self.db.cache
        self.logger = False

        self.assistant = {}
        self.assistantdb = self.db.assistant

        self.auth = {}
        self.authdb = self.db.auth

        self.chats = []
        self.chatsdb = self.db.chats



        self.users = []
        self.usersdb = self.db.users

        self.pm_warns = {}
        self.pm_warnsdb = self.db.pm_warns

        self.pm_messages = {}
        self.pm_messagesdb = self.db.pm_messages

        self.statsdb = self.db.stats
        self.queriesdb = self.db.queries
        self.dailydb = self.db.daily_stats
        self.hourlydb = self.db.hourly_stats

    async def connect(self) -> None:
        """Check if we can connect to the database.

        Raises:
            SystemExit: If the connection to the database fails.
        """
        try:
            start = time()
            await self.mongo.admin.command("ping")
            logger.info(f"Database connection successful. ({time() - start:.2f}s)")
            await self.load_cache()
        except Exception as e:
            raise SystemExit(f"Database connection failed: {type(e).__name__}") from e

    async def close(self) -> None:
        """Close the connection to the database."""
        await self.mongo.close()
        logger.info("Database connection closed.")

    # CACHE
    # CACHE
    async def get_call(self, chat_id: int) -> bool:
        doc = await self.active_callsdb.find_one({"_id": chat_id})
        return bool(doc)

    async def add_call(self, chat_id: int) -> None:
        await self.active_callsdb.update_one(
            {"_id": chat_id},
            {"$set": {"playing": 1}},
            upsert=True
        )

    async def remove_call(self, chat_id: int) -> None:
        await self.active_callsdb.delete_one({"_id": chat_id})

    async def playing(self, chat_id: int, paused: bool = None) -> bool | None:
        if paused is not None:
            await self.active_callsdb.update_one(
                {"_id": chat_id},
                {"$set": {"playing": int(not paused)}},
                upsert=True
            )
        doc = await self.active_callsdb.find_one({"_id": chat_id})
        return bool(doc and doc.get("playing"))

    async def get_active_calls(self) -> list:
        """Get list of active chat IDs."""
        return [doc["_id"] async for doc in self.active_callsdb.find()]

    async def get_admins(self, chat_id: int, reload: bool = False) -> list[int]:
        from delta.helpers._admins import reload_admins

        if chat_id not in self.admin_list or reload:
            self.admin_list[chat_id] = await reload_admins(chat_id)
        return self.admin_list[chat_id]

    # AUTH METHODS
    async def _get_auth(self, chat_id: int) -> set[int]:
        if chat_id not in self.auth:
            doc = await self.authdb.find_one({"_id": chat_id}) or {}
            self.auth[chat_id] = set(doc.get("user_ids", []))
        return self.auth[chat_id]

    async def is_auth(self, chat_id: int, user_id: int) -> bool:
        return user_id in await self._get_auth(chat_id)

    async def add_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id not in users:
            users.add(user_id)
            await self.authdb.update_one(
                {"_id": chat_id}, {"$addToSet": {"user_ids": user_id}}, upsert=True
            )

    async def rm_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id in users:
            users.discard(user_id)
            await self.authdb.update_one(
                {"_id": chat_id}, {"$pull": {"user_ids": user_id}}
            )

    # ASSISTANT METHODS
    async def set_assistant(self, chat_id: int) -> int:
        num = randint(1, len(userbot.clients))
        await self.assistantdb.update_one(
            {"_id": chat_id},
            {"$set": {"num": num}},
            upsert=True,
        )
        self.assistant[chat_id] = num
        return num

    async def get_assistant(self, chat_id: int):
        from delta import anon

        if chat_id not in self.assistant:
            doc = await self.assistantdb.find_one({"_id": chat_id})
            num = doc["num"] if doc else await self.set_assistant(chat_id)
            self.assistant[chat_id] = num

        return anon.clients[self.assistant[chat_id] - 1]

    async def get_client(self, chat_id: int):
        if chat_id not in self.assistant:
            await self.get_assistant(chat_id)
        return {1: userbot.one, 2: userbot.two, 3: userbot.three}.get(
            self.assistant[chat_id]
        )

    # BLACKLIST METHODS
    async def add_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            self.blacklisted.append(chat_id)
            return await self.cache.update_one(
                {"_id": "bl_chats"}, {"$addToSet": {"chat_ids": chat_id}}, upsert=True
            )
        await self.cache.update_one(
            {"_id": "bl_users"}, {"$addToSet": {"user_ids": chat_id}}, upsert=True
        )

    async def del_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            self.blacklisted.remove(chat_id)
            return await self.cache.update_one(
                {"_id": "bl_chats"},
                {"$pull": {"chat_ids": chat_id}},
            )
        await self.cache.update_one(
            {"_id": "bl_users"},
            {"$pull": {"user_ids": chat_id}},
        )

    async def get_blacklisted(self, chat: bool = False) -> list[int]:
        if chat:
            if not self.blacklisted:
                doc = await self.cache.find_one({"_id": "bl_chats"})
                self.blacklisted.extend(doc.get("chat_ids", []) if doc else [])
            return self.blacklisted
        doc = await self.cache.find_one({"_id": "bl_users"})
        return doc.get("user_ids", []) if doc else []

    # CHAT METHODS
    async def is_chat(self, chat_id: int) -> bool:
        return chat_id in self.chats

    async def add_chat(self, chat_id: int) -> None:
        if not await self.is_chat(chat_id):
            self.chats.append(chat_id)
            await self.chatsdb.insert_one({"_id": chat_id})

    async def rm_chat(self, chat_id: int) -> None:
        if await self.is_chat(chat_id):
            self.chats.remove(chat_id)
            await self.chatsdb.delete_one({"_id": chat_id})

    async def get_chats(self) -> list:
        if not self.chats:
            self.chats.extend([chat["_id"] async for chat in self.chatsdb.find()])
        return self.chats

    # COMMAND DELETE
    async def get_cmd_delete(self, chat_id: int) -> bool:
        if chat_id not in self.cmd_delete:
            doc = await self.chatsdb.find_one({"_id": chat_id})
            if doc and doc.get("cmd_delete"):
                self.cmd_delete.append(chat_id)
        return chat_id in self.cmd_delete

    async def set_cmd_delete(self, chat_id: int, delete: bool = False) -> None:
        if delete:
            self.cmd_delete.append(chat_id)
        else:
            self.cmd_delete.remove(chat_id)
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"cmd_delete": delete}},
            upsert=True,
        )



    # LOGGER METHODS
    async def is_logger(self) -> bool:
        return self.logger

    async def get_logger(self) -> bool:
        doc = await self.cache.find_one({"_id": "logger"})
        if doc:
            self.logger = doc["status"]
        return self.logger

    async def set_logger(self, status: bool) -> None:
        self.logger = status
        await self.cache.update_one(
            {"_id": "logger"},
            {"$set": {"status": status}},
            upsert=True,
        )

    # PLAY MODE METHODS
    async def get_play_mode(self, chat_id: int) -> bool:
        if chat_id not in self.admin_play:
            doc = await self.chatsdb.find_one({"_id": chat_id})
            if doc and doc.get("admin_play"):
                self.admin_play.append(chat_id)
        return chat_id in self.admin_play

    async def set_play_mode(self, chat_id: int, remove: bool = False) -> None:
        if remove and chat_id in self.admin_play:
            self.admin_play.remove(chat_id)
        else:
            self.admin_play.append(chat_id)
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"admin_play": not remove}},
            upsert=True,
        )

    # LOOP MODE METHODS
    async def get_loop_mode(self, chat_id: int) -> str:
        """Get loop mode for a chat. Returns 'normal', 'loop_all', or 'loop_one'."""
        doc = await self.chatsdb.find_one({"_id": chat_id})
        if doc and "loop_mode" in doc:
            return doc["loop_mode"]
        return "normal"

    async def set_loop_mode(self, chat_id: int, mode: str) -> None:
        """Set loop mode for a chat. Mode should be 'normal', 'loop_all', or 'loop_one'."""
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"loop_mode": mode}},
            upsert=True,
        )

    # VIDEO MODE METHODS
    async def get_video_mode(self, chat_id: int) -> bool:
        """Get video mode for a chat. Returns True if video enabled, False for audio only."""
        doc = await self.chatsdb.find_one({"_id": chat_id})
        if doc and "video_mode" in doc:
            return doc["video_mode"]
        return True  # Default: video enabled

    async def set_video_mode(self, chat_id: int, enabled: bool) -> None:
        """Set video mode for a chat."""
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"video_mode": enabled}},
            upsert=True,
        )

    # VIDEO QUALITY METHODS
    async def get_video_quality(self, chat_id: int) -> str:
        """Get video quality for a chat. Returns '360p', '480p', '720p', or '1080p'."""
        doc = await self.chatsdb.find_one({"_id": chat_id})
        if doc and "video_quality" in doc:
            return doc["video_quality"]
        return "720p"  # Default quality

    async def set_video_quality(self, chat_id: int, quality: str) -> None:
        """Set video quality for a chat."""
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"video_quality": quality}},
            upsert=True,
        )

    # DRAMA MODE METHODS
    async def get_drama_mode(self, chat_id: int) -> bool:
        """Get drama mode for a chat. Returns True if admin only, False if everyone."""
        doc = await self.chatsdb.find_one({"_id": chat_id})
        if doc and "drama_mode" in doc:
            return doc["drama_mode"]
        return False  # Default: allowed for everyone

    async def set_drama_mode(self, chat_id: int, admin_only: bool) -> None:
        """Set drama mode for a chat."""
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"drama_mode": admin_only}},
            upsert=True,
        )

    # SUDO METHODS
    async def add_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"}, {"$addToSet": {"user_ids": user_id}}, upsert=True
        )

    async def del_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"}, {"$pull": {"user_ids": user_id}}
        )

    async def get_sudoers(self) -> list[int]:
        doc = await self.cache.find_one({"_id": "sudoers"})
        return doc.get("user_ids", []) if doc else []

    # USER METHODS
    async def is_user(self, user_id: int) -> bool:
        return user_id in self.users

    async def add_user(self, user_id: int) -> None:
        if not await self.is_user(user_id):
            self.users.append(user_id)
            await self.usersdb.insert_one({"_id": user_id})

    async def rm_user(self, user_id: int) -> None:
        if await self.is_user(user_id):
            self.users.remove(user_id)
            await self.usersdb.delete_one({"_id": user_id})

    async def get_users(self) -> list:
        if not self.users:
            self.users.extend([user["_id"] async for user in self.usersdb.find()])
        return self.users

    # PM WARNINGS METHODS
    async def get_pm_warns(self, user_id: int) -> int:
        """Get number of PM warnings for a user."""
        if user_id not in self.pm_warns:
            doc = await self.pm_warnsdb.find_one({"_id": user_id})
            self.pm_warns[user_id] = doc.get("warns", 0) if doc else 0
        return self.pm_warns[user_id]

    async def add_pm_warn(self, user_id: int) -> int:
        """Add a PM warning to a user and return new count."""
        current = await self.get_pm_warns(user_id)
        new_count = current + 1
        self.pm_warns[user_id] = new_count
        await self.pm_warnsdb.update_one(
            {"_id": user_id},
            {"$set": {"warns": new_count}},
            upsert=True,
        )
        return new_count

    async def clear_pm_warns(self, user_id: int) -> None:
        """Clear PM warnings for a user."""
        self.pm_warns.pop(user_id, None)
        await self.pm_warnsdb.delete_one({"_id": user_id})

    async def is_pm_blocked(self, user_id: int) -> bool:
        """Check if user is blocked from PM."""
        warns = await self.get_pm_warns(user_id)
        from delta import config
        return warns >= config.PM_WARN_COUNT

    # PM CUSTOM MESSAGES METHODS
    async def get_pm_messages(self) -> dict:
        """Get custom PM messages."""
        if not self.pm_messages:
            doc = await self.pm_messagesdb.find_one({"_id": "custom_messages"})
            if doc:
                self.pm_messages = {
                    "warn": doc.get("warn"),
                    "block": doc.get("block")
                }
            else:
                self.pm_messages = {"warn": None, "block": None}
        return self.pm_messages

    async def set_pm_warn_msg(self, message: str) -> None:
        """Set custom PM warning message."""
        self.pm_messages["warn"] = message
        await self.pm_messagesdb.update_one(
            {"_id": "custom_messages"},
            {"$set": {"warn": message}},
            upsert=True
        )

    async def set_pm_block_msg(self, message: str) -> None:
        """Set custom PM block message."""
        self.pm_messages["block"] = message
        await self.pm_messagesdb.update_one(
            {"_id": "custom_messages"},
            {"$set": {"block": message}},
            upsert=True
        )

    async def clear_pm_messages(self) -> None:
        """Clear custom PM messages (reset to default)."""
        self.pm_messages = {"warn": None, "block": None}
        await self.pm_messagesdb.delete_one({"_id": "custom_messages"})

    # STATS TRACKING METHODS
    async def add_stats(self, track_id: str, title: str, duration: str, user_id: int, chat_id: int, thumbnail: str = None, stream_type: str = "music") -> None:
        """Add or update play statistics."""
        update_data = {
            "title": title, 
            "duration": duration,
            "stream_type": stream_type
        }
        if thumbnail:
            update_data["thumbnail"] = thumbnail

        await self.statsdb.update_one(
            {"_id": track_id},
            {
                "$set": update_data,
                "$inc": {
                    "count": 1,
                    f"users.{user_id}": 1,
                    f"chats.{chat_id}": 1
                }
            },
            upsert=True
        )
        
        # Add to group-specific user stats
        await self.db.group_stats.update_one(
            {"_id": chat_id},
            {"$inc": {f"users.{user_id}": 1}},
            upsert=True
        )

        # Add to daily stats
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        await self.dailydb.update_one(
            {"_id": today},
            {"$inc": {"count": 1}},
            upsert=True
        )

        # Add to hourly stats (Peak Hours)
        current_hour = datetime.now().hour # 0-23
        await self.hourlydb.update_one(
            {"_id": today},
            {"$inc": {f"hours.{current_hour}": 1}},
            upsert=True
        )

    async def get_global_tops(self, limit: int = 10) -> dict:
        """Get top tracks globally."""
        # Filter out Live streams and Unknown duration
        query = {
            "duration": {
                "$nin": ["Live", "Unknown"],
                "$not": {"$regex": "^Stream|Live$", "$options": "i"}
            },
            "thumbnail": {"$exists": True, "$ne": None}
        }
        cursor = self.statsdb.find(query).sort("count", -1).limit(limit)
        results = {}
        async for doc in cursor:
            results[doc["_id"]] = {
                "spot": doc.get("count", 0),
                "title": doc.get("title", "Unknown"),
                "duration": doc.get("duration", "0:00"),
                "thumbnail": doc.get("thumbnail", "")
            }
        return results

    async def get_top_users(self, limit: int = 10) -> dict:
        """Get most active users globally."""
        pipeline = [
            {"$project": {"users": {"$objectToArray": "$users"}}},
            {"$unwind": "$users"},
            {"$group": {"_id": "$users.k", "count": {"$sum": "$users.v"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        cursor = self.statsdb.aggregate(pipeline)
        results = {}
        async for doc in cursor:
            try:
                user_id = int(doc["_id"])
                results[user_id] = doc["count"]
            except (ValueError, TypeError):
                continue
        return results

    async def get_top_chats(self, limit: int = 10) -> dict:
        """Get most active groups globally."""
        pipeline = [
            {"$project": {"chats": {"$objectToArray": "$chats"}}},
            {"$unwind": "$chats"},
            {"$group": {"_id": "$chats.k", "count": {"$sum": "$chats.v"}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        results = {}
        cursor = self.statsdb.aggregate(pipeline)
        docs = await cursor.to_list(length=None)
        for doc in docs:
            try:
                chat_id = int(doc["_id"])
                results[chat_id] = doc["count"]
            except (ValueError, TypeError):
                continue
        return results

    async def get_group_stats(self, chat_id: int, limit: int = 10) -> dict:
        """Get top tracks for a specific group."""
        query = {
            f"chats.{chat_id}": {"$exists": True},
            "duration": {
                "$nin": ["Live", "Unknown"],
                "$not": {"$regex": "^Stream|Live$", "$options": "i"}
            },
            "thumbnail": {"$exists": True, "$ne": None}
        }
        cursor = self.statsdb.find(query).sort(f"chats.{chat_id}", -1).limit(limit)
        results = {}
        async for doc in cursor:
            chats = doc.get("chats", {})
            count = chats.get(str(chat_id), 0)
            if count > 0:
                results[doc["_id"]] = {
                    "spot": count,
                    "title": doc.get("title", "Unknown"),
                    "duration": doc.get("duration", "0:00")
                }
        return results

    async def get_group_top_users(self, chat_id: int, limit: int = 10) -> dict:
        """Get top users for a specific group."""
        doc = await self.db.group_stats.find_one({"_id": chat_id})
        if not doc or "users" not in doc:
            return {}
        
        users = doc["users"]
        # Sort by count desc and take top limit
        sorted_users = dict(sorted(users.items(), key=lambda item: item[1], reverse=True)[:limit])
        return sorted_users

    async def increment_queries(self) -> None:
        """Increment total queries counter."""
        await self.queriesdb.update_one(
            {"_id": "total_queries"},
            {"$inc": {"count": 1}},
            upsert=True
        )

    async def get_queries(self) -> int:
        """Get total queries count."""
        doc = await self.queriesdb.find_one({"_id": "total_queries"})
        return doc.get("count", 0) if doc else 0

    async def get_daily_play_count(self, days: int = 7) -> list:
        """Get daily play counts for the last N days."""
        from datetime import datetime, timedelta
        
        results = []
        today = datetime.now()
        
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            doc = await self.dailydb.find_one({"_id": date})
            count = doc.get("count", 0) if doc else 0
            results.append({
                "date": date,
                "play_count": count
            })
            
        return results[::-1]  # Return chronologically (oldest first)

    async def get_peak_hours(self, days: int = 7) -> list:
        """Get aggregated play counts per hour (0-23) for the last N days."""
        from datetime import datetime, timedelta
        
        # Initialize 24 hours with 0
        hourly_counts = [0] * 24
        
        today = datetime.now()
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            doc = await self.hourlydb.find_one({"_id": date})
            if doc and "hours" in doc:
                hours_data = doc["hours"]
                for hour, count in hours_data.items():
                    try:
                        h = int(hour)
                        if 0 <= h < 24:
                            hourly_counts[h] += count
                    except:
                        pass
        
        return hourly_counts

    # USER PLAYLIST METHODS
    async def add_to_playlist(self, user_id: int, track_id: str, title: str, duration: str, url: str) -> bool:
        """Add a track to user's playlist. Returns True if added, False if already exists."""
        # Check if track already in playlist
        existing = await self.usersdb.find_one({
            "_id": user_id,
            "playlist.track_id": track_id
        })
        if existing:
            return False
        
        await self.usersdb.update_one(
            {"_id": user_id},
            {"$push": {"playlist": {
                "track_id": track_id,
                "title": title,
                "duration": duration,
                "url": url
            }}},
            upsert=True
        )
        return True

    async def get_playlist(self, user_id: int) -> list:
        """Get user's playlist."""
        doc = await self.usersdb.find_one({"_id": user_id})
        return doc.get("playlist", []) if doc else []

    async def remove_from_playlist(self, user_id: int, track_id: str) -> bool:
        """Remove a track from user's playlist."""
        result = await self.usersdb.update_one(
            {"_id": user_id},
            {"$pull": {"playlist": {"track_id": track_id}}}
        )
        return result.modified_count > 0

    async def clear_playlist(self, user_id: int) -> None:
        """Clear user's entire playlist."""
        await self.usersdb.update_one(
            {"_id": user_id},
            {"$set": {"playlist": []}}
        )


    async def migrate_coll(self) -> None:
        from bson import ObjectId
        logger.info("Migrating users and chats from old collections...")

        musers, mchats, done = [], [], []
        ulist = [user async for user in self.db.tgusersdb.find()]
        ulist.extend([user async for user in self.usersdb.find()])

        for user in ulist:
            if isinstance(user.get("_id"), ObjectId):
                user_id = int(user["user_id"])
                if user_id in done:
                    continue
                done.append(user_id)
                musers.append(user)
            else:
                user_id = int(user["_id"])
                if user_id in done:
                    continue
                done.append(user_id)
                musers.append({"_id": user_id})
        await self.usersdb.drop()
        await self.db.tgusersdb.drop()
        if musers:
            await self.usersdb.insert_many(musers)

        async for chat in self.chatsdb.find():
            if isinstance(chat.get("_id"), ObjectId):
                chat_id = int(chat["chat_id"])
                if chat_id in mchats:
                    continue
                done.append(chat_id)
                mchats.append(chat)
            else:
                chat_id = int(chat["_id"])
                if chat_id in done:
                    continue
                done.append(chat_id)
                mchats.append({"_id": chat_id})
        await self.chatsdb.drop()
        if mchats:
            await self.chatsdb.insert_many(mchats)

        await self.cache.insert_one({"_id": "migrated"})
        logger.info("Migration completed.")

    async def load_cache(self) -> None:
        doc = await self.cache.find_one({"_id": "migrated"})
        if not doc:
            await self.migrate_coll()

        await self.get_chats()
        await self.get_users()
        await self.get_blacklisted(True)
        await self.get_logger()
        logger.info("Database cache loaded.")
