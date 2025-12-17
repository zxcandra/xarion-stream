# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from anony import app, db


@app.on_message(filters.command(["blacklist", "unblacklist"]) & app.sudoers)
async def blacklist_cmd(_, message: types.Message):
    """Blacklist/unblacklist a user or chat."""
    
    if len(message.command) < 2:
        return await message.reply_text(
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote>/blacklist [chat_id|user_id]</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    try:
        target_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(
            "❌ <b>ID Tidak Valid</b>\n\n<blockquote>Hanya chat ID dan user ID yang didukung</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    is_blacklist = message.command[0] == "blacklist"
    
    if is_blacklist:
        if target_id in app.bl_users or target_id in db.blacklisted:
            return await message.reply_text(
                "⚠️ <b>Sudah Blacklist</b>\n\n<blockquote>Target sudah ada di daftar hitam</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        await db.add_blacklist(target_id)
        app.bl_users.append(target_id)
        await message.reply_text(
            "🚫 <b>Blacklist Berhasil</b>\n\n<blockquote>Target telah ditambahkan ke daftar hitam</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    else:
        if target_id not in app.bl_users and target_id not in db.blacklisted:
            return await message.reply_text(
                "⚠️ <b>Tidak Blacklist</b>\n\n<blockquote>Target tidak ada di daftar hitam</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        await db.del_blacklist(target_id)
        if target_id in app.bl_users:
            app.bl_users.remove(target_id)
        await message.reply_text(
            "✅ <b>Unblacklist Berhasil</b>\n\n<blockquote>Target telah dihapus dari daftar hitam</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
