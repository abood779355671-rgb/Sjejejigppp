utils/context.py
═══════════════════════════════════════════════════════════════
استخراج معلومات السياق من تحديثات Pyrogram بشكل موحّد.
يبسّط الوصول إلى (المستخدم، المجموعة، النص) من Message أو CallbackQuery.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional, Union

from pyrogram.types import Message, CallbackQuery


class RequestContext:
    """
    حاوية موحّدة لمعلومات الطلب.
    تعمل مع كل من Message و CallbackQuery.
    """

    def __init__(
        self,
        user_id: int,
        chat_id: int,
        chat_type: str,
        is_private: bool,
        is_group: bool,
    ):
        self.user_id = user_id
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.is_private = is_private
        self.is_group = is_group

    @classmethod
    def from_update(
        cls,
        update: Union[Message, CallbackQuery],
    ) -> Optional["RequestContext"]:
        """
        بناء السياق من تحديث Pyrogram.

        Returns:
            RequestContext أو None إن تعذّر الاستخراج.
        """
        # تحديد كائن الرسالة والمستخدم
        if isinstance(update, CallbackQuery):
            user = update.from_user
            message = update.message
            chat = message.chat if message else None
        else:  # Message
            user = update.from_user
            chat = update.chat

        if user is None or chat is None:
            return None

        chat_type_str = str(chat.type.value) if hasattr(chat.type, "value") else str(chat.type)
        is_private = chat_type_str == "private"
        is_group = chat_type_str in ("group", "supergroup")

        return cls(
            user_id=user.id,
            chat_id=chat.id,
            chat_type=chat_type_str,
            is_private=is_private,
            is_group=is_group,
        )
