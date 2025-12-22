# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
Admin Commands - Restart, Shutdown, FloodWait management
"""

import os
import sys
from datetime import datetime

from pyrogram import enums, filters, types

from delta import app, config, logger
from delta.helpers._graceful import graceful_handler, safe_restart, with_flood_wait_handler


# Custom sudo filter that checks at runtime
def sudo_filter(_, __, message):
    """Runtime check for sudo users"""
    if not message.from_user:
        return False
    return message.from_user.id in app.sudoers or message.from_user.id == config.OWNER_ID

sudo_users_filter = filters.create(sudo_filter)


@app.on_message(filters.command(["restart", "reboot"]) & sudo_users_filter)
async def restart_handler(_, message: types.Message):
    """
    Restart bot dengan aman (Admin only)
    
    Usage: /restart
    """
    sent = await message.reply_text(
        "🔄 <b>Restarting Bot...</b>\n\n"
        "<blockquote>Mohon tunggu sebentar...</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
    
    logger.info(f"🔄 Restart initiated by {message.from_user.id}")
    
    try:
        # Update message
        await sent.edit_text(
            "🔄 <b>Restarting Bot...</b>\n\n"
            "<blockquote>✅ Stopping services...\n"
            "⏳ Bot will be back in ~10 seconds</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        
        # Perform safe restart
        await safe_restart()
        
    except Exception as e:
        logger.error(f"❌ Restart failed: {e}", exc_info=True)
        await sent.edit_text(
            f"❌ <b>Restart Failed</b>\n\n"
            f"<blockquote>Error: {str(e)}\n\n"
            f"Manual restart required.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )


@app.on_message(filters.command(["shutdown", "stop"]) & filters.user(config.OWNER_ID))
async def shutdown_handler(_, message: types.Message):
    """
    Shutdown bot dengan aman (Owner only)
    
    Usage: /shutdown
    """
    await message.reply_text(
        "🛑 <b>Shutting Down Bot...</b>\n\n"
        "<blockquote>Goodbye! 👋</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
    
    logger.info(f"🛑 Shutdown initiated by {message.from_user.id}")
    
    # Trigger graceful shutdown
    await graceful_handler.shutdown()


@app.on_message(filters.command(["status", "health"]) & sudo_users_filter)
@with_flood_wait_handler(max_retries=2)
async def status_handler(_, message: types.Message):
    """
    Check bot health status (Admin only)
    
    Usage: /status
    """
    from delta import boot, db, anon
    from delta.helpers._graceful import flood_handler
    import psutil
    import platform
    
    # Calculate uptime
    uptime_seconds = int((datetime.now().timestamp()) - boot)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    
    # Get system info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get bot stats
    total_chats = len(await db.get_chats())
    total_users = len(await db.get_users())
    active_calls = len(db.active_callsdb)
    
    status_text = (
        f"🤖 <b>Bot Status</b>\n\n"
        f"<blockquote expandable>"
        f"<b>⏱️ Uptime:</b> {uptime_hours}h {uptime_minutes}m\n"
        f"<b>🐍 Python:</b> {platform.python_version()}\n"
        f"<b>💻 OS:</b> {platform.system()} {platform.release()}\n\n"
        f"<b>📊 System Resources:</b>\n"
        f"• CPU: {cpu_percent}%\n"
        f"• RAM: {memory.percent}% ({memory.used // 1024 // 1024} MB / {memory.total // 1024 // 1024} MB)\n"
        f"• Disk: {disk.percent}% ({disk.used // 1024 // 1024 // 1024} GB / {disk.total // 1024 // 1024 // 1024} GB)\n\n"
        f"<b>📈 Bot Stats:</b>\n"
        f"• Groups: {total_chats}\n"
        f"• Users: {total_users}\n"
        f"• Active Calls: {active_calls}\n\n"
        f"<b>⚡ FloodWait:</b>\n"
        f"• Count: {flood_handler.flood_wait_count}\n"
        f"• Shutdown: {'🛑 Yes' if graceful_handler.is_shutting_down else '✅ No'}"
        f"</blockquote>"
    )
    
    await message.reply_text(status_text, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command(["logs"]) & filters.user(config.OWNER_ID))
async def logs_handler(_, message: types.Message):
    """
    Get recent logs (Owner only)
    
    Usage: /logs [lines]
    """
    try:
        # Get number of lines to show (default: 50)
        num_lines = 50
        if len(message.command) > 1:
            try:
                num_lines = int(message.command[1])
                num_lines = min(num_lines, 200)  # Max 200 lines
            except ValueError:
                pass
        
        # Read log file
        if not os.path.exists("log.txt"):
            return await message.reply_text("❌ Log file not found")
        
        with open("log.txt", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            recent_logs = "".join(lines[-num_lines:])
        
        # Send as file if too long
        if len(recent_logs) > 4000:
            with open("recent_logs.txt", "w", encoding="utf-8") as f:
                f.write(recent_logs)
            
            await message.reply_document(
                document="recent_logs.txt",
                caption=f"📄 <b>Recent Logs</b> (Last {num_lines} lines)",
                parse_mode=enums.ParseMode.HTML
            )
            
            os.remove("recent_logs.txt")
        else:
            await message.reply_text(
                f"📄 <b>Recent Logs</b> (Last {num_lines} lines)\n\n"
                f"<pre>{recent_logs}</pre>",
                parse_mode=enums.ParseMode.HTML
            )
    
    except Exception as e:
        await message.reply_text(
            f"❌ <b>Error Reading Logs</b>\n\n"
            f"<blockquote>{str(e)}</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )


@app.on_message(filters.command(["ping"]) & ~app.bl_users)
@with_flood_wait_handler(max_retries=2)
async def ping_handler(_, message: types.Message):
    """
    Check bot response time
    
    Usage: /ping
    """
    from datetime import datetime
    
    start = datetime.now()
    sent = await message.reply_text("🏓 Pong!")
    end = datetime.now()
    
    ms = (end - start).total_seconds() * 1000
    
    await sent.edit_text(
        f"🏓 <b>Pong!</b>\n\n"
        f"<blockquote>⚡ Response Time: <b>{ms:.2f}ms</b></blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
