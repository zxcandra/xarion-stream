# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from anony import app, db
from anony.helpers import admin_check, utils


@app.on_message(filters.command(["auth"]) & filters.group & ~app.bl_users)
@admin_check
async def auth_user(_, message: types.Message):
    """Add user to authorized users list."""
    
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote>Reply ke user atau berikan user ID/username</blockquote>",
            parse_mode="html"
        )
    
    user = await utils.extract_user(message)
    if not user:
        return await message.reply_text(
            "❌ <b>User Tidak Ditemukan</b>\n\n<blockquote>Pastikan user ID atau username valid</blockquote>",
            parse_mode="html"
        )
    
    # Check if user is admin
    admins = await db.get_admins(message.chat.id)
    if user.id in admins:
        return await message.reply_text(
            f"⚠️ <b>Sudah Admin</b>\n\n<blockquote>{user.mention} adalah admin dan otomatis terotorisasi</blockquote>",
            parse_mode="html"
        )
    
    if await db.is_auth(message.chat.id, user.id):
        return await message.reply_text(
            f"ℹ️ <b>Sudah Terotorisasi</b>\n\n<blockquote>{user.mention} sudah ada dalam daftar authorized</blockquote>",
            parse_mode="html"
        )
    
    await db.add_auth(message.chat.id, user.id)
    await message.reply_text(
        f"✅ <b>User Diotorisasi</b>\n\n<blockquote>{user.mention} telah ditambahkan ke daftar authorized</blockquote>",
        parse_mode="html"
    )


@app.on_message(filters.command(["unauth"]) & filters.group & ~app.bl_users)
@admin_check
async def unauth_user(_, message: types.Message):
    """Remove user from authorized users list."""
    
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote>Reply ke user atau berikan user ID/username</blockquote>",
            parse_mode="html"
        )
    
    user = await utils.extract_user(message)
    if not user:
        return await message.reply_text(
            "❌ <b>User Tidak Ditemukan</b>\n\n<blockquote>Pastikan user ID atau username valid</blockquote>",
            parse_mode="html"
        )
    
    if not await db.is_auth(message.chat.id, user.id):
        return await message.reply_text(
            f"ℹ️ <b>Belum Terotorisasi</b>\n\n<blockquote>{user.mention} tidak ada dalam daftar authorized</blockquote>",
            parse_mode="html"
        )
    
    await db.rm_auth(message.chat.id, user.id)
    await message.reply_text(
        f"✅ <b>Otorisasi Dihapus</b>\n\n<blockquote>{user.mention} telah dihapus dari daftar authorized</blockquote>",
        parse_mode="html"
    )
