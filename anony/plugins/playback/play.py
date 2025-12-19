# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pathlib import Path

from pyrogram import enums, filters, types

from anony import anon, app, config, db, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers._play import checkUB


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text

@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    # Add reaction to the message
    try:
        import random
        reactions = ["👍", "❤", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "🙏", "👌", "🕊", "😍", "🐳", "❤‍🔥", "🌭", "💯", "🤣", "⚡", "🍌", "🏆", "🍾", "💋", "👻", "👨‍💻", "👀", "🎃", "😇", "😨", "🤝", "✍", "🤗", "🫡", "🎅", "🎄", "☃", "💅", "🤪", "🆒", "💘", "🦄", "😘", "😎", "👾"]
        await m.react(emoji=random.choice(reactions))
    except:
        pass
    
    # Auto-delete command if enabled
    if config.AUTO_DELETE_COMMANDS:
        await utils.auto_delete(m)
    
    sent = await m.reply_text("🔎", parse_mode=enums.ParseMode.HTML)
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    # Check if command has arguments and detect URL
    if len(m.command) >= 2:
        query = " ".join(m.command[1:])
        # Check if it's a YouTube URL
        if "youtube.com" in query or "youtu.be" in query:
            url = query
    
    if url:
        if "playlist" in url:
            await sent.edit_text(
                "🔄 <b>Mengambil Playlist...</b>\n\n<blockquote>Mohon tunggu sebentar...</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                await sent.edit_text(
                    "❌ <b>Gagal Mengambil Playlist</b>\n\n<blockquote>Pastikan link playlist valid dan tidak private</blockquote>",
                    parse_mode=enums.ParseMode.HTML
                )
                await utils.auto_delete(sent)
                return

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            await sent.edit_text(
                f"❌ <b>Gagal Memproses</b>\n\n<blockquote>Jika masalah berlanjut, laporkan ke <a href={config.SUPPORT_CHANNEL}>chat dukungan</a></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            await utils.auto_delete(sent)
            return

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
        if not file:
            await sent.edit_text(
                f"❌ <b>Gagal Memproses</b>\n\n<blockquote>Jika masalah berlanjut, laporkan ke <a href='tg://user?id={config.OWNER_ID}'>chat dukungan</a></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            await utils.auto_delete(sent)
            return

    elif media:
        # removed setattr lang
        file = await tg.download(m.reply_to_message, sent)

    if not file:
        await sent.edit_text(
            "❌ <b>Lagu Tidak Ditemukan</b>\n\n<blockquote><b>Penggunaan:</b>\n<code>/play attention</code>\n<code>/play [youtube url]</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        await utils.auto_delete(sent)
        return

    if file.duration_sec > config.DURATION_LIMIT:
        await sent.edit_text(
            f"❌ <b>Durasi Terlalu Panjang</b>\n\n<blockquote>Maksimal durasi yang diperbolehkan adalah {config.DURATION_LIMIT // 60} menit</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        await utils.auto_delete(sent)
        return

    if await db.is_logger():
        await utils.play_log(m, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)

        if await db.get_call(m.chat.id):
            await sent.edit_text(
                f"✅ <b>Ditambahkan ke Antrian: #{position}</b>\n\n<blockquote><b>Judul:</b> <a href={file.url}>{file.title}</a>\n<b>Durasi:</b> {file.duration} menit\n<b>Diminta oleh:</b> {m.from_user.mention}</blockquote>",
                reply_markup=buttons.play_queued(
                    m.chat.id, file.id, "Putar Sekarang"
                ),
                parse_mode=enums.ParseMode.HTML
            )
            await utils.auto_delete(sent)
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                playlist_msg = await app.send_message(
                    chat_id=m.chat.id,
                    text=f"<u><b>Menambahkan {len(tracks)} track dari playlist ke antrian:</b></u>\n\n" + added,
                )
                await utils.auto_delete(playlist_msg)
            return

    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            await sent.edit_text("⏳ <b>Sedang memproses, harap tunggu...</b>", parse_mode=enums.ParseMode.HTML)
            file.file_path = await yt.download(file.id, video=video)

    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks)
    playlist_msg = await app.send_message(
        chat_id=m.chat.id,
        text=f"<u><b>Menambahkan {len(tracks)} track dari playlist ke antrian:</b></u>\n\n" + added,
    )
    await utils.auto_delete(playlist_msg)
