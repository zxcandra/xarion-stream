# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
from pyrogram import enums, filters, types

from anony import app, config, db
from anony.helpers import buttons, utils


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
async def _help(_, m: types.Message):
    help_text = f"📚 <b>Menu Bantuan {app.name}</b>\n\n"
    help_text += "<blockquote>"
    help_text += "Klik kategori di bawah untuk melihat perintah yang tersedia.\n\n"
    help_text += "💡 <b>Tips:</b> Semua perintah dimulai dengan / (garis miring)"
    help_text += "</blockquote>"
    
    await m.reply_text(
        text=help_text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons.help_markup({}),
        quote=True,
    )


@app.on_message(filters.command(["start"]))
async def start(_, message: types.Message):
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(
            "❌ <b>Akses Ditolak</b>\n\n<blockquote>Maaf, Anda tidak dapat menggunakan bot ini.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE
    _text = (
        f"👋 <b>Halo {message.from_user.first_name}!</b>\n\n🎵 Selamat datang di <b>{app.name}</b>!\n\n<blockquote>🎶 Bot pemutar musik dengan fitur-fitur keren dan berguna untuk grup Telegram Anda!\n🎧 Streaming musik berkualitas tinggi\n📝 Playlist dan queue management\n⚡ Fast & Responsive</blockquote>\n\n<b><i>Klik tombol bantuan untuk info lebih lanjut.</i></b>"
        if private
        else f"👋 <b>Halo semuanya!</b>\n\n<blockquote>🎵 <b>{app.name}</b> sudah aktif dan siap memutar musik!\n🎶 Ketik /help untuk melihat semua perintah yang tersedia.</blockquote>\n\n<b>Fitur Utama:</b>\n• 🎧 Streaming musik berkualitas\n• 📝 Playlist & Queue\n• ⚡ Cepat & Stabil"
    )

    key = buttons.start_key({}, private)
    await message.reply_photo(
        photo=config.START_IMG,
        caption=_text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=key,
        quote=not private,
    )

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        await db.add_user(message.from_user.id)
    else:
        if await db.is_chat(message.chat.id):
            return
        await utils.send_log(message, True)
        await db.add_chat(message.chat.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
async def settings(_, message: types.Message):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    
    await message.reply_text(
        text=f"⚙️ <b>Pengaturan {message.chat.title}</b>\n\n<blockquote>Klik tombol di bawah untuk mengubah pengaturan chat ini.</blockquote>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons.settings_markup(
            {}, admin_only, cmd_delete, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
async def _new_member(_, message: types.Message):
    await asyncio.sleep(3)
    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await utils.send_log(message, True)
            await db.add_chat(message.chat.id)
