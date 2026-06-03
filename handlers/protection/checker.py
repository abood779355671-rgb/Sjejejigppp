handlers/protection/checker.py
═══════════════════════════════════════════════════════════════
معالج فحص الحماية. يُسجَّل في group منخفض ليعمل مبكراً على
رسائل المجموعات (بعد خط الأنابيب).
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.protection.engine import protection_engine
from core.logger import setup_logger

logger = setup_logger("protection_checker")


async def protection_handler(client: Client, message: Message):
    """
    فحص الحماية على رسائل المجموعات.
    إن كانت مخالفة، توقف الانتشار (لا تصل لمعالجات الردود مثلاً).
    """
    from pyrogram import StopPropagation

    bot_id = client.bot_info.id if client.bot_info else 0

    # فحص انضمام البوتات
    if message.new_chat_members:
        await protection_engine.check_bot_join(client, message, bot_id)
        return

    # فحص المحتوى المخالف
    is_violation = await protection_engine.check_message(client, message, bot_id)
    if is_violation:
        raise StopPropagation
