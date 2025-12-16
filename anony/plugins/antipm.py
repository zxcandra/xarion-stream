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


# PMPermit for Assistant Accounts
@userbot.one.on_message(filters.private & filters.incoming, group=1)
@userbot.two.on_message(filters.private & filters.incoming, group=1)
@userbot.three.on_message(filters.private & filters.incoming, group=1)
async def pmpermit_handler(client, message: Message):
    """PMPermit protection for assistant accounts."""
    
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
    
    # Increment warning count
    if user_id not in PM_WARNS:
        PM_WARNS[user_id] = 0
    
    PM_WARNS[user_id] += 1
    warn_count = PM_WARNS[user_id]
    
    # Block if exceeded
    if warn_count > config.PM_WARN_COUNT:
        await message.reply_text(
            "❌ **You have been blocked!**\n\n"
            "You exceeded the warning limit for spamming this assistant account."
        )
        # Block user
        try:
            await client.block_user(user_id)
        except:
            pass
        return
    
    # Send warning
    await message.reply_text(
        f"⚠️ **Warning {warn_count}/{config.PM_WARN_COUNT}**\n\n"
        f"This is an assistant account. Please do not send messages here.\n\n"
        f"**Ini adalah akun assistant. Jangan kirim pesan ke sini.**\n\n"
        f"Use our bot in groups instead / Gunakan bot kami di grup saja."
    )


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
