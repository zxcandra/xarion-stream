# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import re

from pyrogram import enums, filters, types

from anony import anon, app, db, queue, tg, yt
from anony.helpers import admin_check, buttons, can_manage_vc


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
async def cancel_dl(_, query: types.CallbackQuery):
    await query.answer()
    await tg.cancel(query)


@app.on_callback_query(filters.regex("controls") & ~app.bl_users)
@can_manage_vc
async def _controls(_, query: types.CallbackQuery):
    args = query.data.split()
    action, chat_id = args[1], int(args[2])
    q_action = len(args) == 4
    user = query.from_user.mention

    if not await db.get_call(chat_id):
        return await query.answer("Tidak ada streaming yang sedang diputar.", show_alert=True)

    if action == "status":
        return await query.answer()
    await query.answer("Memproses...", show_alert=True)

    if action == "pause":
        if not await db.playing(chat_id):
            return await query.answer(
                "Streaming sudah dijeda!", show_alert=True
            )
        await anon.pause(chat_id)
        if q_action:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, "Streaming dijeda", False)
            )
        status = "Streaming dijeda"
        reply = f"{user} menjeda streaming."

    elif action == "resume":
        if await db.playing(chat_id):
            return await query.answer("Streaming tidak dijeda!", show_alert=True)
        await anon.resume(chat_id)
        if q_action:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, "Sedang memutar", True)
            )
        reply = f"{user} melanjutkan streaming."

    elif action == "skip":
        await anon.play_next(chat_id)
        status = "Streaming dilewati"
        reply = f"{user} melewati streaming."

    elif action == "force":
        pos, media = queue.check_item(chat_id, args[3])
        if not media or pos == -1:
            return await query.edit_message_text("Lagu ini telah kadaluarsa dari antrian.")

        m_id = queue.get_current(chat_id).message_id
        queue.force_add(chat_id, media, remove=pos)
        try:
            await app.delete_messages(
                chat_id=chat_id, message_ids=[m_id, media.message_id], revoke=True
            )
            media.message_id = None
        except:
            pass

        msg = await app.send_message(chat_id=chat_id, text="Memutar lagu selanjutnya...")
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
        media.message_id = msg.id
        return await anon.play_media(chat_id, msg, media)

    elif action == "replay":
        media = queue.get_current(chat_id)
        media.user = user
        await anon.replay(chat_id)
        status = "Streaming diputar ulang"
        reply = f"{user} memutar ulang streaming."


    elif action == "shuffle":
        # Shuffle the queue
        success = queue.shuffle(chat_id)
        if success:
            items = queue.get_queue(chat_id)
            return await query.answer(f"🔀 {len(items) - 1} lagu di-shuffle!", show_alert=True)
        else:
            return await query.answer("❌ Tidak ada yang bisa di-shuffle", show_alert=True)

    elif action == "stop":
        await anon.stop(chat_id)
        status = "Streaming dihentikan"
        reply = f"{user} menghentikan streaming."

    try:
        if action in ["skip", "replay", "stop"]:
            await query.message.reply_text(reply, quote=False)
            await query.message.delete()
        else:
            mtext = re.sub(
                r"\n\n<blockquote>.*?</blockquote>",
                "",
                query.message.caption.html or query.message.text.html,
                flags=re.DOTALL,
            )
            keyboard = buttons.controls(
                chat_id, status=status if action != "resume" else None
            )
        await query.edit_message_text(
            f"{mtext}\n\n<blockquote>{reply}</blockquote>", reply_markup=keyboard
        )
    except:
        pass


