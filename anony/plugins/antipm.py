# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters
from pyrogram.types import Message

from anony import config, db, userbot
from anony.core.lang import Language

lang_helper = Language()


# Anti-PM for Assistant Accounts (Userbot)
@userbot.one.on_message(filters.private & filters.incoming, group=-1)
@userbot.two.on_message(filters.private & filters.incoming, group=-1)
@userbot.three.on_message(filters.private & filters.incoming, group=-1)
async def anti_pm_assistant(client, message: Message):
    """Handle anti-PM protection for assistant accounts."""
    
    # Skip if anti-PM is disabled
    if not config.ANTI_PM_ENABLED:
        return
    
    # Allow owner to PM
    if message.from_user.id == config.OWNER_ID:
        return
    
    user_id = message.from_user.id
    
    # Check if user is already blocked
    if await db.is_pm_blocked(user_id):
        await message.reply_text("❌ You have been blocked for spamming this assistant account.")
        return
    
    # Add warning
    warn_count = await db.add_pm_warn(user_id)
    
    # Get user's language preference (default to English)
    try:
        _lang = await lang_helper.get_lang(user_id)
    except:
        _lang = "en"
    
    lang_dict = lang_helper.languages.get(_lang, lang_helper.languages["en"])
    
    # Send warning message
    if warn_count <= config.PM_WARN_COUNT:
        await message.reply_text(
            lang_dict["pm_warn"].format(warn_count, config.PM_WARN_COUNT)
        )
    else:
        # Final warning / block message
        await message.reply_text(lang_dict["pm_blocked"])
