# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
Dashboard Admin Commands - Control dashboard from Telegram
"""

from pyrogram import enums, filters, types

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
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    command = message.command[1].lower()
    
    if command == "start":
        await message.reply_text(
            f"📊 <b>Starting Dashboard Server...</b>\n\n"
            f"<blockquote>Please start the dashboard manually using:\n"
            f"<code>python -m dashboard.server</code>\n\n"
            f"Or use: <code>python dashboard/server.py</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    elif command == "stop":
        await message.reply_text(
            f"📊 <b>Dashboard Server</b>\n\n"
            f"<blockquote>To stop the dashboard, press Ctrl+C in the terminal "
            f"where it's running.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    else:
        await message.reply_text(
            f"❌ <b>Invalid Command</b>\n\n"
            f"<blockquote>Use: <code>/dashboard start</code> or <code>/dashboard stop</code></blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

