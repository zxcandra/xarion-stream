# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import re

from pyrogram import enums, types

from anony import app


class Utilities:
    def __init__(self):
        pass

    def format_eta(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d} min"
        else:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h}:{m:02d}:{s:02d} h"

    def format_size(self, bytes: int) -> str:
        if bytes >= 1024**3:
            return f"{bytes / 1024 ** 3:.2f} GB"
        elif bytes >= 1024**2:
            return f"{bytes / 1024 ** 2:.2f} MB"
        else:
            return f"{bytes / 1024:.2f} KB"

    def to_seconds(self, time: str) -> int:
        parts = [int(p) for p in time.strip().split(":")]
        return sum(value * 60**i for i, value in enumerate(reversed(parts)))

    def get_url(self, message_1: types.Message) -> str | None:
        link = None
        messages = [message_1]
        entities = [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK]

        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type in entities:
                        link = entity.url
                        break

            if message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type in entities:
                        link = entity.url
                        break

        if link:
            return link.split("&si")[0].split("?si")[0]
        return None

    async def extract_user(self, msg: types.Message) -> types.User | None:
        if msg.reply_to_message:
            return msg.reply_to_message.from_user

        if msg.entities:
            for e in msg.entities:
                if e.type == enums.MessageEntityType.TEXT_MENTION:
                    return e.user

        if msg.text:
            try:
                if m := re.search(r"@(\w{5,32})", msg.text):
                    return await app.get_users(m.group(0))
                if m := re.search(r"\b\d{6,15}\b", msg.text):
                    return await app.get_users(int(m.group(0)))
            except:
                pass

        return None

    async def play_log(
        self,
        m: types.Message,
        title: str,
        duration: str,
    ) -> None:
        if m.chat.id == app.logger:
            return
        _text = f"<u>{app.name} Log Play</u>\n\n<b>Chat:</b> <code>{m.chat.id}</code> | {m.chat.title}\n<b>User:</b> <code>{m.from_user.id}</code> | {m.from_user.mention}\n<b>Link pesan:</b> {m.link}\n\n<b>Judul:</b> {title}\n<b>Durasi:</b> {duration} menit"
        await app.send_message(chat_id=app.logger, text=_text)

    async def send_log(self, m: types.Message, chat: bool = False) -> None:
        if chat:
            user = m.from_user
            return await app.send_message(
                chat_id=app.logger,
                text=f"<u><b>Log Chat Baru</b></u>\n\n<b>Chat:</b> <code>{m.chat.id}</code> | {m.chat.title}\n<b>User:</b> <code>{user.id if user else 0}</code> | {user.mention if user else 'Anonymous'}",
            )

        await app.send_message(
            chat_id=app.logger,
            text=f"<u><b>Log Pengguna Baru</b></u>\n\n<b>ID:</b> <code>{m.from_user.id}</code>\n<b>Nama:</b> @{m.from_user.username} | {m.from_user.mention}",
        )

    async def auto_delete(self, message: types.Message, delay: int = None) -> None:
        """
        Auto delete a message after a specified delay.
        
        Args:
            message: The message to delete
            delay: Delay in seconds (uses config.AUTO_DELETE_TIME if None)
        """
        from anony import config
        import asyncio
        
        if delay is None:
            delay = config.AUTO_DELETE_TIME
        
        if delay > 0:
            await asyncio.sleep(delay)
            try:
                await message.delete()
            except:
                pass

    def format_number(self, num):
        """Format number to readable format (1.2K, 1.5M, etc)."""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)

    def get_medal(self, rank):
        """Get medal emoji for ranking."""
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        return medals.get(rank, f"{rank}.")

    def progress_bar(self, value, total, length=10):
        """Generate progress bar."""
        if total == 0:
            return "▱" * length
        filled = int((value / total) * length)
        return "▰" * filled + "▱" * (length - filled)
