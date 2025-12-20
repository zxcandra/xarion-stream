# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import re

from pyrogram import enums, filters, types

from delta import anon, app, db, queue, tg, yt
from delta.helpers import admin_check, buttons, can_manage_vc


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
async def cancel_dl(_, query: types.CallbackQuery):
    await query.answer()
    await tg.cancel(query)


@app.on_callback_query(filters.regex("^noop$") & ~app.bl_users)
async def noop_callback(_, query: types.CallbackQuery):
    """Handle no-operation callbacks (for non-clickable label buttons)"""
    await query.answer()


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
    
    # Handle playlist and close without admin requirement message
    if action == "playlist":
        media = queue.get_current(chat_id)
        if not media:
            return await query.answer("Tidak ada lagu yang sedang diputar!", show_alert=True)
        
        user_id = query.from_user.id
        track_id = media.id
        title = media.title
        duration = getattr(media, 'duration', '0:00')
        url = getattr(media, 'url', '')
        
        try:
            added = await db.add_to_playlist(user_id, track_id, title, duration, url)
            if added:
                return await query.answer(f"✅ '{title}' ditambahkan ke playlist Anda!", show_alert=True)
            else:
                return await query.answer(f"ℹ️ '{title}' sudah ada di playlist Anda!", show_alert=True)
        except Exception as e:
            return await query.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)

    if action == "close":
        try:
            await query.message.delete()
        except:
            pass
        return

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

    elif action == "page":
        # Handle queue pagination
        page = int(args[3])
        
        # Re-fetch items
        items = queue.get_queue(chat_id)
        total_items = len(items)
        page_size = 20
        total_pages = (total_items + page_size - 1) // page_size
        
        # Ensure page is valid
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * page_size
        end_idx = start_idx + page_size
        current_items = items[start_idx:end_idx]
        
        # Calculate total duration
        total_seconds = sum(item.duration_sec for item in items if hasattr(item, 'duration_sec'))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            total_duration = f"{hours}:{minutes:02d}:00"
        else:
            total_duration = f"{minutes}:00"
            
        # Build text
        text = f"📋 <b>Antrian Musik</b>\n\n"
        text += f"<b>Total:</b> {total_items} lagu • ⏱ {total_duration}\n\n"
        text += "<blockquote>"
        
        # Emoji numbers for first 10 items of the FIRST page only
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, item in enumerate(current_items, start=start_idx + 1):
            media_icon = "🎬" if item.video else "🎵"
            if i <= 10:
                num = emoji_numbers[i-1]
            else:
                num = f"{i}."
            text += f"{num} {media_icon} {item.title}\n"
        
        text += "</blockquote>"
        
        # Show remaining count if not on last page
        remaining = total_items - end_idx
        if remaining > 0:
            text += f"\n\n➕ <i>... dan {remaining} lagu lagi</i>"
            
        return await query.edit_message_text(
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.queue_markup(
                chat_id,
                "Sedang memutar" if await db.playing(chat_id) else "Streaming dijeda",
                await db.playing(chat_id),
                page,
                total_pages
            )
        )




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
        "sudo": "<b><u>Perintah sudo:</b></u>\n\n/ac: Menampilkan jumlah panggilan aktif.\n\n/activevc: Menampilkan daftar panggilan aktif.\n\n/broadcast [balas ke pesan]: Broadcast pesan ke semua chat.\n-nochat: Kecualikan grup dari broadcast.\n-user: Sertakan pengguna dalam broadcast.\n-copy: Hapus tag forwarded dari pesan broadcast.\n<b>Contoh:</b> <code>/broadcast -user -copy</code>\n\n/eval: Jalankan kode yang diberikan.\n\n/logs: Kirim file log.\n\n/logger [on|off]: Aktifkan/nonaktifkan logger.\n\n/restart: Restart bot.\n\n/addsudo: Tambahkan pengguna ke daftar sudo.\n/rmsudo: Hapus pengguna dari daftar sudo.",
        "drama": "<u><b>🎬 DramaBox:</b></u>\n<i>Nonton drama pendek dari DramaBox langsung di Telegram!</i>\n\n/drama [judul]: Cari drama berdasarkan judul.\n/drama: Tampilkan drama trending.\n/dramatrending atau /dt: Drama populer.\n/dramaterbaru atau /dn: Drama terbaru.\n\n<b>Fitur:</b>\n• Pilih episode langsung dari bot\n• Pilih kualitas video (144p - 1080p)\n• Streaming di Voice Chat Grup\n• Link streaming langsung ke browser\n\n⚠️ <b>Pengaturan:</b>\nAdmin dapat membatasi akses fitur ini melalui /settings."
    }
    
    await query.edit_message_text(
        text=help_texts.get(data[1], "Info tidak tersedia."),
        reply_markup=buttons.help_markup({}, True),
    )


@app.on_callback_query(filters.regex("donate") & ~app.bl_users)
async def _donate_cb(_, query: types.CallbackQuery):
    """Handle donate button click and show donation info."""
    from delta import config
    
    await query.answer()
    
    donate_text = "✨ <b>Dukung Bot Musik Tetap Hidup!</b> ✨\n\n<blockquote>Suka dengan fitur bot ini? Bantu kami agar server tetap menyala dan bot bisa terus memutar musik tanpa henti! 🚀\nDonasi kalian sangat berarti untuk membayar biaya server bulanan kami. 🔌</blockquote>\n\nYuk scan QR di bawah ini untuk donasi! 👇"
    
    await query.message.reply_text(
        text=donate_text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=types.InlineKeyboardMarkup(
            [[types.InlineKeyboardButton(text="🎁 Dukung Kami", url=config.DONATE_QR_IMAGE)]]
        ),
    )


