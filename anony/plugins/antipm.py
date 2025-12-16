# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic
# PMPermit for Assistant Accounts


from pyrogram import filters
from pyrogram.types import Message

from anony import config, db, userbot


# Store approved users (owner always approved)
APPROVED_USERS = set()
PM_WARNS = {}

# Custom messages (loaded from database)
CUSTOM_PM_WARN = None
CUSTOM_PM_BLOCK = None
MESSAGES_LOADED = False

# Default messages
DEFAULT_WARN_MSG = (
    "⚠️ **Peringatan {warn}/{total}**\n"
    "⚠️ **Warning {warn}/{total}**\n\n"
    "**🇮🇩 Bahasa Indonesia:**\n"
    "Ini adalah akun assistant bot musik. Mohon jangan kirim pesan ke sini.\n"
    "Gunakan bot utama kami di grup untuk memutar musik.\n\n"
    "**🇬🇧 English:**\n"
    "This is a music bot assistant account. Please do not send messages here.\n"
    "Use our main bot in groups to play music."
)

DEFAULT_BLOCK_MSG = (
    "❌ **Anda telah diblokir!**\n"
    "❌ **You have been blocked!**\n\n"
    "Anda telah melebihi batas peringatan karena spam ke akun assistant ini.\n"
    "You exceeded the warning limit for spamming this assistant account."
)


async def load_custom_messages():
    """Load custom PM messages from database."""
    global CUSTOM_PM_WARN, CUSTOM_PM_BLOCK, MESSAGES_LOADED
    
    if not MESSAGES_LOADED:
        messages = await db.get_pm_messages()
        CUSTOM_PM_WARN = messages.get("warn")
        CUSTOM_PM_BLOCK = messages.get("block")
        MESSAGES_LOADED = True


# PMPermit for Assistant Accounts
@userbot.one.on_message(filters.private & filters.incoming, group=1)
@userbot.two.on_message(filters.private & filters.incoming, group=1)
@userbot.three.on_message(filters.private & filters.incoming, group=1)
async def pmpermit_handler(client, message: Message):
    """PMPermit protection for assistant accounts."""
    
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
    
    # Check if user is already blocked - SILENTLY IGNORE
    if await db.is_pm_blocked(user_id):
        # User already blocked, ensure Telegram block is applied
        try:
            await client.block_user(user_id)
        except Exception as e:
            pass
        return
    
    # Increment warning count
    if user_id not in PM_WARNS:
        PM_WARNS[user_id] = 0
    
    PM_WARNS[user_id] += 1
    warn_count = PM_WARNS[user_id]
    
    # Block if exceeded
    if warn_count > config.PM_WARN_COUNT:
        block_msg = CUSTOM_PM_BLOCK if CUSTOM_PM_BLOCK else DEFAULT_BLOCK_MSG
        try:
            await message.reply_text(block_msg)
        except:
            pass
        
        # Hard block the user via Telegram
        try:
            # Use Pyrogram's block_user method
            await client.block_user(user_id)
        except Exception as e:
            # If block_user doesn't work, try alternative method
            try:
                from pyrogram.raw import functions
                await client.invoke(
                    functions.contacts.Block(
                        id=await client.resolve_peer(user_id)
                    )
                )
            except:
                pass
        return
    
    # Send warning
    warn_msg = CUSTOM_PM_WARN if CUSTOM_PM_WARN else DEFAULT_WARN_MSG
    warn_msg = warn_msg.format(warn=warn_count, total=config.PM_WARN_COUNT)
    await message.reply_text(warn_msg)


