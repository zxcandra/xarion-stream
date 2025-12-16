# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
import os
import platform
import psutil

from pyrogram import enums, filters, types
from pyrogram.types import InputMediaPhoto

from anony import app, config, db, lang, userbot
from anony.helpers import buttons
from anony.plugins import all_modules


@app.on_message(filters.command(["stats"]) & filters.group & ~app.bl_users)
@lang.language()
async def stats_command(_, m: types.Message):
    """Main stats command with button navigation."""
    is_sudo = m.from_user.id in app.sudoers
    await m.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=m.lang["gstats_11"].format(app.name),
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=buttons.stats_buttons(m.lang, is_sudo),
    )


@app.on_callback_query(filters.regex("GetStatsNow") & ~app.bl_users)
@lang.language()
async def get_stats_callback(_, query: types.CallbackQuery):
    """Handle stats data requests (Tracks/Users/Chats/Here)."""
    try:
        await query.answer()
    except:
        pass
    
    callback_data = query.data.strip()
    what = callback_data.split(None, 1)[1]
    chat_id = query.message.chat.id
    
    await query.edit_message_caption(
        query.lang["gstats_3"].format(
            f"Grup {query.message.chat.title}" if what == "Here" else what
        ),
        parse_mode=enums.ParseMode.MARKDOWN
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
    else:
        return
    
    if not stats:
        await asyncio.sleep(1)
        return await query.edit_message_caption(
            query.lang["gstats_2"],
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=buttons.back_stats_markup(query.lang)
        )
    
    # Build message
    msg = ""
    limit = 0
    total_plays = 0
    
    if what in ["Tracks", "Here"]:
        # Display tracks
        for track_id, data in list(stats.items())[:10]:
            limit += 1
            total_plays += data["spot"]
            title = data["title"][:35]
            count = data["spot"]
            
            if track_id == "telegram":
                msg += f"🎵 [Telegram Media](https://t.me/{config.SUPPORT_CHANNEL}) **dimainkan {count} kali**\n\n"
            else:
                msg += f"🎵 [{title}](https://www.youtube.com/watch?v={track_id}) **dimainkan {count} kali**\n\n"
        
        if what == "Tracks":
            queries = await db.get_queries()
            header = query.lang["gstats_4"].format(
                queries, app.name, len(stats), total_plays, limit
            )
        else:
            header = query.lang["gstats_7"].format(len(stats), total_plays, limit)
        msg = header + "\n" + msg
        
    elif what in ["Users", "Chats"]:
        # Display users/chats
        for item_id, count in list(stats.items())[:10]:
            try:
                if what == "Users":
                    extract = (await app.get_users(item_id)).first_name
                else:
                    extract = (await app.get_chat(item_id)).title
                await asyncio.sleep(0.5)
            except:
                continue
            
            limit += 1
            msg += f"💖 `{extract}` dimainkan {count} kali.\n\n"
        
        if what == "Users":
            header = query.lang["gstats_6"].format(limit, app.name)
        else:
            header = query.lang["gstats_5"].format(limit, app.name)
        msg = header + "\n" + msg
    
    med = InputMediaPhoto(media=config.GLOBAL_IMG_URL, caption=msg)
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.back_stats_markup(query.lang)
        )
    except:
        await query.message.reply_photo(
            photo=config.GLOBAL_IMG_URL,
            caption=msg,
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=buttons.back_stats_markup(query.lang)
        )


@app.on_callback_query(filters.regex("TopOverall") & ~app.bl_users)
@lang.language()
async def overall_stats_callback(_, query: types.CallbackQuery):
    """Display bot info and stats."""
    try:
        await query.answer()
    except:
        pass
    
    await query.edit_message_caption(query.lang["gstats_8"], parse_mode=enums.ParseMode.MARKDOWN)
    
    served_chats = len(await db.get_chats())
    served_users = len(await db.get_users())
    total_queries = await db.get_queries()
    blocked = len(db.blacklisted)
    sudoers = len(app.sudoers)
    mod = len(all_modules)
    assistant = len(userbot.clients)
    
    text = f"""🎵 **Statistik & Info Bot:**

🎵 **Modul:** {mod}
🎵 **Grup:** {served_chats}
🎵 **User:** {served_users}
🎵 **Diblokir:** {blocked}
🎵 **Sudoers:** {sudoers}

🎵 **Queries:** {total_queries}
🎵 **Assistant:** {assistant}
🎵 **Auto Leave:** {"Ya" if config.AUTO_LEAVE else "Tidak"}

🎵 **Durasi Limit:** {config.DURATION_LIMIT // 60} menit
🎵 **Playlist Limit:** {config.PLAYLIST_LIMIT}
🎵 **Queue Limit:** {config.QUEUE_LIMIT}"""
    
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.overall_stats_markup(query.lang, main=True)
        )
    except:
        await query.message.reply_photo(
            photo=config.STATS_IMG_URL,
            caption=text,
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=buttons.overall_stats_markup(query.lang, main=True)
        )


@app.on_callback_query(filters.regex("bot_stats_sudo") & ~app.bl_users)
@lang.language()
async def sudo_stats_callback(_, query: types.CallbackQuery):
    """System info for sudo users only."""
    if query.from_user.id not in app.sudoers:
        return await query.answer("Hanya untuk sudo users.", show_alert=True)
    
    try:
        await query.answer()
    except:
        pass
    
    await query.edit_message_caption("Mengambil system info...", parse_mode=enums.ParseMode.MARKDOWN)
    
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
    
    text = f"""⚙️ **System Information**

**Platform:** {sc}
**RAM:** {ram}
**Physical Cores:** {p_core}
**Total Cores:** {t_core}
**CPU Frequency:** {cpu_freq}

**Storage Total:** {total_storage} GB
**Storage Used:** {used_storage} GB
**Storage Free:** {total_storage - used_storage} GB"""
    
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.overall_stats_markup(query.lang)
        )
    except:
        await query.message.reply_photo(
            photo=config.STATS_IMG_URL,
            caption=text,
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=buttons.overall_stats_markup(query.lang)
        )


@app.on_callback_query(filters.regex("stats_back") & ~app.bl_users)
@lang.language()
async def stats_back_callback(_, query: types.CallbackQuery):
    """Back button - return to main stats menu."""
    try:
        await query.answer()
    except:
        pass
    
    is_sudo = query.from_user.id in app.sudoers
    med = InputMediaPhoto(
        media=config.STATS_IMG_URL,
        caption=query.lang["gstats_11"].format(app.name)
    )
    try:
        await query.edit_message_media(
            media=med,
            reply_markup=buttons.stats_buttons(query.lang, is_sudo)
        )
    except:
        await query.message.reply_photo(
            photo=config.STATS_IMG_URL,
            caption=query.lang["gstats_11"].format(app.name),
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=buttons.stats_buttons(query.lang, is_sudo)
        )
