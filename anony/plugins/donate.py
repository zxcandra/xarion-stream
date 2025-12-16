# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, config


@app.on_message(filters.command(["donate"]))
async def donate_command(_, message: types.Message):
    """Show donate information with QR code link."""
    donate_text = message.lang["donate_text"]
    
    try:
        await message.reply_photo(
            photo=config.DONATE_QR_IMAGE,
            caption=donate_text,
            quote=True,
        )
    except Exception:
        await message.reply_text(
            "❌ Gagal mengirim QR code. Pastikan URL gambar di config benar.",
            quote=True,
        )
