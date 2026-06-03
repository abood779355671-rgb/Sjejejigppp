services/filter_service.py
═══════════════════════════════════════════════════════════════
خدمة الفلاتر: فحص الرسائل ضد الكلمات/الروابط الممنوعة.
═══════════════════════════════════════════════════════════════
"""

import re

from pyrogram import Client
from pyrogram.types import Message

from database.repositories.filter_command_repo import filter_repo
from services.permission_service import permission_service
from core.logger import setup_logger

logger = setup_logger("filter_service")


class FilterService:
    """خدمة الفلاتر."""

    async def check_message(
        self,
        client: Client,
        message: Message,
    ) -> bool:
        """
        فحص رسالة ضد الفلاتر.

        Returns:
            True إن طابقت فلتراً (وحُذفت).
        """
        text = message.text or message.caption
        if not text or not message.from_user:
            return False

        chat_id = message.chat.id
        user_id = message.from_user.id

        # الإداريون (أدمن فأعلى) معفون من الفلاتر
        if await permission_service.has_permission(chat_id, user_id, "delete_messages"):
            return False

        filters_list = await filter_repo.get_filters_for_chat(chat_id)
        if not filters_list:
            return False

        text_lower = text.lower()
        for flt in filters_list:
            word = flt["filter_word"]
            ftype = flt["filter_type"]

            matched = False
            if ftype == "regex":
                try:
                    matched = bool(re.search(word, text, re.IGNORECASE))
                except re.error:
                    matched = False
            elif ftype == "link":
                # فلتر يطابق أي رابط يحتوي الكلمة
                matched = word in text_lower
            else:  # word
                matched = word in text_lower

            if matched:
                try:
                    await message.delete()
                except Exception as e:
                    logger.debug(f"فشل حذف رسالة الفلتر: {e}")
                return True

        return False


filter_service = FilterService()
