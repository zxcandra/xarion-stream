# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from anony import app, config, db, queue
from anony.helpers import utils


@app.on_message(filters.command(["shuffle"]) & filters.group & ~app.bl_users)
async def shuffle_command(_, message: types.Message):
    """Shuffle the queue."""
    # Auto-delete command if enabled
    if config.AUTO_DELETE_COMMANDS:
        await utils.auto_delete(message)
    
    if not await db.get_call(message.chat.id):
        sent = await message.reply_text("❌ Tidak ada streaming yang sedang diputar.")
        await utils.auto_delete(sent)
        return
    
    items = queue.get_queue(message.chat.id)
    if len(items) <= 1:
        sent = await message.reply_text("❌ Antrian kosong atau hanya ada 1 lagu.")
        await utils.auto_delete(sent)
        return
    
    # Shuffle the queue
    success = queue.shuffle(message.chat.id)
    
    if success:
        sent = await message.reply_text(
            f"🔀 <b>Queue di-shuffle!</b>\n\n"
            f"<blockquote>{len(items) - 1} lagu telah diacak.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        sent = await message.reply_text("❌ Gagal meng-shuffle queue.")
    
    await utils.auto_delete(sent)
