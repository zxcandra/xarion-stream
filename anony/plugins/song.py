# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, filters, types

from anony import app, config, yt


@app.on_message(filters.command(["song", "mp3"]) & ~app.bl_users)
async def song_command(_, message: types.Message):
    """Download and send highest quality audio from YouTube - Auto download."""
    
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
        
        # Auto download - no confirmation needed
        await mystic.edit_text("⏳ Downloading audio...")
        
        yturl = f"https://www.youtube.com/watch?v={track.id}"
        
        import yt_dlp
        import os
        import asyncio
        
        filename = f"downloads/{track.id}.mp3"
        
        # Get cookies for YouTube authentication
        cookie = yt.get_cookies()
        
        # Use bestaudio format for standard quality
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": filename,
            "quiet": True,
            "no_warnings": True,
            "cookiefile": cookie,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",  # Highest quality
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
            return await mystic.edit_text(
                "❌ File terlalu besar (>50MB)\n\nCoba lagu dengan durasi lebih pendek."
            )
        
        await mystic.edit_text("📤 Uploading audio...")
        await app.send_chat_action(
            chat_id=message.chat.id,
            action=enums.ChatAction.UPLOAD_AUDIO
        )
        
        # Send audio
        await message.reply_audio(
            audio=filename,
            thumb=track.thumbnail,
            title=track.title,
            performer=track.channel_name,
            duration=track.duration_sec
        )
        
        await mystic.delete()
        
        # Cleanup
        try:
            os.remove(filename)
        except:
            pass
            
    except Exception as e:
        await mystic.edit_text(f"❌ Error: {str(e)}")

