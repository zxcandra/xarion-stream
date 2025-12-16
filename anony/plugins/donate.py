# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, config, lang


@app.on_message(filters.command(["donate"]))
@lang.language()
async def donate_command(_, message: types.Message):
    """Show donate information with QR code link."""
    donate_text = message.lang["donate_text"]
    
    try:
        # Download QR code locally first
        qr_path = "cache/donate_qr.png"
        from anony.helpers import thumb
        import os
        
        await thumb.save_thumb(qr_path, config.DONATE_QR_IMAGE)
        
        await message.reply_photo(
            photo=qr_path,
            caption=donate_text,
            quote=True,
        )
        
        # Clean up
        if os.path.exists(qr_path):
            os.remove(qr_path)
            
    except Exception as e:
        await message.reply_text(
            f"❌ Gagal mengirim QR code.\nError: `{e}`",
            quote=True,
        )
