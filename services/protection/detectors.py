services/protection/detectors.py
═══════════════════════════════════════════════════════════════
كاشفات المحتوى المخالف.
كل دالة تفحص رسالة وتُرجع True إن كانت تطابق نوع حماية معين.
دوال نقية (Pure) قابلة للاختبار بسهولة.
═══════════════════════════════════════════════════════════════
"""

import re
from datetime import datetime, timezone

from pyrogram.types import Message


# نمط الروابط (http/https/www/t.me/تيليجرام)
_LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|[a-zA-Z0-9-]+\.(com|net|org|io|me|co|info|xyz))",
    re.IGNORECASE,
)
# نمط روابط الدعوة
_INVITE_PATTERN = re.compile(
    r"(t\.me/joinchat/|t\.me/\+|telegram\.me/joinchat/)",
    re.IGNORECASE,
)
# نمط اليوزرات
_USERNAME_PATTERN = re.compile(r"@[a-zA-Z][a-zA-Z0-9_]{4,31}")


class ContentDetectors:
    """كاشفات المحتوى."""

    @staticmethod
    def has_links(message: Message) -> bool:
        """فحص وجود روابط."""
        text = message.text or message.caption or ""
        if _LINK_PATTERN.search(text):
            return True
        # فحص الروابط في الـ entities
        entities = message.entities or message.caption_entities or []
        for entity in entities:
            if entity.type.value in ("url", "text_link"):
                return True
        return False

    @staticmethod
    def has_invite_links(message: Message) -> bool:
        """فحص روابط الدعوة لمجموعات/قنوات."""
        text = message.text or message.caption or ""
        return bool(_INVITE_PATTERN.search(text))

    @staticmethod
    def has_username(message: Message) -> bool:
        """فحص وجود منشن يوزر."""
        text = message.text or message.caption or ""
        return bool(_USERNAME_PATTERN.search(text))

    @staticmethod
    def is_forwarded(message: Message) -> bool:
        """فحص ما إذا كانت الرسالة موجّهة (forward)."""
        return bool(message.forward_date or message.forward_from or message.forward_from_chat)

    @staticmethod
    def is_photo(message: Message) -> bool:
        return bool(message.photo)

    @staticmethod
    def is_video(message: Message) -> bool:
        return bool(message.video or message.video_note)

    @staticmethod
    def is_file(message: Message) -> bool:
        return bool(message.document)

    @staticmethod
    def is_audio(message: Message) -> bool:
        return bool(message.audio or message.voice)

    @staticmethod
    def is_sticker(message: Message) -> bool:
        return bool(message.sticker)

    @staticmethod
    def is_gif(message: Message) -> bool:
        return bool(message.animation)

    @staticmethod
    def is_new_account(message: Message, days_threshold: int) -> bool:
        """
        فحص ما إذا كان الحساب جديداً.
        تقدير عمر الحساب من معرّف المستخدم (طريقة تقريبية شائعة):
        المعرّفات الأكبر = حسابات أحدث.
        """
        if not message.from_user:
            return False
        # عتبة معرّف تقريبية للحسابات الجديدة جداً
        # (هذه طريقة تقديرية، تيليجرام لا يوفّر تاريخ الإنشاء مباشرة)
        user_id = message.from_user.id
        # معرّفات فوق ~6 مليار غالباً حسابات حديثة جداً (2023+)
        # نستخدم منطقاً محافظاً
        return user_id > 6_000_000_000

    @staticmethod
    def is_bot_added(message: Message) -> list:
        """
        فحص ما إذا كانت رسالة انضمام تحتوي بوتات.
        Returns: قائمة معرّفات البوتات المنضمة.
        """
        bots = []
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.is_bot:
                    bots.append(member.id)
        return bots


detectors = ContentDetectors()
