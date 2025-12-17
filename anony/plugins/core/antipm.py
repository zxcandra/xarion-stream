# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic
# Auto Clear PM (No Block) for Assistant Accounts


import asyncio
from pyrogram import filters
from pyrogram.types import Message

from anony import config, db, userbot


# Store approved users (owner always approved)
APPROVED_USERS = set()

# Custom messages (loaded from database)
CUSTOM_PM_WARN = None
MESSAGES_LOADED = False

# Default message
DEFAULT_WARN_MSG = (
    "⚠️ **MOHON JANGAN SPAM!**\n\n"
    "Jangan kirim pesan ke akun assistant ini.\n"
    "Pesan Anda akan terhapus otomatis dalam 3 detik."
)


async def load_custom_messages():
    """Load custom PM messages from database."""
    global CUSTOM_PM_WARN, MESSAGES_LOADED
    
    if not MESSAGES_LOADED:
        messages = await db.get_pm_messages()
        CUSTOM_PM_WARN = messages.get("warn")
        MESSAGES_LOADED = True


# Auto Clear PM Handler
@userbot.one.on_message(filters.private & filters.incoming, group=1)
@userbot.two.on_message(filters.private & filters.incoming, group=1)
@userbot.three.on_message(filters.private & filters.incoming, group=1)
async def pm_auto_clear(client, message: Message):
    """Auto clear PM messages after 3 seconds without blocking."""
    
    # Load custom messages from database (once)
    await load_custom_messages()
    
    # Skip if anti-PM is disabled
    if not config.ANTI_PM_ENABLED:
        return
    
    user_id = message.from_user.id
    
    # Allow owner
    if user_id == config.OWNER_ID:
        return
    
    # Allow approved users
    if user_id in APPROVED_USERS:
        return
    
    # Send warning
    warn_msg = CUSTOM_PM_WARN if CUSTOM_PM_WARN else DEFAULT_WARN_MSG
    
    try:
        sent_warn = await message.reply_text(warn_msg)
    except:
        return
        
    # Wait 3 seconds
    await asyncio.sleep(3)
    
    # Delete BOTH messages (User's + Warning)
    try:
        await message.delete()  # Delete user message
    except:
        pass
        
    try:
        await sent_warn.delete() # Delete warning message
    except:
        pass


# Approve command (for owner only)
@userbot.one.on_message(filters.command("approve", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("approve", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("approve", prefixes=".") & filters.me)
async def approve_pm(client, message: Message):
    """Approve a user to PM (disable auto clear for them)."""
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        APPROVED_USERS.add(user_id)
        await message.reply_text(
            f"✅ <b>Approved!</b>\n\n<blockquote>User {message.reply_to_message.from_user.mention} telah diizinkan untuk PM.</blockquote>",
            parse_mode="html"
        )
    else:
        await message.reply_text(
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote>Reply ke pesan user untuk approve</blockquote>",
            parse_mode="html"
        )


# Disapprove command (for owner only)
@userbot.one.on_message(filters.command("disapprove", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("disapprove", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("disapprove", prefixes=".") & filters.me)
async def disapprove_pm(client, message: Message):
    """Disapprove a user (enable auto clear)."""
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        APPROVED_USERS.discard(user_id)
        await message.reply_text(
            f"❌ <b>Disapproved!</b>\n\n<blockquote>User {message.reply_to_message.from_user.mention} kembali ke mode auto-clear.</blockquote>",
            parse_mode="html"
        )
    else:
        await message.reply_text(
            "ℹ️ <b>Penggunaan:</b>\n\n<blockquote>Reply ke pesan user untuk disapprove</blockquote>",
            parse_mode="html"
        )


# Set custom warning message
@userbot.one.on_message(filters.command("setpmwarn", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("setpmwarn", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("setpmwarn", prefixes=".") & filters.me)
async def set_pm_warn(client, message: Message):
    """Set custom PM warning message."""
    global CUSTOM_PM_WARN
    
    if len(message.command) < 2:
        await message.reply_text(
            "ℹ️ <b>Set PM Warning</b>\n\n<blockquote><code>.setpmwarn [pesan]</code>\n\nContoh: <code>.setpmwarn ⚠️ Jangan spam!</code></blockquote>",
            parse_mode="html"
        )
        return
    
    custom_msg = message.text.split(maxsplit=1)[1]
    CUSTOM_PM_WARN = custom_msg
    await db.set_pm_warn_msg(custom_msg)
    await message.reply_text(
        f"✅ <b>Custom Warning Set!</b>\n\n<blockquote><b>Preview:</b>\n{custom_msg}</blockquote>",
        parse_mode="html"
    )


# Reset to default messages
@userbot.one.on_message(filters.command("resetpm", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("resetpm", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("resetpm", prefixes=".") & filters.me)
async def reset_pm_messages(client, message: Message):
    """Reset PM messages to default."""
    global CUSTOM_PM_WARN
    
    CUSTOM_PM_WARN = None
    await db.clear_pm_messages()
    await message.reply_text(
        "✅ <b>Reset Berhasil!</b>\n\n<blockquote>Pesan PM warning kembali ke default.</blockquote>",
        parse_mode="html"
    )


# PMPermit help command
@userbot.one.on_message(filters.command("pmhelp", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("pmhelp", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("pmhelp", prefixes=".") & filters.me)
async def pm_auto_help(client, message: Message):
    """Show Auto Clear PM help."""
    help_text = (
        "**🧹 Auto Clear PM (Tanpa Blokir)**\n\n"
        
        "**Cara Kerja:**\n"
        "• User PM → Bot kirim peringatan\n"
        "• Tunggu 3 detik\n"
        "• Hapus pesan user + peringatan\n"
        "• TIDAK ADA BLOKIR\n\n"
        
        "**Command:**\n"
        "• `.approve` - Whitelist user (chat tidak dihapus)\n"
        "• `.disapprove` - Kembalikan ke auto delete\n"
        "• `.setpmwarn` - Custom pesan peringatan\n"
        "• `.resetpm` - Reset ke pesan default"
    )
    
    new_help = (
        "🧹 <b>Auto Clear PM (Tanpa Blokir)</b>\n\n"
        "<blockquote><b>Cara Kerja:</b>\n"
        "• User PM → Bot kirim peringatan\n"
        "• Tunggu 3 detik\n"
        "• Hapus pesan user + peringatan\n"
        "• TIDAK ada blokir</blockquote>\n\n"
        "<b>Daftar Perintah:</b>\n"
        "• <code>.approve</code> - Whitelist user\n"
        "• <code>.disapprove</code> - Hapus whitelist\n"
        "• <code>.setpmwarn</code> - Custom pesan\n"
        "• <code>.resetpm</code> - Reset default"
    )
    
    await message.reply_text(new_help, parse_mode="html")
