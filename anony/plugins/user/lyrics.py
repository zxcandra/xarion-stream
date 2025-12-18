# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pyrogram import filters, types

from anony import app, config, queue
from anony.helpers._decorators import command_limiter, require_rate_limit, safe_execute
from anony.helpers._lyrics import lyrics_searcher


# Custom sudo filter that checks at runtime
def sudo_filter(_, __, message):
    """Runtime check for sudo users"""
    if not message.from_user:
        return False
    return message.from_user.id in app.sudoers or message.from_user.id == config.OWNER_ID

sudo_users_filter = filters.create(sudo_filter)


@app.on_message(
    filters.command(["lyrics", "lirik"]) 
    & filters.group 
    & ~app.bl_users
)
@require_rate_limit(command_limiter)
@safe_execute(send_error=True)
async def lyrics_handler(_, message: types.Message):
    """
    Get lyrics for currently playing song or search by query
    
    Usage:
        /lyrics - Get lyrics for current song
        /lyrics <query> - Search lyrics for specific song
    """
    sent = await message.reply_text("🔎 <b>Mencari lirik...</b>", parse_mode="HTML")
    
    # Determine what song to search for
    if len(message.command) > 1:
        # User provided a query
        query = " ".join(message.command[1:])
    else:
        # Get currently playing song
        current = queue.get_current(message.chat.id)
        if not current:
            return await sent.edit_text(
                "❌ <b>Tidak ada lagu yang sedang diputar</b>\n\n"
                "<blockquote>Gunakan <code>/lyrics [nama lagu]</code> untuk mencari lirik lagu tertentu.</blockquote>",
                parse_mode="HTML"
            )
        query = current.title
    
    # Search for lyrics
    lyrics_data = await lyrics_searcher.search(query)
    
    if not lyrics_data:
        return await sent.edit_text(
            f"❌ <b>Lirik Tidak Ditemukan</b>\n\n"
            f"<blockquote>Tidak dapat menemukan lirik untuk: <i>{query}</i>\n\n"
            f"💡 Tips:\n"
            f"• Pastikan ejaan nama lagu benar\n"
            f"• Coba sertakan nama artis\n"
            f"• Gunakan format: /lyrics Artist - Song</blockquote>",
            parse_mode="HTML"
        )
    
    # Format and send lyrics
    formatted_lyrics = lyrics_searcher.format_lyrics(lyrics_data)
    
    await sent.edit_text(
        formatted_lyrics,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@app.on_message(
    filters.command(["cache", "storage"]) 
    & sudo_users_filter
)
@safe_execute(send_error=True)
async def cache_stats_handler(_, message: types.Message):
    """
    Show cache statistics and manage storage (Admin only)
    
    Usage:
        /cache - Show cache stats
        /cache clear - Clear all cached files
    """
    from anony.helpers._cleanup import cleanup
    
    stats = await cleanup.get_cache_stats()
    
    if len(message.command) > 1 and message.command[1].lower() == "clear":
        await cleanup.clear_all()
        await message.reply_text(
            "✅ <b>Cache Cleared</b>\n\n"
            "<blockquote>Semua file cache telah dihapus.</blockquote>",
            parse_mode="HTML"
        )
        return
    
    await message.reply_text(
        f"💾 <b>Cache Statistics</b>\n\n"
        f"<blockquote>"
        f"📁 <b>Total Files:</b> {stats['total_files']}\n"
        f"💿 <b>Total Size:</b> {stats['total_size_mb']:.2f} MB\n"
        f"📂 <b>Path:</b> <code>{stats['path']}</code>\n\n"
        f"💡 <b>Tip:</b> Gunakan /cache clear untuk menghapus semua cache"
        f"</blockquote>",
        parse_mode="HTML"
    )
