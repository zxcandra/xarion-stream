# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import anon, app, db
from anony.helpers import admin_check


@app.on_message(filters.command(["pause"]) & filters.group & ~app.bl_users)
@admin_check
async def pause(_, message: types.Message):
    if not await db.get_call(message.chat.id):
        return await message.reply_text(
            "❌ <b>Tidak ada streaming</b>\n\n<blockquote>Gunakan /play untuk mulai memutar musik</blockquote>",
            parse_mode="html"
        )
    if not await db.playing(message.chat.id):
        return await message.reply_text(
            "⏸ <b>Streaming sudah dijeda</b>\n\n<blockquote>Gunakan /resume untuk melanjutkan</blockquote>",
            parse_mode="html"
        )
    await anon.pause(message.chat.id)
    await message.reply_text(
        f"⏸ <b>Streaming Dijeda</b>\n\n<blockquote>{message.from_user.mention} menjeda streaming</blockquote>",
        parse_mode="html"
    )
