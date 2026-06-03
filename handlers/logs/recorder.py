handlers/logs/recorder.py
═══════════════════════════════════════════════════════════════
مسجّل الأحداث التلقائي: يسجّل حذف/تعديل الرسائل ودخول/خروج الأعضاء.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from database.repositories.log_repo import log_repo
from config.constants import EventType
from core.logger import setup_logger

logger = setup_logger("logs_recorder")


async def record_edited_message(client: Client, message: Message):
    """تسجيل تعديل رسالة."""
    if not message.from_user:
        return
    await log_repo.log_event(
        EventType.MESSAGE_EDITED.value,
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        details={"text": (message.text or message.caption or "")[:200]},
    )


async def record_member_join(client: Client, message: Message):
    """تسجيل دخول أعضاء."""
    if not message.new_chat_members:
        return
    for member in message.new_chat_members:
        await log_repo.log_event(
            EventType.MEMBER_JOINED.value,
            chat_id=message.chat.id,
            target_id=member.id,
            details={"name": member.first_name},
        )


async def record_member_left(client: Client, message: Message):
    """تسجيل خروج عضو."""
    if not message.left_chat_member:
        return
    await log_repo.log_event(
        EventType.MEMBER_LEFT.value,
        chat_id=message.chat.id,
        target_id=message.left_chat_member.id,
        details={"name": message.left_chat_member.first_name},
    )
