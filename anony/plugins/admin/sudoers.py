# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from anony import app, db
from anony.helpers import utils


@app.on_message(filters.command(["addsudo"]) & filters.user(app.owner))
async def add_sudo(_, message: types.Message):
    """Add user to sudoers list."""
    
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote>Reply ke user atau berikan user ID/username</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    user = await utils.extract_user(message)
    if not user:
        return await message.reply_text(
            "❌ <b>User Tidak Ditemukan</b>\n\n<blockquote>Pastikan user ID atau username valid</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    if user.id in app.sudoers:
        return await message.reply_text(
            f"ℹ️ <b>Sudah Sudoer</b>\n\n<blockquote>{user.mention} sudah ada dalam daftar sudoers</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    app.sudoers.append(user.id)
    await db.add_sudo(user.id)
    await message.reply_text(
        f"✅ <b>Sudoer Ditambahkan</b>\n\n<blockquote>{user.mention} telah ditambahkan ke daftar sudoers</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )


@app.on_message(filters.command(["rmsudo", "delsudo"]) & filters.user(app.owner))
async def remove_sudo(_, message: types.Message):
    """Remove user from sudoers list."""
    
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote>Reply ke user atau berikan user ID/username</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    user = await utils.extract_user(message)
    if not user:
        return await message.reply_text(
            "❌ <b>User Tidak Ditemukan</b>\n\n<blockquote>Pastikan user ID atau username valid</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    if user.id not in app.sudoers:
        return await message.reply_text(
            f"ℹ️ <b>Bukan Sudoer</b>\n\n<blockquote>{user.mention} tidak ada dalam daftar sudoers</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    app.sudoers.remove(user.id)
    await db.del_sudo(user.id)
    await message.reply_text(
        f"✅ <b>Sudoer Dihapus</b>\n\n<blockquote>{user.mention} telah dihapus dari daftar sudoers</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
