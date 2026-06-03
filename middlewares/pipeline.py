middlewares/pipeline.py
═══════════════════════════════════════════════════════════════
خط أنابيب الطبقات الوسيطة (Middleware Pipeline).

يُنفَّذ في بداية معالجة كل رسالة بالترتيب:
1. تسجيل المستخدم والمجموعة.
2. فحص الحظر العام.
3. فحص وضع الصيانة.
4. فحص الفلود العام.

يُرجع True إذا كان يجب متابعة المعالجة، False إذا يجب التوقف.

هذا يجمع كل الفحوصات في مكان واحد بدلاً من تكرارها في كل معالج.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional

from pyrogram.types import Message

from middlewares.ban_check import ban_check_middleware
from middlewares.maintenance import maintenance_middleware
from middlewares.rate_limit import rate_limit_middleware
from database.repositories.user_repo import user_repo
from database.repositories.group_repo import group_repo
from core.logger import setup_logger

logger = setup_logger("pipeline")


class MiddlewarePipeline:
    """خط أنابيب المعالجة المسبقة."""

    @staticmethod
    async def process(message: Message) -> bool:
        """
        تشغيل خط الأنابيب على رسالة.

        Returns:
            True: تابع المعالجة.
            False: توقّف (محظور/صيانة/فلود).
        """
        user = message.from_user
        chat = message.chat

        # تجاهل الرسائل بلا مستخدم (رسائل القناة، الخدمة)
        if user is None:
            return True

        # ───────────────────────────────────────
        # 1. فحص الحظر العام (الأسرع أولاً)
        # ───────────────────────────────────────
        if await ban_check_middleware.is_blocked(user.id):
            logger.debug(f"تجاهل رسالة من محظور عام: {user.id}")
            return False

        # ───────────────────────────────────────
        # 2. فحص وضع الصيانة
        # ───────────────────────────────────────
        if await maintenance_middleware.should_block(user.id):
            try:
                await message.reply_text(
                    "🛠 البوت في وضع الصيانة حالياً، يرجى المحاولة لاحقاً"
                )
            except Exception:
                pass
            return False

        # ───────────────────────────────────────
        # 3. فحص الفلود العام
        # ───────────────────────────────────────
        if await rate_limit_middleware.check_global_flood(user.id):
            logger.debug(f"فلود عام من المستخدم: {user.id}")
            return False  # تجاهل صامت لمنع الإغراق

        # ───────────────────────────────────────
        # 4. تسجيل/تحديث المستخدم والمجموعة
        # ───────────────────────────────────────
        await MiddlewarePipeline._register_entities(message)

        return True

    @staticmethod
    async def _register_entities(message: Message) -> None:
        """تسجيل/تحديث بيانات المستخدم والمجموعة في قاعدة البيانات."""
        user = message.from_user
        chat = message.chat

        try:
            # تسجيل المستخدم
            await user_repo.upsert_user(
                user_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                language_code=user.language_code or "ar",
                is_bot=user.is_bot,
            )

            # تسجيل المجموعة (إن كانت رسالة في مجموعة)
            chat_type_str = str(chat.type.value) if hasattr(chat.type, "value") else str(chat.type)
            if chat_type_str in ("group", "supergroup"):
                await group_repo.upsert_group(
                    chat_id=chat.id,
                    title=chat.title,
                    username=chat.username,
                    chat_type=chat_type_str,
                )
        except Exception as e:
            # لا نوقف المعالجة بسبب فشل التسجيل
            logger.error(f"خطأ في تسجيل الكيانات: {e}")


middleware_pipeline = MiddlewarePipeline()
