# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
import os
import platform
import psutil

from pyrogram import enums, filters, types
from pyrogram.types import InputMediaPhoto

from anony import app, config, db, userbot
from anony.helpers import buttons
from anony.plugins import all_modules


@app.on_message(filters.command(["stats"]) & filters.group & ~app.bl_users)
async def stats_command(_, m: types.Message):
    """Main stats command with button navigation."""
    is_sudo = m.from_user.id in app.sudoers
    await m.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=f"🎵 <b>Selamat Datang di Statistik {app.name}!</b>\n\n<blockquote>Pilih kategori statistik yang ingin dilihat:</blockquote>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons.stats_buttons({}, is_sudo),
    )


@app.on_callback_query(filters.regex("GetStatsNow") & ~app.bl_users)
async def get_stats_callback(_, query: types.CallbackQuery):
    """Handle stats data requests (Tracks/Users/Chats/Here)."""
    try:
        await query.answer()
    except:
        pass
    
    callback_data = query.data.strip()
    what = callback_data.split(None, 1)[1]
    chat_id = query.message.chat.id
    
    target = f"Grup {query.message.chat.title}" if what == "Here" else what
    await query.edit_message_caption(
        f"📊 <b>Top 10 {target}</b>",
        parse_mode=enums.ParseMode.HTML
    )
    
    # Fetch data based on type
    if what == "Tracks":
        stats = await db.get_global_tops()
    elif what == "Users":
        stats = await db.get_top_users()
    elif what == "Chats":
        stats = await db.get_top_chats()
    elif what == "Here":
        stats = await db.get_group_stats(chat_id)
    elif what == "UsersHere":
        stats = await db.get_group_top_users(chat_id)
    else:
        return
    
    if not stats:
        await asyncio.sleep(1)
        return await query.edit_message_caption(
            "Belum ada data statistik.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.back_stats_markup({})
        )
    
    # Build message
    msg = ""
    limit = 0
    total_plays = 0
    
    if what in ["Tracks", "Here"]:
        # Display tracks with enhanced formatting
        from anony.helpers import utils
        
        for track_id, data in list(stats.items())[:10]:
            limit += 1
            total_plays += data["spot"]
            title = data["title"][:35]
            count = data["spot"]
            
            # Medal for top 3
            rank_icon = utils.get_medal(limit)
            
            if track_id == "telegram":
                msg += f"{rank_icon} <a href='https://t.me/{config.SUPPORT_CHANNEL}'>Telegram Media</a> • <b>{utils.format_number(count)} plays</b>\n"
            else:
                msg += f"{rank_icon} <a href='https://www.youtube.com/watch?v={track_id}'>{title}</a> • <b>{utils.format_number(count)} plays</b>\n"
        
        if what == "Tracks":
            queries = await db.get_queries()
            header = f"🎵 <b>Statistik Global</b>\n\n"
            header += f"<blockquote>📊 <b>Total Queries:</b> {utils.format_number(queries)}\n"
            header += f"🎸 <b>Bot:</b> {app.name}\n"
            header += f"🎶 <b>Total Tracks:</b> {utils.format_number(len(stats))}\n"
            header += f"▶️ <b>Total Plays:</b> {utils.format_number(total_plays)}</blockquote>\n\n"
            header += f"<b>🏆 Top {limit} Most Played:</b>\n\n<blockquote>"
        else:
            header = f"📊 <b>Statistik Grup</b>\n\n"
            header += f"<blockquote>🎶 <b>Total Tracks:</b> {utils.format_number(len(stats))}\n"
            header += f"▶️ <b>Total Plays:</b> {utils.format_number(total_plays)}</blockquote>\n\n"
            header += f"<b>🏆 Top {limit} Lagu:</b>\n\n<blockquote>"
        msg = header + msg + "</blockquote>"
        
    elif what in ["Users", "Chats", "UsersHere"]:
        # Display users/chats with enhanced formatting
        from anony.helpers import utils
        
        # Calculate max for progress bar
        max_plays = max(stats.values()) if stats else 1
        
        for item_id, count in list(stats.items())[:10]:
            try:
                if what in ["Users", "UsersHere"]:
                    try:
                        user = await app.get_users(item_id)
                        extract = f"<a href='tg://user?id={item_id}'>{user.first_name}</a>"
                    except:
                        extract = "Deleted User"
                else:
                    try:
                        chat = await app.get_chat(item_id)
                        if chat.username:
                            extract = f"<a href='https://t.me/{chat.username}'>{chat.title}</a>"
                        else:
                            extract = f"<b>{chat.title}</b>"
                    except:
                        extract = "Deleted Group"
            except:
                continue
            
            limit += 1
            rank_icon = utils.get_medal(limit)
            progress = utils.progress_bar(count, max_plays, 8)
            
            msg += f"{rank_icon} {extract}\n"
            msg += f"   {progress} <b>{utils.format_number(count)} plays</b>\n\n"
        
        if what == "Users":
            header = f"👥 <b>Top {limit} User Teraktif di {app.name}:</b>\n\n<blockquote>"
        elif what == "UsersHere":
            header = f"👤 <b>Top {limit} Pengguna Teraktif di Grup Ini:</b>\n\n<blockquote>"
        else:
            header = f"📈 <b>Top {limit} Grup Teraktif di {app.name}:</b>\n\n<blockquote>"
        msg = header + msg + "</blockquote>"
    
    med = InputMediaPhoto(media=config.GLOBAL_IMG_URL, caption=msg, parse_mode=enums.ParseMode.HTML)
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.back_stats_markup({})
        )
    except:
        await query.message.reply_photo(
            photo=config.GLOBAL_IMG_URL,
            caption=msg,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.back_stats_markup({})
        )


