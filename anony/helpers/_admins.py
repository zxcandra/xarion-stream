# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from functools import wraps

from pyrogram import StopPropagation, enums, types

# Note: 'app' and 'db' are imported lazily in functions to avoid circular imports


def admin_check(func):
    @wraps(func)
    async def wrapper(_, update: types.Message | types.CallbackQuery, *args, **kwargs):
        from anony import app, db
        
        async def reply(text):
            if isinstance(update, types.Message):
                return await update.reply_text(text)
            else:
                return await update.answer(text, show_alert=True)

        chat_id = (
            update.chat.id
            if isinstance(update, types.Message)
            else update.message.chat.id
        )
        user_id = update.from_user.id
        admins = await db.get_admins(chat_id)

        if user_id in app.sudoers:
            return await func(_, update, *args, **kwargs)

        if user_id not in admins:
            return await reply("Anda? Kelola obrolan video? Tidak dengan izin seperti itu.")

        return await func(_, update, *args, **kwargs)

    return wrapper


def can_manage_vc(func):
    @wraps(func)
    async def wrapper(_, update: types.Message | types.CallbackQuery, *args, **kwargs):
        from anony import app, db
        
        chat_id = (
            update.chat.id
            if isinstance(update, types.Message)
            else update.message.chat.id
        )
        user_id = update.from_user.id

        if user_id in app.sudoers:
            return await func(_, update, *args, **kwargs)

        if await db.is_auth(chat_id, user_id):
            return await func(_, update, *args, **kwargs)

        admins = await db.get_admins(chat_id)
        if user_id in admins:
            return await func(_, update, *args, **kwargs)

        if isinstance(update, types.Message):
            return await update.reply_text("Anda? Kelola obrolan video? Tidak dengan izin seperti itu.")
        else:
            return await update.answer("Anda? Kelola obrolan video? Tidak dengan izin seperti itu.", show_alert=True)

    return wrapper


async def is_admin(chat_id: int, user_id: int) -> bool:
    from anony import app, db
    
    if user_id in await db.get_admins(chat_id):
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]
    except:
        raise StopPropagation


async def reload_admins(chat_id: int) -> list[int]:
    from anony import app
    
    try:
        admins = [
            admin
            async for admin in app.get_chat_members(
                chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            )
            if not admin.user.is_bot
        ]
        return [admin.user.id for admin in admins]
    except:
        return []
