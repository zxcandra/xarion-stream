# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import anon, app, db
from anony.helpers import admin_check


@app.on_message(filters.command(["resume"]) & filters.group & ~app.bl_users)
@admin_check
async def resume(_, message: types.Message):
    if not await db.get_call(message.chat.id):
        return await message.reply_text(
            "❌ <b>Tidak ada streaming</b>\n\n<blockquote>Gunakan /play untuk mulai memutar musik</blockquote>",
            parse_mode="html"
        )
    if await db.playing(message.chat.id):
        return await message.reply_text(
            "▶️ <b>Streaming sedang berjalan</b>\n\n<blockquote>Gunakan /pause untuk menjeda</blockquote>",
            parse_mode="html"
        )
    await anon.resume(message.chat.id)
    await message.reply_text(
        f"▶️ <b>Streaming Dilanjutkan</b>\n\n<blockquote>{message.from_user.mention} melanjutkan streaming</blockquote>",
        parse_mode="html"
    )
