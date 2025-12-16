# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from anony import app, config, lang


@app.on_message(filters.command(["donate"]))
@lang.language()
async def donate_command(_, message: types.Message):
    """Show donate information with inline button."""
    donate_text = message.lang["donate_text"]
    
    await message.reply_text(
        text=donate_text,
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=types.InlineKeyboardMarkup(
            [[types.InlineKeyboardButton(text="🎁 Dukung Kami", url=config.DONATE_QR_IMAGE)]]
        ),
        quote=True,
    )
