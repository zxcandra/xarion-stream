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
        
        # Use existing download method from YouTube class
        file_path = await yt.download(track.id, video=False)
        
        if not file_path:
            return await mystic.edit_text(
                "❌ Gagal download lagu.\n\nHubungi @" + config.SUPPORT_CHANNEL
            )
        
        import os
        
        # Check file size (Telegram limit: 50MB for bots)
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            os.remove(file_path)
            return await mystic.edit_text(
                "❌ File terlalu besar (>50MB)\n\nCoba lagu dengan durasi lebih pendek."
            )
        
        await mystic.edit_text("📤 Uploading audio...")
        await app.send_chat_action(
            chat_id=message.chat.id,
            action=enums.ChatAction.UPLOAD_AUDIO
        )
        
        # Send audio without thumbnail for now
        await message.reply_audio(
            audio=file_path,
            title=track.title,
            performer=track.channel_name,
            duration=track.duration_sec
        )
        
        await mystic.delete()
        
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
            
    except Exception as e:
        await mystic.edit_text(f"❌ Error: {str(e)}")