# SETTINGS COMMAND
@app.on_message(filters.command(["settings"]) & filters.group & ~app.bl_users)
async def player_settings_cmd(_, message: types.Message):
    """Display player settings panel."""
    chat_id = message.chat.id
    
    # Get current settings
    loop_mode = await db.get_loop_mode(chat_id)
    admin_only = await db.get_play_mode(chat_id)
    cmd_delete = await db.get_cmd_delete(chat_id)
    video_mode = await db.get_video_mode(chat_id)
    video_quality = await db.get_video_quality(chat_id)
    drama_mode = await db.get_drama_mode(chat_id)
    
    # Format loop mode display
    loop_text = {
        "normal": "▶️ Normal",
        "loop_all": "🔁 Loop All",
        "loop_one": "🔂 Loop One"
    }.get(loop_mode, "▶️ Normal")
    
    text = f"""⚙️ <b>Player Settings</b>

<blockquote>🔁 <b>Loop Mode:</b> {loop_text}
📹 <b>Video Mode:</b> {'✅ Aktif' if video_mode else '❌ Nonaktif'}
🎬 <b>Kualitas:</b> 📺 {video_quality}
👮 <b>Admin Only:</b> {'✅ Aktif' if admin_only else '❌ Nonaktif'}
🗑 <b>Auto Delete:</b> {'✅ Aktif' if cmd_delete else '❌ Nonaktif'}
🎭 <b>Drama (Admin):</b> {'✅ Aktif' if drama_mode else '❌ Nonaktif'}</blockquote>

<i>Klik tombol di bawah untuk mengubah pengaturan</i>"""
    
    await message.reply_text(
        text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons.player_settings_markup(loop_mode, admin_only, cmd_delete, video_mode, video_quality, drama_mode, chat_id)
    )


@app.on_callback_query(filters.regex("player_settings") & ~app.bl_users)
@admin_check
async def _player_settings_cb(_, query: types.CallbackQuery):
    """Handle player settings callback."""
    cmd = query.data.split()
    if len(cmd) == 1:
        return await query.answer()
    await query.answer("Memproses...", show_alert=True)

    chat_id = query.message.chat.id
    loop_mode = await db.get_loop_mode(chat_id)
    admin_only = await db.get_play_mode(chat_id)
    cmd_delete = await db.get_cmd_delete(chat_id)
    video_mode = await db.get_video_mode(chat_id)
    drama_mode = await db.get_drama_mode(chat_id)

    if cmd[1] == "loop":
        # Cycle through loop modes
        modes = ["normal", "loop_all", "loop_one"]
        current_idx = modes.index(loop_mode) if loop_mode in modes else 0
        new_mode = modes[(current_idx + 1) % len(modes)]
        await db.set_loop_mode(chat_id, new_mode)
        loop_mode = new_mode
    elif cmd[1] == "video":
        video_mode = not video_mode
        await db.set_video_mode(chat_id, video_mode)
    elif cmd[1] == "drama":
        drama_mode = not drama_mode
        await db.set_drama_mode(chat_id, drama_mode)
    elif cmd[1] == "admin":
        admin_only = not admin_only
        await db.set_play_mode(chat_id, not admin_only)
    elif cmd[1] == "delete":
        cmd_delete = not cmd_delete
        await db.set_cmd_delete(chat_id, cmd_delete)
    elif cmd[1] == "quality":
        # Cycle through quality options
        qualities = ["360p", "480p", "720p", "1080p"]
        video_quality = await db.get_video_quality(chat_id)
        current_idx = qualities.index(video_quality) if video_quality in qualities else 2
        new_quality = qualities[(current_idx + 1) % len(qualities)]
        await db.set_video_quality(chat_id, new_quality)
        video_quality = new_quality
    elif cmd[1] == "close":
        try:
            await query.message.delete()
        except:
            pass
        return
    
    # Get video quality if not already set
    if 'video_quality' not in dir():
        video_quality = await db.get_video_quality(chat_id)
    
    # Format loop mode display
    loop_text = {
        "normal": "▶️ Normal",
        "loop_all": "🔁 Loop All",
        "loop_one": "🔂 Loop One"
    }.get(loop_mode, "▶️ Normal")
    
    text = f"""⚙️ <b>Player Settings</b>

<blockquote>🔁 <b>Loop Mode:</b> {loop_text}
📹 <b>Video Mode:</b> {'✅ Aktif' if video_mode else '❌ Nonaktif'}
🎬 <b>Kualitas:</b> 📺 {video_quality}
👮 <b>Admin Only:</b> {'✅ Aktif' if admin_only else '❌ Nonaktif'}
🗑 <b>Auto Delete:</b> {'✅ Aktif' if cmd_delete else '❌ Nonaktif'}
🎭 <b>Drama (Admin):</b> {'✅ Aktif' if drama_mode else '❌ Nonaktif'}</blockquote>

<i>Klik tombol di bawah untuk mengubah pengaturan</i>"""
    
    await query.edit_message_text(
        text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons.player_settings_markup(loop_mode, admin_only, cmd_delete, video_mode, video_quality, drama_mode, chat_id)
    )