@app.on_callback_query(filters.regex("TopOverall") & ~app.bl_users)
async def overall_stats_callback(_, query: types.CallbackQuery):
    """Display bot info and stats."""
    try:
        await query.answer()
    except:
        pass
    
    await query.edit_message_caption("Mengambil statistik bot...", parse_mode=enums.ParseMode.HTML)
    
    served_chats = len(await db.get_chats())
    served_users = len(await db.get_users())
    total_queries = await db.get_queries()
    blocked = len(db.blacklisted)
    sudoers = len(app.sudoers)
    mod = len(all_modules)
    assistant = len(userbot.clients)
    
    text = f"""🎵 <b>Statistik & Info Bot:</b>

<blockquote>🎵 <b>Modul:</b> {mod}
🎵 <b>Grup:</b> {served_chats}
🎵 <b>User:</b> {served_users}
🎵 <b>Diblokir:</b> {blocked}
🎵 <b>Sudoers:</b> {sudoers}

🎵 <b>Queries:</b> {total_queries}
🎵 <b>Assistant:</b> {assistant}
🎵 <b>Auto Leave:</b> {"Ya" if config.AUTO_LEAVE else "Tidak"}

🎵 <b>Durasi Limit:</b> {config.DURATION_LIMIT // 60} menit
🎵 <b>Playlist Limit:</b> {config.PLAYLIST_LIMIT}
🎵 <b>Queue Limit:</b> {config.QUEUE_LIMIT}</blockquote>"""
    
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text, parse_mode=enums.ParseMode.HTML)
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.overall_stats_markup({}, main=True)
        )
    except:
        await query.message.reply_photo(
            photo=config.STATS_IMG_URL,
            caption=text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.overall_stats_markup({}, main=True)
        )


@app.on_callback_query(filters.regex("bot_stats_sudo") & ~app.bl_users)
async def sudo_stats_callback(_, query: types.CallbackQuery):
    """System info for sudo users only."""
    if query.from_user.id not in app.sudoers:
        return await query.answer("Hanya untuk sudo users.", show_alert=True)
    
    try:
        await query.answer()
    except:
        pass
    
    await query.edit_message_caption("Mengambil system info...", parse_mode=enums.ParseMode.HTML)
    
    sc = platform.system()
    p_core = psutil.cpu_count(logical=False)
    t_core = psutil.cpu_count(logical=True)
    ram = f"{str(round(psutil.virtual_memory().total / (1024.0**3)))} GB"
    cpu_freq = psutil.cpu_freq().current
    if cpu_freq >= 1000:
        cpu_freq = f"{round(cpu_freq / 1000, 2)}GHz"
    else:
        cpu_freq = f"{round(cpu_freq, 2)}MHz"
    
    hdd = psutil.disk_usage("/")
    total_storage = round(hdd.total / (1024.0**3))
    used_storage = round(hdd.used / (1024.0**3))
    
    text = f"""⚙️ <b>System Information</b>

<blockquote><b>Platform:</b> {sc}
<b>RAM:</b> {ram}
<b>Physical Cores:</b> {p_core}
<b>Total Cores:</b> {t_core}
<b>CPU Frequency:</b> {cpu_freq}

<b>Storage Total:</b> {total_storage} GB
<b>Storage Used:</b> {used_storage} GB
<b>Storage Free:</b> {total_storage - used_storage} GB</blockquote>"""
    
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text, parse_mode=enums.ParseMode.HTML)
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.overall_stats_markup({})
        )
    except:
        await query.message.reply_photo(
            photo=config.STATS_IMG_URL,
            caption=text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.overall_stats_markup({})
        )


@app.on_callback_query(filters.regex("stats_back") & ~app.bl_users)
async def stats_back_callback(_, query: types.CallbackQuery):
    """Back button - return to main stats menu."""
    try:
        await query.answer()
    except:
        pass
    
    is_sudo = query.from_user.id in app.sudoers
    med = InputMediaPhoto(
        media=config.STATS_IMG_URL,
        caption=f"🎵 <b>Selamat Datang di Statistik {app.name}!</b>\n\n<blockquote>Pilih kategori statistik yang ingin dilihat:</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.stats_buttons({}, is_sudo)
        )
    except:
        await query.message.reply_photo(
            photo=config.STATS_IMG_URL,
            caption=f"🎵 <b>Selamat Datang di Statistik {app.name}!</b>\n\n<blockquote>Pilih kategori statistik yang ingin dilihat:</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons.stats_buttons({}, is_sudo)
        )