@app.on_callback_query(filters.regex("help") & ~app.bl_users)
async def _help(_, query: types.CallbackQuery):
    data = query.data.split()
    if len(data) == 1:
        return await query.answer(url=f"https://t.me/{app.username}?start=help")

    if data[1] == "back":
        return await query.edit_message_text(
            text="<b>Klik tombol di bawah untuk mendapatkan informasi tentang perintah saya.</b>\n\n<i><b>Catatan:</b> Semua perintah dapat digunakan dengan /</i>", 
            reply_markup=buttons.help_markup({})
        )
    elif data[1] == "close":
        try:
            await query.message.delete()
            return await query.message.reply_to_message.delete()
        except:
            pass

    # Help text mapping - hardcoded from id.json
    help_texts = {
        "admins": "<u><b>Perintah admin:</b></u>\n\n/pause: Jeda streaming yang sedang berjalan.\n/resume: Lanjutkan streaming yang dijeda.\n/skip: Lewati streaming saat ini.\n/stop: Hentikan streaming yang sedang berjalan.\n\n/reload: Muat ulang cache admin.",
        "auth": "<u><b>Perintah auth:</b></u>\n<i>Pengguna terotorisasi dapat mengontrol streaming tanpa menjadi admin.</i>\n\n/auth: Tambahkan pengguna ke daftar terotorisasi.\n/unauth: Hapus pengguna dari daftar terotorisasi.",
        "blist": "<u><b>Perintah blacklist:</b></u>\n<i>Chat dan pengguna yang di-blacklist tidak bisa menggunakan bot.</i>\n\n/blacklist [chat_id|user_id]: Tambahkan chat/pengguna ke blacklist.\n/unblacklist [chat_id|user_id]: Hapus chat/pengguna dari blacklist",
        "ping": "<u><b>Perintah ping:</b></u>\n\n/help: Menampilkan menu bantuan bot.\n\n/ping: Cek ping dan penggunaan memori bot.\n\n/start: Mulai bot.\n\n/sudolist: Menampilkan daftar pengguna sudo bot.",
        "play": "<u><b>Perintah play:</b></u>\n<i>Anda dapat memutar musik di obrolan video menggunakan perintah berikut.</i>\n\n/play [nama lagu/url youtube/balas ke audio]: Putar musik di obrolan video.\n/vplay [nama lagu/url youtube/balas ke video]: Putar video musik di obrolan video.\n-f: Paksa putar musik di obrolan video.\n-v: Putar video musik di obrolan video.\n\n<b>Contoh:</b> <code>/play -f -v attention</code>",
        "queue": "<u><b>Perintah queue:</b></u>\n\n/queue: Menampilkan track yang sedang dalam antrian.",
        "stats": "<u><b>Perintah stats:</b></u>\n\n/stats: Menampilkan statistik bot.",
        "sudo": "<b><u>Perintah sudo:</b></u>\n\n/ac: Menampilkan jumlah panggilan aktif.\n\n/activevc: Menampilkan daftar panggilan aktif.\n\n/broadcast [balas ke pesan]: Broadcast pesan ke semua chat.\n-nochat: Kecualikan grup dari broadcast.\n-user: Sertakan pengguna dalam broadcast.\n-copy: Hapus tag forwarded dari pesan broadcast.\n<b>Contoh:</b> <code>/broadcast -user -copy</code>\n\n/eval: Jalankan kode yang diberikan.\n\n/logs: Kirim file log.\n\n/logger [on|off]: Aktifkan/nonaktifkan logger.\n\n/restart: Restart bot.\n\n/addsudo: Tambahkan pengguna ke daftar sudo.\n/rmsudo: Hapus pengguna dari daftar sudo."
    }
    
    await query.edit_message_text(
        text=help_texts.get(data[1], "Info tidak tersedia."),
        reply_markup=buttons.help_markup({}, True),
    )


@app.on_callback_query(filters.regex("settings") & ~app.bl_users)
@admin_check
async def _settings_cb(_, query: types.CallbackQuery):
    cmd = query.data.split()
    if len(cmd) == 1:
        return await query.answer()
    await query.answer("Memproses...", show_alert=True)

    chat_id = query.message.chat.id
    _admin = await db.get_play_mode(chat_id)
    _delete = await db.get_cmd_delete(chat_id)

    if cmd[1] == "delete":
        _delete = not _delete
        await db.set_cmd_delete(chat_id, _delete)
    elif cmd[1] == "play":
        await db.set_play_mode(chat_id, _admin)
        _admin = not _admin
    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            {},
            _admin,
            _delete,
            chat_id,
        )
    )


@app.on_callback_query(filters.regex("donate") & ~app.bl_users)
async def _donate_cb(_, query: types.CallbackQuery):
    """Handle donate button click and show donation info."""
    from anony import config
    
    await query.answer()
    
    donate_text = "✨ <b>Dukung Bot Musik Tetap Hidup!</b> ✨\n\n<blockquote>Suka dengan fitur bot ini? Bantu kami agar server tetap menyala dan bot bisa terus memutar musik tanpa henti! 🚀\nDonasi kalian sangat berarti untuk membayar biaya server bulanan kami. 🔌</blockquote>\n\nYuk scan QR di bawah ini untuk donasi! 👇"
    
    await query.message.reply_text(
        text=donate_text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=types.InlineKeyboardMarkup(
            [[types.InlineKeyboardButton(text="🎁 Dukung Kami", url=config.DONATE_QR_IMAGE)]]
        ),
    )
