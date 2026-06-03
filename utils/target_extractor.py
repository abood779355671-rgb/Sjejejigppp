utils/target_extractor.py
═══════════════════════════════════════════════════════════════
استخراج المستخدم المستهدف من رسالة بأي طريقة:
1. الرد على رسالته.
2. ذكر يوزره (@username).
3. كتابة معرّفه الرقمي (ID).
4. منشن نصي (text_mention).

يُرجع كائناً موحّداً يحوي معلومات الهدف.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional
from dataclasses import dataclass

from pyrogram import Client
from pyrogram.types import Message

from database.repositories.user_repo import user_repo
from utils.validators import validators
from core.exceptions import ValidationError
from core.logger import setup_logger

logger = setup_logger("target_extractor")


@dataclass
class Target:
    """معلومات المستخدم المستهدف."""
    user_id: int
    first_name: Optional[str] = None
    username: Optional[str] = None

    @property
    def mention(self) -> str:
        """منشن HTML للهدف."""
        name = self.first_name or "المستخدم"
        return f'<a href="tg://user?id={self.user_id}">{name}</a>'


class TargetExtractor:
    """مستخرج المستهدف."""

    @staticmethod
    async def extract(
        client: Client,
        message: Message,
    ) -> Optional[Target]:
        """
        استخراج المستهدف من الرسالة بكل الطرق الممكنة.

        ترتيب الأولوية:
        1. الرد على رسالة.
        2. منشن نصي (text_mention) في الأرجومنتس.
        3. يوزر مكتوب.
        4. معرّف رقمي مكتوب.

        Returns:
            Target أو None إن تعذّر.
        """
        # ─── 1. الرد على رسالة ───
        if message.reply_to_message and message.reply_to_message.from_user:
            u = message.reply_to_message.from_user
            return Target(user_id=u.id, first_name=u.first_name, username=u.username)

        # ─── 2. فحص الـ entities للمنشن النصي ───
        if message.entities:
            for entity in message.entities:
                if entity.type.value == "text_mention" and entity.user:
                    u = entity.user
                    return Target(user_id=u.id, first_name=u.first_name, username=u.username)

        # ─── استخراج الأرجومنت (الكلمة بعد الأمر) ───
        if not message.text and not message.caption:
            return None

        text = message.text or message.caption
        parts = text.split()
        if len(parts) < 2:
            return None

        arg = parts[1].strip()

        # ─── 3. يوزر ───
        if arg.startswith("@"):
            try:
                username = validators.validate_username(arg)
            except ValidationError:
                return None
            # البحث في قاعدة البيانات أولاً
            user = await user_repo.get_user_by_username(username)
            if user:
                return Target(
                    user_id=user["user_id"],
                    first_name=user.get("first_name"),
                    username=user.get("username"),
                )
            # محاولة جلبه من تيليجرام
            try:
                u = await client.get_users(arg)
                return Target(user_id=u.id, first_name=u.first_name, username=u.username)
            except Exception:
                return None

        # ─── 4. معرّف رقمي ───
        try:
            target_id = validators.validate_user_id(arg)
        except ValidationError:
            return None

        # محاولة جلب الاسم من القاعدة أو تيليجرام
        user = await user_repo.get_user(target_id)
        if user:
            return Target(
                user_id=target_id,
                first_name=user.get("first_name"),
                username=user.get("username"),
            )
        try:
            u = await client.get_users(target_id)
            return Target(user_id=u.id, first_name=u.first_name, username=u.username)
        except Exception:
            return Target(user_id=target_id)  # نعيده ولو بلا اسم


target_extractor = TargetExtractor()
