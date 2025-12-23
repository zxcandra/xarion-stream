# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
import os
import platform
import psutil

from pyrogram import enums, filters, types
from pyrogram.types import InputMediaPhoto

from delta import app, config, db, userbot
from delta.helpers import buttons
from delta.plugins import all_modules


@app.on_message(filters.command(["stats"]) & filters.group & ~app.bl_users)
async def stats_command(_, m: types.Message):
    """Main stats command with button navigation."""
    from delta.helpers import utils
    
    is_sudo = m.from_user.id in app.sudoers
    chat_id = m.chat.id
    
    # Get current group stats
    group_tracks = await db.get_group_stats(chat_id)
    
    total_tracks = len(group_tracks)
    total_plays = sum(track["spot"] for track in group_tracks.values())
    
    # Get top user
    top_user_text = ""
    # Get top user (fetch more to filter bots)
    group_users = await db.get_group_top_users(chat_id, limit=5)
    
    if group_users:
        # Identify excluded IDs (Bot and Assistants)
        excluded_ids = {app.id}
        for client in userbot.clients:
            if hasattr(client, 'id'):
                excluded_ids.add(client.id)
            elif hasattr(client, 'me') and client.me:
                excluded_ids.add(client.me.id)

        for user_id, plays in group_users.items():
            if user_id in excluded_ids:
                continue
                
            try:
                user = await app.get_users(user_id)
                top_user_text = f"\n👤 <b>Top User:</b> <a href='tg://user?id={user_id}'>{user.first_name}</a> ({utils.format_number(plays)} plays)"
                break
            except:
                continue
    
    # Get group ranking
    all_groups = await db.get_top_chats(limit=1000)
    group_rank = "N/A"
    if chat_id in all_groups:
        rank_position = list(all_groups.keys()).index(chat_id) + 1
        total_groups = len(all_groups)
        group_rank = f"#{rank_position} dari {total_groups}"
    
    caption = f"""📊 <b>Statistik {m.chat.title}</b>

<blockquote>🏆 <b>Ranking Global:</b> {group_rank}
🎶 <b>Total Tracks:</b> {utils.format_number(total_tracks)}
▶️ <b>Total Plays:</b> {utils.format_number(total_plays)}{top_user_text}</blockquote>

<i>Klik tombol di bawah untuk detail lengkap</i>"""
    
    await m.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons.stats_buttons({}, is_sudo),
    )


