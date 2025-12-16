# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, config, lang


@app.on_message(filters.command(["donate"]))
@lang.language()
async def donate_command(_, message: types.Message):
    """Show donate information with QR code image."""
    donate_text = message.lang["donate_text"]
    
    await message.reply_photo(
        photo=config.DONATE_QR_IMAGE,
        caption=donate_text,
        quote=True,
    )
