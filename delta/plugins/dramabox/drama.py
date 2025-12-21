# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
DramaBox Command Handlers

Command untuk mengakses konten DramaBox dari Telegram.
"""

from pyrogram import enums, filters, types
from delta import app, anon, db, queue
from delta.helpers import Media, is_admin
from .api import dramabox, Drama, Episode


# ==================== HELPER FUNCTIONS ====================

def format_drama_list(dramas: list[Drama], title: str, emoji: str = "🎬") -> str:
    """Format daftar drama untuk ditampilkan."""
    text = f"{emoji} <b>{title}</b>\n\n"
    
    for i, drama in enumerate(dramas[:10], 1):
        # Limit tags to 2 for cleaner display
        tags_str = ", ".join(drama.tags[:2]) if drama.tags else "-"
        hot = f"🔥{drama.hot_code}" if drama.hot_code else ""
        
        # Title with hot code on same line
        title_line = f"<b>{i}.</b> {drama.title}"
        if hot:
            title_line += f" {hot}"
        
        text += f"{title_line}\n"
        text += f"    📺 {drama.chapter_count} Eps • {tags_str}\n\n"
    
    text += "<i>💡 Pilih nomor di bawah untuk lihat detail</i>"
    return text


def format_drama_detail(drama: Drama) -> str:
    """Format detail drama."""
    tags_str = " • ".join(drama.tags[:5]) if drama.tags else "-"
    
    text = f"🎬 <b>{drama.title}</b>\n\n"
    text += f"<blockquote>"
    text += f"📺 <b>Episode:</b> {drama.chapter_count}\n"
    text += f"👥 <b>Pemeran:</b> {drama.protagonist}\n"
    text += f"🏷️ <b>Tags:</b> {tags_str}\n\n"
    text += f"📖 {drama.introduction[:300]}{'...' if len(drama.introduction) > 300 else ''}"
    text += f"</blockquote>"
    
    return text


def create_episode_keyboard(episodes: list[Episode], book_id: str, page: int = 0) -> types.InlineKeyboardMarkup:
    """Membuat keyboard untuk memilih episode dengan pagination."""
    eps_per_page = 10
    start = page * eps_per_page
    end = start + eps_per_page
    page_episodes = episodes[start:end]
    total_pages = (len(episodes) + eps_per_page - 1) // eps_per_page
    
    buttons = []
    row = []
    for ep in page_episodes:
        emoji = "🔒 " if ep.is_paid else ""
        btn_text = f"{emoji}EP {ep.chapter_index + 1}"
        row.append(types.InlineKeyboardButton(
            text=btn_text,
            callback_data=f"drama_ep:{book_id}:{ep.chapter_index}"
        ))
        if len(row) == 5:  # 5 tombol per baris
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(types.InlineKeyboardButton("◀️ Prev", callback_data=f"drama_page:{book_id}:{page-1}"))
    
    nav_row.append(types.InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    
    if end < len(episodes):
        nav_row.append(types.InlineKeyboardButton("Next ▶️", callback_data=f"drama_page:{book_id}:{page+1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Back button
    buttons.append([types.InlineKeyboardButton("❌ Tutup", callback_data="drama_close")])
    
    return types.InlineKeyboardMarkup(buttons)


def create_quality_keyboard(episode: Episode, book_id: str) -> types.InlineKeyboardMarkup:
    """Membuat keyboard untuk memilih kualitas video."""
    buttons = []
    
    # Sort qualities in descending order
    qualities = sorted(episode.video_urls.keys(), key=lambda x: int(x.replace('p', '')), reverse=True)
    
    row = []
    for quality in qualities:
        emoji = "🎬" if quality in ["1080p", "720p"] else "📹"
        row.append(types.InlineKeyboardButton(
            text=f"{emoji} {quality}",
            callback_data=f"drama_play:{book_id}:{episode.chapter_index}:{quality}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    # Back button
    buttons.append([
        types.InlineKeyboardButton("◀️ Kembali", callback_data=f"drama_back:{book_id}"),
        types.InlineKeyboardButton("❌ Tutup", callback_data="drama_close")
    ])
    
    return types.InlineKeyboardMarkup(buttons)


def create_numbered_drama_keyboard(dramas: list[Drama], page: int = 0, search_type: str = "trending") -> types.InlineKeyboardMarkup:
    """Membuat keyboard dengan tombol nomor 1-10 dan pagination."""
    items_per_page = 10
    start = page * items_per_page
    end = start + items_per_page
    page_dramas = dramas[start:end]
    total_pages = (len(dramas) + items_per_page - 1) // items_per_page
    
    buttons = []
    row = []
    
    for i, drama in enumerate(page_dramas, start=start + 1):
        row.append(types.InlineKeyboardButton(
            text=str(i),
            callback_data=f"drama_info:{drama.book_id}"
        ))
        if len(row) == 4:  # 4 tombol per baris
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    # Navigation buttons
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(types.InlineKeyboardButton("◀️", callback_data=f"drama_list:{search_type}:{page-1}"))
        
        nav_row.append(types.InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
        
        if end < len(dramas):
            nav_row.append(types.InlineKeyboardButton("▶️", callback_data=f"drama_list:{search_type}:{page+1}"))
        
        buttons.append(nav_row)
    
    buttons.append([types.InlineKeyboardButton("❌ Tutup", callback_data="drama_close")])
    
    return types.InlineKeyboardMarkup(buttons)


# ==================== COMMAND HANDLERS ====================

@app.on_message(filters.command(["drama", "dramabox"]) & ~app.bl_users)
async def drama_command(_, message: types.Message):
    """Mencari drama atau menampilkan trending jika tanpa query."""
    
    # Check Admin Only Mode (skip in private chat)
    if message.chat.type != enums.ChatType.PRIVATE:
        if await db.get_drama_mode(message.chat.id):
            if message.from_user and not await is_admin(message.chat.id, message.from_user.id):
                return await message.reply_text("❌ <b>Maaf, fitur ini khusus Admin di grup ini.</b>", parse_mode=enums.ParseMode.HTML)
    
    if len(message.command) < 2:
        # Tampilkan trending
        mystic = await message.reply_text("⏳ <b>Memuat drama trending...</b>", parse_mode=enums.ParseMode.HTML)
        
        dramas = await dramabox.get_trending()
        if not dramas:
            return await mystic.edit_text("❌ <b>Gagal memuat data</b>", parse_mode=enums.ParseMode.HTML)
        
        text = format_drama_list(dramas, "Drama Trending", "🔥")
        keyboard = create_numbered_drama_keyboard(dramas, 0, "trending")
        
        return await mystic.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    
    # Pencarian drama
    query = message.text.split(None, 1)[1]
    mystic = await message.reply_text(f"🔍 <b>Mencari:</b> <code>{query}</code>...", parse_mode=enums.ParseMode.HTML)
    
    dramas = await dramabox.search(query)
    if not dramas:
        return await mystic.edit_text(
            f"❌ <b>Tidak Ditemukan</b>\n\n<blockquote>Drama dengan kata kunci '{query}' tidak ditemukan</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
    
    text = format_drama_list(dramas, f"Hasil Pencarian: {query}", "🔍")
    keyboard = create_numbered_drama_keyboard(dramas, 0, f"search:{query}")
    
    await mystic.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_message(filters.command(["dramatrending", "dt"]) & ~app.bl_users)
async def drama_trending_command(_, message: types.Message):
    """Menampilkan drama trending."""
    
    # Check Admin Only Mode (skip in private chat)
    if message.chat.type != enums.ChatType.PRIVATE:
        if await db.get_drama_mode(message.chat.id):
            if message.from_user and not await is_admin(message.chat.id, message.from_user.id):
                return await message.reply_text("❌ <b>Maaf, fitur ini khusus Admin di grup ini.</b>", parse_mode=enums.ParseMode.HTML)
            
    mystic = await message.reply_text("⏳ <b>Memuat drama trending...</b>", parse_mode=enums.ParseMode.HTML)
    
    dramas = await dramabox.get_trending()
    if not dramas:
        return await mystic.edit_text("❌ <b>Gagal memuat data</b>", parse_mode=enums.ParseMode.HTML)
    
    text = format_drama_list(dramas, "Drama Trending", "🔥")
    keyboard = create_numbered_drama_keyboard(dramas, 0, "trending")
    
    await mystic.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_message(filters.command(["dramaterbaru", "dn"]) & ~app.bl_users)
async def drama_latest_command(_, message: types.Message):
    """Menampilkan drama terbaru."""
    
    # Check Admin Only Mode (skip in private chat)
    if message.chat.type != enums.ChatType.PRIVATE:
        if await db.get_drama_mode(message.chat.id):
            if message.from_user and not await is_admin(message.chat.id, message.from_user.id):
                return await message.reply_text("❌ <b>Maaf, fitur ini khusus Admin di grup ini.</b>", parse_mode=enums.ParseMode.HTML)
            
    mystic = await message.reply_text("⏳ <b>Memuat drama terbaru...</b>", parse_mode=enums.ParseMode.HTML)
    
    dramas = await dramabox.get_latest()
    if not dramas:
        return await mystic.edit_text("❌ <b>Gagal memuat data</b>", parse_mode=enums.ParseMode.HTML)
    
    text = format_drama_list(dramas, "Drama Terbaru", "🆕")
    keyboard = create_numbered_drama_keyboard(dramas, 0, "latest")
    
    await mystic.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


# ==================== CALLBACK HANDLERS ====================

@app.on_callback_query(filters.regex(r"^drama_info:"))
async def drama_info_callback(_, callback: types.CallbackQuery):
    """Menampilkan detail drama dan daftar episode."""
    book_id = callback.data.split(":")[1]
    
    await callback.answer("⏳ Memuat...")
    
    # Ambil episode untuk mendapatkan info
    episodes = await dramabox.get_all_episodes(book_id)
    if not episodes:
        return await callback.answer("❌ Gagal memuat episode", show_alert=True)
    
    # Cari drama dari trending/latest untuk info tambahan
    dramas = await dramabox.get_trending()
    drama = next((d for d in dramas if d.book_id == book_id), None)
    
    if not drama:
        dramas = await dramabox.get_latest()
        drama = next((d for d in dramas if d.book_id == book_id), None)
    
    if drama:
        text = format_drama_detail(drama)
        text += f"\n\n📺 <b>Pilih Episode:</b> (Total: {len(episodes)})"
    else:
        text = f"📺 <b>Drama</b>\n\n<blockquote>Total Episode: {len(episodes)}\n\nPilih episode untuk menonton:</blockquote>"
    
    keyboard = create_episode_keyboard(episodes, book_id)
    
    if drama and drama.cover:
        try:
            await callback.message.delete()
            await callback.message.reply_photo(
                photo=drama.cover,
                caption=text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=keyboard
            )
            return
        except:
            pass
            
    await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^drama_page:"))
async def drama_page_callback(_, callback: types.CallbackQuery):
    """Handle pagination episode."""
    parts = callback.data.split(":")
    book_id = parts[1]
    page = int(parts[2])
    
    await callback.answer()
    
    episodes = await dramabox.get_all_episodes(book_id)
    if not episodes:
        return await callback.answer("❌ Gagal memuat data", show_alert=True)
    
    keyboard = create_episode_keyboard(episodes, book_id, page)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^drama_ep:"))
async def drama_episode_callback(_, callback: types.CallbackQuery):
    """Menampilkan pilihan kualitas untuk episode."""
    parts = callback.data.split(":")
    book_id = parts[1]
    ep_index = int(parts[2])
    
    await callback.answer("⏳ Memuat kualitas...")
    
    episodes = await dramabox.get_all_episodes(book_id)
    if not episodes or ep_index >= len(episodes):
        return await callback.answer("❌ Episode tidak ditemukan", show_alert=True)
    
    episode = episodes[ep_index]
    
    if episode.is_paid and not episode.video_urls:
        return await callback.answer("🔒 Episode ini berbayar", show_alert=True)
    
    if not episode.video_urls:
        return await callback.answer("❌ Link tidak tersedia", show_alert=True)
    
    text = f"🎬 <b>{episode.chapter_name}</b>\n\n"
    text += "<blockquote>Pilih kualitas video yang diinginkan:</blockquote>"
    
    keyboard = create_quality_keyboard(episode, book_id)
    
    if callback.message.photo:
        await callback.message.edit_caption(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^drama_play:"))
async def drama_play_callback(_, callback: types.CallbackQuery):
    """Mengirimkan link streaming."""
    parts = callback.data.split(":")
    book_id = parts[1]
    ep_index = int(parts[2])
    quality = parts[3]
    
    await callback.answer("⏳ Menyiapkan link...")
    
    episodes = await dramabox.get_all_episodes(book_id)
    if not episodes or ep_index >= len(episodes):
        return await callback.answer("❌ Episode tidak ditemukan", show_alert=True)
    
    episode = episodes[ep_index]
    video_url = episode.video_urls.get(quality)
    
    if not video_url:
        return await callback.answer("❌ Kualitas tidak tersedia", show_alert=True)
    
    text = f"🎬 <b>{episode.chapter_name}</b> [{quality}]\n\n"
    text += f"<blockquote>🔗 Link streaming siap!\n\n"
    text += f"⚠️ Link expired dalam beberapa jam.\n"
    text += f"Klik tombol di bawah untuk menonton.</blockquote>"
    
    # Check if private chat (bot DM)
    is_private = callback.message.chat.type == enums.ChatType.PRIVATE
    
    if is_private:
        # Bot DM: Download options only
        keyboard = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("📥 Unduh", callback_data=f"drama_download:{book_id}:{ep_index}:{quality}"),
                types.InlineKeyboardButton("📥 Unduh di Browser", url=video_url)
            ],
            [types.InlineKeyboardButton("◀️ Kembali", callback_data=f"drama_ep:{book_id}:{ep_index}")]
        ])
    else:
        # Group: Play + Download
        keyboard = types.InlineKeyboardMarkup([
            [
                types.InlineKeyboardButton("▶️ Putar", callback_data=f"drama_stream:{book_id}:{ep_index}:{quality}"),
                types.InlineKeyboardButton("📥 Unduh", callback_data=f"drama_download:{book_id}:{ep_index}:{quality}")
            ],
            [types.InlineKeyboardButton("🌐 Nonton di Browser", url=video_url)],
            [types.InlineKeyboardButton("◀️ Kembali", callback_data=f"drama_ep:{book_id}:{ep_index}")]
        ])
    
    if callback.message.photo:
        await callback.message.edit_caption(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^drama_stream:"))
async def drama_stream_callback(_, callback: types.CallbackQuery):
    """Memutar episode di Voice Chat."""
    parts = callback.data.split(":")
    book_id = parts[1]
    ep_index = int(parts[2])
    quality = parts[3]
    
    await callback.answer("⏳ Memproses stream...")
    
    episodes = await dramabox.get_all_episodes(book_id)
    if not episodes or ep_index >= len(episodes):
        return await callback.answer("❌ Episode tidak ditemukan", show_alert=True)
    
    episode = episodes[ep_index]
    video_url = episode.video_urls.get(quality)
    
    if not video_url:
        return await callback.answer("❌ Kualitas tidak tersedia", show_alert=True)
        
    chat_id = callback.message.chat.id
    user_mention = callback.from_user.mention
    
    # Construct Media object
    media = Media(
        id=f"drama_{book_id}_{ep_index}",
        duration="Live",
        duration_sec=0,
        file_path=video_url,
        message_id=0,
        title=f"{episode.chapter_name} [{quality}]",
        url=video_url,
        user=user_mention,
        video=True
    )
    
    # Check if a call is active
    if await db.get_call(chat_id):
        position = queue.add(chat_id, media)
        await callback.message.reply_text(
            f"✅ <b>Ditambahkan ke Antrian: #{position}</b>\n\n"
            f"<blockquote><b>Judul:</b> {media.title}\n"
            f"<b>Diminta oleh:</b> {user_mention}</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        return
        
    # Start new stream
    msg = await callback.message.reply_text("🔄 <b>Memproses stream...</b>", parse_mode=enums.ParseMode.HTML)
    media.message_id = msg.id
    await anon.play_media(chat_id=chat_id, message=msg, media=media)


@app.on_callback_query(filters.regex(r"^drama_download:"))
async def drama_download_callback(_, callback: types.CallbackQuery):
    """Mengunduh episode drama."""
    import aiohttp
    import os
    import asyncio
    
    parts = callback.data.split(":")
    book_id = parts[1]
    ep_index = int(parts[2])
    quality = parts[3]
    
    await callback.answer("⏳ Memulai unduhan...")
    
    episodes = await dramabox.get_all_episodes(book_id)
    if not episodes or ep_index >= len(episodes):
        return await callback.answer("❌ Episode tidak ditemukan", show_alert=True)
    
    episode = episodes[ep_index]
    video_url = episode.video_urls.get(quality)
    
    if not video_url:
        return await callback.answer("❌ Kualitas tidak tersedia", show_alert=True)
        
    # Mencari judul drama untuk filename
    dramas = await dramabox.get_trending()
    drama = next((d for d in dramas if d.book_id == book_id), None)
    
    if not drama:
        dramas = await dramabox.get_latest()
        drama = next((d for d in dramas if d.book_id == book_id), None)
        
    drama_title = drama.title if drama else "DramaBox"
    
    # Bersihkan filename
    safe_title = "".join(x for x in drama_title if x.isalnum() or x in [' ', '-', '_']).strip()
    safe_ep = "".join(x for x in episode.chapter_name if x.isalnum() or x in [' ', '-', '_']).strip()
    filename = f"{safe_title} - {safe_ep} - {quality}.mp4"
    
    msg = await callback.message.reply_text(
        f"⬇️ <b>Sedang Mengunduh</b>\n\n"
        f"<blockquote>"
        f"🎬 {drama_title}\n"
        f"📺 {episode.chapter_name}\n"
        f"💿 {quality}\n\n"
        f"⏳ Mohon tunggu, proses download sedang berjalan..."
        f"</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
    
    # Download file locally first - use final filename directly
    downloads_dir = "downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    local_path = os.path.join(downloads_dir, filename)
    
    try:
        # Download dari URL
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):  # 1MB chunks
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress every 10MB
                        if downloaded % (10 * 1024 * 1024) < 1024 * 1024:
                            progress = (downloaded / total_size * 100) if total_size > 0 else 0
                            size_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            try:
                                await msg.edit_text(
                                    f"⬇️ <b>Sedang Mengunduh</b>\n\n"
                                    f"<blockquote>"
                                    f"🎬 {drama_title}\n"
                                    f"📺 {episode.chapter_name}\n"
                                    f"💿 {quality}\n\n"
                                    f"📊 Progress: <code>{progress:.1f}%</code>\n"
                                    f"📦 Size: <code>{size_mb:.1f} MB / {total_mb:.1f} MB</code>"
                                    f"</blockquote>",
                                    parse_mode=enums.ParseMode.HTML
                                )
                            except:
                                pass
        
        # Upload ke Telegram
        await msg.edit_text(
            f"⬆️ <b>Mengirim ke Telegram</b>\n\n"
            f"<blockquote>"
            f"🎬 {drama_title}\n"
            f"📺 {episode.chapter_name}\n"
            f"💿 {quality}\n\n"
            f"⏳ Sedang mengunggah file..."
            f"</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        
        await callback.message.reply_video(
            video=local_path,
            caption=f"🎬 <b>{drama_title}</b>\n📺 {episode.chapter_name}\n💿 {quality}",
            supports_streaming=True,
            parse_mode=enums.ParseMode.HTML
        )
        
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text(f"❌ <b>Gagal mengirim file.</b>\n\nError: {str(e)}", parse_mode=enums.ParseMode.HTML)
    finally:
        # Cleanup
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass




@app.on_callback_query(filters.regex(r"^drama_back:"))
async def drama_back_callback(_, callback: types.CallbackQuery):
    """Kembali ke daftar episode."""
    book_id = callback.data.split(":")[1]
    
    await callback.answer()
    
    episodes = await dramabox.get_all_episodes(book_id)
    if not episodes:
        return await callback.answer("❌ Gagal memuat data", show_alert=True)
    
    text = f"📺 <b>Pilih Episode:</b> (Total: {len(episodes)})"
    keyboard = create_episode_keyboard(episodes, book_id)
    
    if callback.message.photo:
        await callback.message.edit_caption(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^drama_close$"))
async def drama_close_callback(_, callback: types.CallbackQuery):
    """Menutup/hapus pesan."""
    await callback.answer()
    await callback.message.delete()


@app.on_callback_query(filters.regex(r"^drama_list:"))
async def drama_list_callback(_, callback: types.CallbackQuery):
    """Handle drama list pagination."""
    parts = callback.data.split(":")
    search_type = parts[1]
    page = int(parts[2])
    
    await callback.answer()
    
    # Fetch dramas based on search type
    if search_type == "trending":
        dramas = await dramabox.get_trending()
        title = "Drama Trending"
        emoji = "🔥"
    elif search_type == "latest":
        dramas = await dramabox.get_latest()
        title = "Drama Terbaru"
        emoji = "🆕"
    elif search_type.startswith("search:"):
        query = search_type.split(":", 1)[1]
        dramas = await dramabox.search(query)
        title = f"Hasil Pencarian: {query}"
        emoji = "🔍"
    else:
        return await callback.answer("❌ Tipe tidak valid", show_alert=True)
    
    if not dramas:
        return await callback.answer("❌ Gagal memuat data", show_alert=True)
    
    text = format_drama_list(dramas, title, emoji)
    keyboard = create_numbered_drama_keyboard(dramas, page, search_type)
    
    await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)



@app.on_callback_query(filters.regex(r"^noop$"))
async def noop_callback(_, callback: types.CallbackQuery):
    """No operation callback."""
    await callback.answer()
