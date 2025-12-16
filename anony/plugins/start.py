# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
from pyrogram import enums, filters, types

from anony import app, config, db
from anony.helpers import buttons, utils


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
async def _help(_, m: types.Message):
    await m.reply_text(
        text="ℹ️ **Menu Bantuan**\n\nPilih kategori di bawah untuk melihat perintah yang tersedia:",
        reply_markup=buttons.help_markup({}),
        quote=True,
    )


@app.on_message(filters.command(["start"]))
async def start(_, message: types.Message):
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text("❌ Anda telah diblokir dari menggunakan bot ini.")

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE
    _text = (
        f"👋 **Halo {message.from_user.first_name}!**\n\n🎵 Selamat datang di **{app.name}**!\n\n> 🎶 Bot pemutar musik dengan fitur-fitur keren dan berguna untuk grup Telegram Anda!\n> 🎧 Streaming musik berkualitas tinggi\n> 📝 Playlist dan queue management\n> ⚡ Fast & Responsive\n\n<b><i>Klik tombol bantuan untuk info lebih lanjut.</i></b>"
        if private
        else f"👋 **Halo semuanya!**\n\n> 🎵 **{app.name}** sudah aktif dan siap memutar musik!\n> 🎶 Ketik /help untuk melihat semua perintah yang tersedia.\n\n**Fitur Utama:**\n• 🎧 Streaming musik berkualitas\n• 📝 Playlist & Queue\n• ⚡ Cepat & Stabil"
    )

    key = buttons.start_key({}, private)
    await message.reply_photo(
        photo=config.START_IMG,
        caption=_text,
        parse_mode=enums.ParseMode.MARKDOWN,
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
    _language = await db.get_lang(message.chat.id)
    
    await message.reply_text(
        text=f"<u><b>Pengaturan {message.chat.title}</b></u>\n\nKlik tombol di bawah untuk mengubah pengaturan chat ini.",
        reply_markup=buttons.settings_markup(
            {}, admin_only, cmd_delete, _language, message.chat.id
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
