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
        sent = await message.reply_text(
            "❌ <b>Tidak ada streaming</b>\n\n<blockquote>Gunakan /play untuk mulai memutar musik</blockquote>",
            parse_mode="html"
        )
        await utils.auto_delete(sent)
        return
    
    items = queue.get_queue(message.chat.id)
    if len(items) <= 1:
        sent = await message.reply_text(
            "❌ <b>Antrian terlalu sedikit</b>\n\n<blockquote>Minimal harus ada 2 lagu untuk di-shuffle</blockquote>",
            parse_mode="html"
        )
        await utils.auto_delete(sent)
        return
    
    # Shuffle the queue
    success = queue.shuffle(message.chat.id)
    
    if success:
        sent = await message.reply_text(
            f"🔀 <b>Queue Di-Shuffle!</b>\n\n<blockquote>{len(items) - 1} lagu telah diacak</blockquote>",
            parse_mode="html"
        )
    else:
        sent = await message.reply_text(
            "❌ <b>Gagal shuffle</b>\n\n<blockquote>Terjadi kesalahan saat meng-shuffle queue</blockquote>",
            parse_mode="html"
        )
    
    await utils.auto_delete(sent)
