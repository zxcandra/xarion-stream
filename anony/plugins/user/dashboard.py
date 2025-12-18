# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
Dashboard Admin Commands - Control dashboard from Telegram
"""

from pyrogram import filters, types

from anony import app, config, logger


# Custom sudo filter that checks at runtime
def sudo_filter(_, __, message):
    """Runtime check for sudo users"""
    if not message.from_user:
        return False
    return message.from_user.id in app.sudoers or message.from_user.id == config.OWNER_ID

sudo_users_filter = filters.create(sudo_filter)


@app.on_message(filters.command(["dashboard"]) & sudo_users_filter)
async def dashboard_command(_, message: types.Message):
    """
    Dashboard management (Admin only)
    
    Usage:
        /dashboard - Show dashboard info
        /dashboard start - Start dashboard server
        /dashboard stop - Stop dashboard server
    """
    
    if len(message.command) == 1:
        # Show dashboard info
        dashboard_url = f"http://localhost:8000"  # Adjust based on your deployment
        
        await message.reply_text(
            f"📊 <b>Statistics Dashboard</b>\n\n"
            f"<blockquote>"
            f"🌐 <b>URL:</b> <code>{dashboard_url}</code>\n\n"
            f"<b>Commands:</b>\n"
            f"• <code>/dashboard start</code> - Start server\n"
            f"• <code>/dashboard stop</code> - Stop server\n\n"
            f"💡 Dashboard shows real-time statistics:\n"
            f"• Top tracks & users\n"
            f"• Active voice calls\n"
            f"• Daily play counts\n"
            f"• Group rankings"
            f"</blockquote>",
            parse_mode="HTML"
        )
        return
    
    command = message.command[1].lower()
    
    if command == "start":
        await message.reply_text(
            f"📊 <b>Starting Dashboard Server...</b>\n\n"
            f"<blockquote>Please start the dashboard manually using:\n"
            f"<code>python -m dashboard.server</code>\n\n"
            f"Or use: <code>python dashboard/server.py</code></blockquote>",
            parse_mode="HTML"
        )
    
    elif command == "stop":
        await message.reply_text(
            f"📊 <b>Dashboard Server</b>\n\n"
            f"<blockquote>To stop the dashboard, press Ctrl+C in the terminal "
            f"where it's running.</blockquote>",
            parse_mode="HTML"
        )
    
    else:
        await message.reply_text(
            f"❌ <b>Invalid Command</b>\n\n"
            f"<blockquote>Use: <code>/dashboard start</code> or <code>/dashboard stop</code></blockquote>",
            parse_mode="HTML"
        )


@app.on_message(filters.command(["stats", "statistics"]) & filters.group & ~app.bl_users)
async def group_stats_command(_, message: types.Message):
    """
    Get statistics for current group
    
    Usage: /stats
    """
    from anony import db
    
    chat_id = message.chat.id
    
    sent = await message.reply_text("📊 <b>Mengambil statistik...</b>", parse_mode="HTML")
    
    try:
        # Get group stats
        stats = await db.get_group_stats(chat_id, limit=5)
        users = await db.get_group_top_users(chat_id, limit=5)
        
        # Format top tracks
        if stats:
            tracks_text = "\n".join([
                f"{i+1}. <b>{data['title']}</b> - {data['spot']} plays"
                for i, (track_id, data) in enumerate(stats.items())
            ])
        else:
            tracks_text = "<i>Belum ada data</i>"
        
        # Format top users
        if users:
            users_text = "\n".join([
                f"{i+1}. User {user_id}: {count} plays"
                for i, (user_id, count) in enumerate(users.items())
            ])
        else:
            users_text = "<i>Belum ada data</i>"
        
        await sent.edit_text(
            f"📊 <b>Statistik {message.chat.title}</b>\n\n"
            f"<blockquote expandable>"
            f"<b>🏆 Top Tracks:</b>\n{tracks_text}\n\n"
            f"<b>👤 Most Active Users:</b>\n{users_text}"
            f"</blockquote>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error getting group stats: {e}")
        await sent.edit_text(
            f"❌ <b>Gagal Mengambil Statistik</b>\n\n"
            f"<blockquote>Error: {str(e)}</blockquote>",
            parse_mode="HTML"
        )
