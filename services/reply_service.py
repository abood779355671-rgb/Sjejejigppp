services/reply_service.py
═══════════════════════════════════════════════════════════════
خدمة مطابقة وإرسال الردود التلقائية.
تدعم 4 أنواع مطابقة وردوداً عشوائية ووسائط.
الأداء: تُحمّل ردود المجموعة وتُطابق محلياً.
═══════════════════════════════════════════════════════════════
"""

import re
import random
from typing import Optional

from pyrogram import Client
from pyrogram.types import Message

from database.repositories.reply_repo import reply_repo
from config.constants import MatchType, ReplyType
from core.logger import setup_logger

logger = setup_logger("reply_service")


class ReplyService:
    """خدمة الردود."""

    @staticmethod
    def _matches(text: str, reply: dict) -> bool:
        """فحص ما إذا كان النص يطابق محفّز الرد."""
        trigger = reply["trigger_text"]
        match_type = reply["match_type"]
        text_lower = text.lower().strip()
        trigger_lower = trigger.lower().strip()

        if match_type == MatchType.EXACT.value:
            return text_lower == trigger_lower
        elif match_type == MatchType.CONTAINS.value:
            return trigger_lower in text_lower
        elif match_type == MatchType.KEYWORD.value:
            # كلمة كاملة (محاطة بحدود)
            return bool(re.search(rf"\b{re.escape(trigger_lower)}\b", text_lower))
        elif match_type == MatchType.REGEX.value:
            try:
                return bool(re.search(trigger, text, re.IGNORECASE))
            except re.error:
                return False
        return False

    async def find_and_send(
        self,
        client: Client,
        message: Message,
    ) -> bool:
        """
        البحث عن رد مطابق وإرساله.

        Returns:
            True إن وُجد رد وأُرسل.
        """
        text = message.text or message.caption
        if not text:
            return False

        chat_id = message.chat.id
        replies = await reply_repo.get_replies_for_chat(chat_id)
        if not replies:
            return False

        # جمع كل الردود المطابقة
        matched = [r for r in replies if self._matches(text, r)]
        if not matched:
            return False

        # إن كان هناك ردود عشوائية، نختار واحداً عشوائياً من المطابق
        chosen = random.choice(matched)

        await self._send_reply(client, message, chosen)
        return True

    @staticmethod
    async def _send_reply(client: Client, message: Message, reply: dict) -> None:
        """إرسال الرد حسب نوعه."""
        reply_type = reply["reply_type"]
        content = reply.get("reply_content")
        media_file_id = reply.get("media_file_id")
        chat_id = message.chat.id

        try:
            if reply_type == ReplyType.TEXT.value:
                await message.reply_text(content or "")
            elif reply_type == ReplyType.PHOTO.value and media_file_id:
                await message.reply_photo(media_file_id, caption=content or "")
            elif reply_type == ReplyType.VIDEO.value and media_file_id:
                await message.reply_video(media_file_id, caption=content or "")
            elif reply_type == ReplyType.AUDIO.value and media_file_id:
                await message.reply_audio(media_file_id, caption=content or "")
            elif reply_type == ReplyType.GIF.value and media_file_id:
                await message.reply_animation(media_file_id, caption=content or "")
            else:
                if content:
                    await message.reply_text(content)
        except Exception as e:
            logger.debug(f"فشل إرسال الرد: {e}")


reply_service = ReplyService()
