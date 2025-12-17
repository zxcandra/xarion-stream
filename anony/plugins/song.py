# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from anony import app, config, yt


@app.on_message(filters.command(["song", "mp3"]) & filters.private & ~app.bl_users)
async def song_command(_, message: types.Message):
    """Download and send highest quality audio from YouTube."""
    
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Penggunaan:</b>\n\n<code>/song charlie puth attention</code>\natau\n<code>/song https://youtu.be/VIDEO_ID</code>"
        )
    
    query = message.text.split(None, 1)[1]
    mystic = await message.reply_text("🔍 Mencari lagu...")
    
    try:
        # Search for the song
        track = await yt.search(query, mystic.id)
        if not track:
            return await mystic.edit_text(
                "❌ Gagal menemukan lagu.\n\nCoba dengan kata kunci yang berbeda."
            )
        
        # Build response with thumbnail and download button
        caption = f"🎵 <b>{track.title}</b>\n\n"
        caption += f"⏱ <b>Durasi:</b> {track.duration}\n"
        caption += f"👁 <b>Views:</b> {track.view_count}\n"
        caption += f"📺 <b>Channel:</b> {track.channel_name}\n\n"
        caption += "<i>Klik tombol di bawah untuk download audio kualitas terbaik</i>"
        
        button = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(
                text="⬇️ Download Audio",
                callback_data=f"song_dl {track.id}"
            )],
            [types.InlineKeyboardButton(
                text="❌ Tutup",
                callback_data="close"
            )]
        ])
        
        await mystic.delete()
        await message.reply_photo(
            photo=track.thumbnail,
            caption=caption,
            reply_markup=button
        )
        
    except Exception as e:
        await mystic.edit_text(f"❌ Error: {str(e)}")


@app.on_message(filters.command(["song", "mp3"]) & filters.group & ~app.bl_users)
async def song_command_group(_, message: types.Message):
    """Redirect to PM for song download in groups."""
    button = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton(
            text="💬 Buka di Private Chat",
            url=f"https://t.me/{app.username}?start=song"
        )]
    ])
    await message.reply_text(
        "🎵 <b>Download Lagu</b>\n\n"
        "Gunakan perintah ini di private chat untuk download lagu!",
        reply_markup=button
    )


@app.on_callback_query(filters.regex(pattern=r"song_dl") & ~app.bl_users)
async def song_download_cb(_, query: types.CallbackQuery):
    """Download and send highest quality audio."""
    try:
        await query.answer("⬇️ Downloading...", show_alert=True)
    except:
        pass
    
    vidid = query.data.split(None, 1)[1]
    yturl = f"https://www.youtube.com/watch?v={vidid}"
    
    await query.edit_message_caption("⏳ Downloading audio (kualitas terbaik)...")
    
    # Download thumbnail
    thumb_path = await query.message.download()
    
    try:
        import yt_dlp
        import os
        import asyncio
        
        filename = f"downloads/{vidid}.mp3"
        
        # Use bestaudio format for highest quality
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": filename,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",  # 320kbps - highest quality
            }],
        }
        
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(yturl, download=True)
                return info
        
        info = await asyncio.to_thread(_download)
        
        if not os.path.exists(filename):
            raise Exception("File tidak ditemukan setelah download")
        
        # Check file size (Telegram limit: 50MB for bots)
        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            os.remove(filename)
            return await query.edit_message_caption(
                "❌ File terlalu besar (>50MB)\n\nCoba lagu dengan durasi lebih pendek."
            )
        
        await query.edit_message_caption("📤 Uploading audio...")
        await app.send_chat_action(
            chat_id=query.message.chat.id,
            action=enums.ChatAction.UPLOAD_AUDIO
        )
        
        # Send audio
        await query.message.reply_audio(
            audio=filename,
            thumb=thumb_path,
            title=info.get("title", "Unknown"),
            performer=info.get("uploader", "Unknown"),
            duration=info.get("duration", 0)
        )
        
        await query.message.delete()
        
        # Cleanup
        try:
            os.remove(filename)
            os.remove(thumb_path)
        except:
            pass
            
    except Exception as e:
        await query.edit_message_caption(f"❌ Download gagal: {str(e)}")
