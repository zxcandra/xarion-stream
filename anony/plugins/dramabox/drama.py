# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

"""
DramaBox Command Handlers

Command untuk mengakses konten DramaBox dari Telegram.
"""

from pyrogram import enums, filters, types
from anony import app, anon, db, queue
from anony.helpers import Media
from .api import dramabox, Drama, Episode


# ==================== HELPER FUNCTIONS ====================

def format_drama_list(dramas: list[Drama], title: str, emoji: str = "🎬") -> str:
    """Format daftar drama untuk ditampilkan."""
    text = f"{emoji} <b>{title}</b>\n\n"
    
    for i, drama in enumerate(dramas[:10], 1):
        tags_str = ", ".join(drama.tags[:3]) if drama.tags else "-"
        hot = f" 🔥{drama.hot_code}" if drama.hot_code else ""
        text += f"<b>{i}.</b> <code>{drama.title}</code>{hot}\n"
        text += f"   └ 📺 {drama.chapter_count} Episode • {tags_str}\n\n"
    
    text += "<blockquote>💡 Gunakan <code>/drama [judul]</code> untuk mencari drama</blockquote>"
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
        emoji = "🔒" if ep.is_paid else "▶️"
        btn_text = f"{emoji} EP {ep.chapter_index + 1}"
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


def create_drama_results_keyboard(dramas: list[Drama]) -> types.InlineKeyboardMarkup:
    """Membuat keyboard untuk hasil pencarian drama."""
    buttons = []
    
    for drama in dramas[:8]:  # Limit 8 hasil
        buttons.append([types.InlineKeyboardButton(
            text=f"📺 {drama.title[:40]}{'...' if len(drama.title) > 40 else ''}",
            callback_data=f"drama_info:{drama.book_id}"
        )])
    
    buttons.append([types.InlineKeyboardButton("❌ Tutup", callback_data="drama_close")])
    
    return types.InlineKeyboardMarkup(buttons)


# ==================== COMMAND HANDLERS ====================

@app.on_message(filters.command(["drama", "dramabox"]) & ~app.bl_users)
async def drama_command(_, message: types.Message):
    """Mencari drama atau menampilkan trending jika tanpa query."""
    
    if len(message.command) < 2:
        # Tampilkan trending
        mystic = await message.reply_text("⏳ <b>Memuat drama trending...</b>", parse_mode=enums.ParseMode.HTML)
        
        dramas = await dramabox.get_trending()
        if not dramas:
            return await mystic.edit_text("❌ <b>Gagal memuat data</b>", parse_mode=enums.ParseMode.HTML)
        
        text = format_drama_list(dramas, "Drama Trending", "🔥")
        keyboard = create_drama_results_keyboard(dramas)
        
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
    keyboard = create_drama_results_keyboard(dramas)
    
    await mystic.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_message(filters.command(["dramatrending", "dt"]) & ~app.bl_users)
async def drama_trending_command(_, message: types.Message):
    """Menampilkan drama trending."""
    mystic = await message.reply_text("⏳ <b>Memuat drama trending...</b>", parse_mode=enums.ParseMode.HTML)
    
    dramas = await dramabox.get_trending()
    if not dramas:
        return await mystic.edit_text("❌ <b>Gagal memuat data</b>", parse_mode=enums.ParseMode.HTML)
    
    text = format_drama_list(dramas, "Drama Trending", "🔥")
    keyboard = create_drama_results_keyboard(dramas)
    
    await mystic.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_message(filters.command(["dramaterbaru", "dn"]) & ~app.bl_users)
async def drama_latest_command(_, message: types.Message):
    """Menampilkan drama terbaru."""
    mystic = await message.reply_text("⏳ <b>Memuat drama terbaru...</b>", parse_mode=enums.ParseMode.HTML)
    
    dramas = await dramabox.get_latest()
    if not dramas:
        return await mystic.edit_text("❌ <b>Gagal memuat data</b>", parse_mode=enums.ParseMode.HTML)
    
    text = format_drama_list(dramas, "Drama Terbaru", "🆕")
    keyboard = create_drama_results_keyboard(dramas)
    
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
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)


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
    
    keyboard = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("▶️ Tonton Sekarang", url=video_url)],
        [types.InlineKeyboardButton("🎵 Stream di Voice Chat", callback_data=f"drama_stream:{book_id}:{ep_index}:{quality}")],
        [types.InlineKeyboardButton("◀️ Kembali", callback_data=f"drama_ep:{book_id}:{ep_index}")]
    ])
    
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
    
    await callback.message.edit_text(text, parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^drama_close$"))
async def drama_close_callback(_, callback: types.CallbackQuery):
    """Menutup/hapus pesan."""
    await callback.answer()
    await callback.message.delete()


@app.on_callback_query(filters.regex(r"^noop$"))
async def noop_callback(_, callback: types.CallbackQuery):
    """No operation callback."""
    await callback.answer()