@app.on_callback_query(filters.regex("GetStatsNow") & ~app.bl_users)
async def get_stats_callback(_, query: types.CallbackQuery):
    """Handle stats data requests (Artists/Users/Chats/Here)."""
    try:
        await query.answer()
    except:
        pass
    
    callback_data = query.data.strip()
    what = callback_data.split(None, 1)[1]
    chat_id = query.message.chat.id
    
    # Menyesuaikan label target (Tracks diganti Artist)
    target_display = "Artist" if what == "Tracks" else what
    target = f"Grup {query.message.chat.title}" if what == "Here" else target_display
    
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
    from delta.helpers import utils

    if what in ["Tracks", "Here"]:
        # LOGIKA BARU: TOP ARTIST (MENGELOMPOKKAN TRACKS BERDASARKAN ARTIST)
        artist_counts = {}
        for track_id, data in stats.items():
            title = data.get("title", "Unknown")
            # Memisahkan nama artis (Contoh: "Artis - Judul" -> "Artis")
            if " - " in title:
                artist_name = title.split(" - ")[0].strip()
            else:
                artist_name = "Various Artist"
            
            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + data["spot"]
            total_plays += data["spot"]

        # Sort artis berdasarkan play terbanyak
        sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        for artist, plays in sorted_artists:
            limit += 1
            rank_icon = utils.get_medal(limit)
            msg += f"{rank_icon} <b>{artist}</b> • <b>{utils.format_number(plays)} plays</b>\n"
        
        if what == "Tracks":
            queries = await db.get_queries()
            header = f"👨‍🎤 <b>Top Artist Global</b>\n\n"
            header += f"<blockquote>📊 <b>Total Queries:</b> {utils.format_number(queries)}\n"
            header += f"🎸 <b>Bot:</b> {app.name}\n"
            header += f"🎶 <b>Total Artists:</b> {utils.format_number(len(artist_counts))}\n"
            header += f"▶️ <b>Total Plays:</b> {utils.format_number(total_plays)}</blockquote>\n\n"
            header += f"<b>🏆 Top {limit} Most Played Artists:</b>\n\n<blockquote>"
        else:
            header = f"👨‍🎤 <b>Top Artist Grup</b>\n\n"
            header += f"<blockquote>🎶 <b>Total Artists:</b> {utils.format_number(len(artist_counts))}\n"
            header += f"▶️ <b>Total Plays:</b> {utils.format_number(total_plays)}</blockquote>\n\n"
            header += f"<b>🏆 Top {limit} Artis Terpopuler:</b>\n\n<blockquote>"
        msg = header + msg + "</blockquote>"
        
    elif what in ["Users", "Chats", "UsersHere"]:
        # Display users/chats with enhanced formatting
        max_plays = max(stats.values()) if stats else 1
        
        # Identify excluded IDs (Bot and Assistants)
        excluded_ids = {app.id}
        for client in userbot.clients:
            if hasattr(client, 'id'):
                excluded_ids.add(client.id)
            elif hasattr(client, 'me') and client.me:
                excluded_ids.add(client.me.id)

        for item_id, count in list(stats.items()):
            if what in ["Users", "UsersHere"] and item_id in excluded_ids:
                continue
                
            if limit >= 10:
                break
            try:
                if what in ["Users", "UsersHere"]:
                    try:
                        user_id_int = int(item_id)
                        user = await app.get_users(user_id_int)
                        extract = f"<a href='tg://user?id={user_id_int}'>{user.first_name}</a>"
                    except:
                        try:
                            user_id_int = int(item_id)
                            extract = f"<a href='tg://user?id={user_id_int}'>User {user_id_int}</a>"
                        except:
                            continue
                else:
                    try:
                        chat = await app.get_chat(item_id)
                        if chat.username:
                            extract = f"<a href='https://t.me/{chat.username}'>{chat.title}</a>"
                        else:
                            extract = f"<b>{chat.title}</b>"
                    except:
                        continue
            except:
                continue
            
            limit += 1
            rank_icon = utils.get_medal(limit)
            progress = utils.progress_bar(count, max_plays, 8)
            
            msg += f"{rank_icon} {extract}\n"
            msg += f"   {progress} <b>{utils.format_number(count)} plays</b>\n\n"
        
        if what == "Users":
            header = f"🌟 <b>Top {limit} User Teraktif (Global):</b>\n\n<blockquote>"
        elif what == "UsersHere":
            header = f"👤 <b>Top {limit} Pengguna Teraktif di Grup Ini:</b>\n\n<blockquote>"
        else:
            header = f"🌍 <b>Top {limit} Grup Teraktif (Global):</b>\n\n<blockquote>"
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
    
    from delta.helpers import utils
    
    served_chats = len(await db.get_chats())
    served_users = len(await db.get_users())
    total_queries = await db.get_queries()
    blocked = len(db.blacklisted)
    sudoers = len(app.sudoers)
    mod = len(all_modules)
    assistant = len(userbot.clients)
    
    text = f"""🤖 <b>Statistik & Info Bot:</b>

<blockquote>📦 <b>Modul:</b> {mod}
💬 <b>Grup:</b> {served_chats}
👥 <b>User:</b> {served_users}
🚫 <b>Diblokir:</b> {blocked}
⚡ <b>Sudoers:</b> {sudoers}

🔢 <b>Queries:</b> {utils.format_number(total_queries)}
🤖 <b>Assistant:</b> {assistant}
🚪 <b>Auto Leave:</b> {"✅ Ya" if config.AUTO_LEAVE else "❌ Tidak"}

⏱️ <b>Durasi Limit:</b> {config.DURATION_LIMIT // 60} menit
📋 <b>Playlist Limit:</b> {config.PLAYLIST_LIMIT}
📝 <b>Queue Limit:</b> {config.QUEUE_LIMIT}</blockquote>"""
    
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


@app.on_callback_query(filters.regex("stats_close") & ~app.bl_users)
async def stats_close_callback(_, query: types.CallbackQuery):
    """Close button - delete stats message."""
    try:
        await query.message.delete()
    except:
        pass
