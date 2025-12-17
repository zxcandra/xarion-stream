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
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote><code>/song [judul lagu]</code>\nAtau: <code>/song [youtube url]</code></blockquote>",
            parse_mode="html"
        )
    
    query = message.text.split(None, 1)[1]
    mystic = await message.reply_text("🔎 <b>Mencari Lagu...</b>", parse_mode="html")
    
    try:
        # Search for the song
        track = await yt.search(query, mystic.id)
        if not track:
            return await mystic.edit_text(
                "❌ <b>Lagu Tidak Ditemukan</b>\n\n<blockquote>Coba gunakan kata kunci atau link yang berbeda</blockquote>",
                parse_mode="html"
            )
        
        # Auto download - no confirmation needed
        await mystic.edit_text(
            "⬇️ <b>Mengunduh Audio...</b>\n\n<blockquote>Mohon tunggu sebentar...</blockquote>",
            parse_mode="html"
        )
        
        import yt_dlp
        import os
        import asyncio
        import re
        
        yturl = f"https://www.youtube.com/watch?v={track.id}"
        
        # Sanitize title for filename (remove special characters)
        safe_title = re.sub(r'[^\w\s-]', '', track.title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        safe_title = safe_title[:50]  # Limit length
        
        output_template = f"downloads/{safe_title}.%(ext)s"
        
        # Get cookies for YouTube authentication
        cookie = yt.get_cookies()
        
        # Download and convert to MP3
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "cookiefile": cookie,
            "keepvideo": False,  # Remove original after conversion
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        }
        
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(yturl, download=True)
        
        await asyncio.to_thread(_download)
        
        # File will be .mp3 after conversion
        file_path = f"downloads/{safe_title}.mp3"
        
        if not os.path.exists(file_path):
            return await mystic.edit_text(
                f"❌ <b>Gagal Mengunduh</b>\n\n<blockquote>Silakan lapor ke <a href='{config.SUPPORT_CHANNEL}'>chat dukungan</a></blockquote>",
                parse_mode="html"
            )
        
        import os
        
        # Check file size (Telegram limit: 50MB for bots)
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            os.remove(file_path)
            return await mystic.edit_text(
                "❌ <b>File Terlalu Besar</b>\n\n<blockquote>Ukuran file >50MB. Coba lagu dengan durasi lebih pendek.</blockquote>",
                parse_mode="html"
            )
        
        await mystic.edit_text("⬆️ <b>Mengunggah Audio...</b>", parse_mode="html")
        await app.send_chat_action(
            chat_id=message.chat.id,
            action=enums.ChatAction.UPLOAD_AUDIO
        )
        
        # Download thumbnail
        thumb_path = None
        try:
            import aiohttp
            thumb_path = f"downloads/{safe_title}_thumb.jpg"
            async with aiohttp.ClientSession() as session:
                async with session.get(track.thumbnail) as resp:
                    if resp.status == 200:
                        with open(thumb_path, 'wb') as f:
                            f.write(await resp.read())
        except:
            thumb_path = None
        
        # Build caption with song info
        caption = f"🎵 <b>{track.title}</b>\n\n"
        caption += "<blockquote>"
        caption += f"⏱ <b>Durasi:</b> {track.duration}\n"
        if track.view_count:
            caption += f"👁 <b>Views:</b> {track.view_count}"
        caption += "</blockquote>"
        
        # Create inline button for YouTube link
        keyboard = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(
                text="🔗 YouTube Link",
                url=track.url
            )]
        ])
        
        # Send audio with thumbnail
        await message.reply_audio(
            audio=file_path,
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboard,
            thumb=thumb_path,
            title=track.title,
            performer=track.channel_name,
            duration=track.duration_sec
        )
        
        await mystic.delete()
        
        # Cleanup
        try:
            os.remove(file_path)
            if thumb_path:
                os.remove(thumb_path)
        except:
            pass
            
    except Exception as e:
        await mystic.edit_text(f"❌ <b>Terjadi Kesalahan</b>\n\n<blockquote>{str(e)}</blockquote>", parse_mode="html")

