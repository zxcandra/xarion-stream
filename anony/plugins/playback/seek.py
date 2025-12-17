# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import anon, app, db, queue
from anony.helpers import admin_check


@app.on_message(filters.command(["seek"]) & filters.group & ~app.bl_users)
@admin_check
async def seek(_, message: types.Message):
    if not await db.get_call(message.chat.id):
        return await message.reply_text(
            "❌ <b>Tidak ada streaming</b>\n\n<blockquote>Gunakan /play untuk mulai memutar musik</blockquote>",
            parse_mode="html"
        )
    
    if len(message.command) < 2:
        return await message.reply_text(
            "⏩ <b>Penggunaan Seek</b>\n\n<blockquote><code>/seek [detik]</code>\n\nContoh: <code>/seek 60</code> (jump ke menit 1)</blockquote>",
            parse_mode="html"
        )
    
    try:
        seconds = int(message.command[1])
    except ValueError:
        return await message.reply_text(
            "❌ <b>Angka tidak valid</b>\n\n<blockquote>Masukkan angka detik yang valid</blockquote>",
            parse_mode="html"
        )
    
    media = queue.get_current(message.chat.id)
    if not media:
        return await message.reply_text(
            "❌ <b>Tidak ada media</b>\n\n<blockquote>Tidak ada lagu yang sedang diputar</blockquote>",
            parse_mode="html"
        )
    
    m = await message.reply_text("⏩ Seeking...")
    await anon.play_media(message.chat.id, m, media, seek_time=seconds)
    await m.edit_text(
        f"⏩ <b>Seek Berhasil</b>\n\n<blockquote>Jump ke detik ke-{seconds}</blockquote>",
        parse_mode="html"
    )
