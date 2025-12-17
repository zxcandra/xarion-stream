# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio

from pyrogram import enums, filters, types

from anony import anon, app, boot, config


@app.on_message(filters.command(["ping"]) & filters.group & ~app.bl_users)
async def ping(_, message: types.Message):
    start = asyncio.get_event_loop().time()
    m = await message.reply_photo(
        photo=config.PING_IMG,
        caption="🏓 Pinging...",
    )
    end = asyncio.get_event_loop().time()
    uptime = int(end - boot)
    await m.edit_caption(
        f"🏓 <b>Pong!</b>\n\n<blockquote>💬 <b>Latency:</b> <code>{(end - start) * 1000:.3f}ms</code>\n📡 <b>Ping:</b> <code>{await anon.ping()}ms</code>\n⏱️ <b>Uptime:</b> <code>{uptime // 3600}h {(uptime % 3600) // 60}m</code></blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