# Approve command (for owner only)
@userbot.one.on_message(filters.command("approve", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("approve", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("approve", prefixes=".") & filters.me)
async def approve_pm(client, message: Message):
    """Approve a user to PM."""
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        APPROVED_USERS.add(user_id)
        PM_WARNS.pop(user_id, None)
        await message.reply_text(f"✅ Approved {message.reply_to_message.from_user.mention}")
    else:
        await message.reply_text("Reply to a user's message to approve them.")


# Disapprove command (for owner only)
@userbot.one.on_message(filters.command("disapprove", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("disapprove", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("disapprove", prefixes=".") & filters.me)
async def disapprove_pm(client, message: Message):
    """Disapprove a user from PM."""
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        APPROVED_USERS.discard(user_id)
        PM_WARNS[user_id] = 0
        await message.reply_text(f"❌ Disapproved {message.reply_to_message.from_user.mention}")
    else:
        await message.reply_text("Reply to a user's message to disapprove them.")


# Set custom warning message
@userbot.one.on_message(filters.command("setpmwarn", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("setpmwarn", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("setpmwarn", prefixes=".") & filters.me)
async def set_pm_warn(client, message: Message):
    """Set custom PM warning message. Use {warn} and {total} as placeholders."""
    global CUSTOM_PM_WARN
    
    if len(message.command) < 2:
        await message.reply_text(
            "**Usage:** `.setpmwarn <message>`\n\n"
            "Use `{warn}` for warning count and `{total}` for total warnings.\n\n"
            "**Example:**\n"
            "`.setpmwarn ⚠️ Warning {warn}/{total}\\n\\nDon't spam this account!`"
        )
        return
    
    custom_msg = message.text.split(maxsplit=1)[1]
    CUSTOM_PM_WARN = custom_msg
    await db.set_pm_warn_msg(custom_msg)
    await message.reply_text(f"✅ Custom warning message set and saved!\n\n**Preview:**\n{custom_msg.format(warn=1, total=config.PM_WARN_COUNT)}")


# Set custom block message
@userbot.one.on_message(filters.command("setpmblock", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("setpmblock", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("setpmblock", prefixes=".") & filters.me)
async def set_pm_block(client, message: Message):
    """Set custom PM block message."""
    global CUSTOM_PM_BLOCK
    
    if len(message.command) < 2:
        await message.reply_text(
            "**Usage:** `.setpmblock <message>`\n\n"
            "**Example:**\n"
            "`.setpmblock ❌ You are blocked!\\n\\nStop spamming.`"
        )
        return
    
    custom_msg = message.text.split(maxsplit=1)[1]
    CUSTOM_PM_BLOCK = custom_msg
    await db.set_pm_block_msg(custom_msg)
    await message.reply_text(f"✅ Custom block message set and saved!\n\n**Preview:**\n{custom_msg}")


# Reset to default messages
@userbot.one.on_message(filters.command("resetpm", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("resetpm", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("resetpm", prefixes=".") & filters.me)
async def reset_pm_messages(client, message: Message):
    """Reset PM messages to default."""
    global CUSTOM_PM_WARN, CUSTOM_PM_BLOCK
    
    CUSTOM_PM_WARN = None
    CUSTOM_PM_BLOCK = None
    await db.clear_pm_messages()
    await message.reply_text("✅ PM messages reset to default and cleared from database!")


# Show current PM messages
@userbot.one.on_message(filters.command("showpm", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("showpm", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("showpm", prefixes=".") & filters.me)
async def show_pm_messages(client, message: Message):
    """Show current PM messages."""
    warn_msg = CUSTOM_PM_WARN if CUSTOM_PM_WARN else DEFAULT_WARN_MSG
    block_msg = CUSTOM_PM_BLOCK if CUSTOM_PM_BLOCK else DEFAULT_BLOCK_MSG
    
    status = "Custom" if CUSTOM_PM_WARN else "Default"
    
    await message.reply_text(
        f"**Current PM Messages ({status}):**\n\n"
        f"**Warning Message:**\n{warn_msg.format(warn=1, total=config.PM_WARN_COUNT)}\n\n"
        f"**Block Message:**\n{block_msg}"
    )


# PMPermit help command
@userbot.one.on_message(filters.command("pmhelp", prefixes=".") & filters.me)
@userbot.two.on_message(filters.command("pmhelp", prefixes=".") & filters.me)
@userbot.three.on_message(filters.command("pmhelp", prefixes=".") & filters.me)
async def pm_help(client, message: Message):
    """Show PMPermit help and available commands."""
    help_text = (
        "**🛡️ PMPermit - Help & Commands**\n\n"
        
        "**📋 User Management:**\n"
        "• `.approve` - Approve user (reply to their message)\n"
        "• `.disapprove` - Remove approval (reply to their message)\n\n"
        
        "**✏️ Custom Messages:**\n"
        "• `.setpmwarn <message>` - Set custom warning message\n"
        "  → Use `{warn}` and `{total}` as placeholders\n"
        "  → Example: `.setpmwarn 🚫 Warning {warn}/{total}\\n\\nDon't spam!`\n\n"
        
        "• `.setpmblock <message>` - Set custom block message\n"
        "  → Example: `.setpmblock ❌ Blocked!\\n\\nSpam detected.`\n\n"
        
        "**📊 View & Reset:**\n"
        "• `.showpm` - Show current messages (custom or default)\n"
        "• `.resetpm` - Reset to default messages\n\n"
        
        "**ℹ️ Info:**\n"
        "• Default warnings: 3 (configurable in .env)\n"
        "• Auto-block after limit exceeded\n"
        "• Owner always bypassed\n"
        "• Messages support Markdown: **bold**, *italic*, emoji\n\n"
        
        "**💡 Tips:**\n"
        "• All commands use `.` prefix and work in PM only\n"
        "• Use `\\n` for new line in custom messages\n"
        "• Custom messages saved until bot restart\n"
        "• `.pmhelp` - Show this help anytime"
    )
    
    await message.reply_text(help_text)
