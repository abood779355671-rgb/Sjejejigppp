services/protection/engine.py
═══════════════════════════════════════════════════════════════
محرك الحماية الرئيسي.
يفحص كل رسالة مقابل إعدادات الحماية المفعّلة،
ويطبّق العقوبة عند المخالفة، ويحذف الرسالة المخالفة.

المتميز فأعلى (bypass_protection) معفى من الحماية.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.protection.detectors import detectors
from services.protection.warn_engine import warn_engine
from services.permission_service import permission_service
from database.repositories.protection_repo import protection_repo
from database.repositories.log_repo import log_repo
from middlewares.rate_limit import rate_limit_middleware
from config.constants import (
    ProtectionType, PROTECTION_NAMES_AR, EventType,
)
from core.logger import setup_logger

logger = setup_logger("protection_engine")


class ProtectionEngine:
    """محرك الحماية."""

    # خريطة: نوع الحماية → دالة الكاشف
    _CHECKS = [
        (ProtectionType.INVITE_LINKS, "anti_invite_links", lambda m: detectors.has_invite_links(m)),
        (ProtectionType.LINKS, "anti_links", lambda m: detectors.has_links(m)),
        (ProtectionType.USERNAME, "anti_username", lambda m: detectors.has_username(m)),
        (ProtectionType.FORWARD, "anti_forward", lambda m: detectors.is_forwarded(m)),
        (ProtectionType.PHOTO, "anti_photo", lambda m: detectors.is_photo(m)),
        (ProtectionType.VIDEO, "anti_video", lambda m: detectors.is_video(m)),
        (ProtectionType.FILES, "anti_files", lambda m: detectors.is_file(m)),
        (ProtectionType.AUDIO, "anti_audio", lambda m: detectors.is_audio(m)),
        (ProtectionType.STICKERS, "anti_stickers", lambda m: detectors.is_sticker(m)),
        (ProtectionType.GIF, "anti_gif", lambda m: detectors.is_gif(m)),
    ]

    async def check_message(
        self,
        client: Client,
        message: Message,
        bot_id: int,
    ) -> bool:
        """
        فحص رسالة مقابل كل أنواع الحماية المفعّلة.

        Returns:
            True إن كانت مخالفة (وعُولجت)، False إن كانت سليمة.
        """
        if not message.from_user:
            return False

        chat_id = message.chat.id
        user_id = message.from_user.id

        # جلب الإعدادات (من Cache)
        settings_data = await protection_repo.get_settings(chat_id)
        if not settings_data:
            return False

        # إن لم تكن أي حماية مفعّلة، توقف سريعاً
        if not self._any_protection_enabled(settings_data):
            return False

        # المتميز فأعلى معفى من الحماية
        if await permission_service.has_permission(chat_id, user_id, "bypass_protection"):
            return False

        punishment = settings_data.get("punishment", "warn")
        max_warns = settings_data.get("max_warns", 3)

        # ─── 1. فحص الفلود (منفصل لأنه يعتمد على Redis) ───
        if settings_data.get("anti_flood"):
            limit = settings_data.get("flood_limit", 5)
            seconds = settings_data.get("flood_seconds", 5)
            if await rate_limit_middleware.check_group_flood(chat_id, user_id, limit, seconds):
                await rate_limit_middleware.reset_flood(chat_id, user_id)
                return await self._handle_violation(
                    client, message, chat_id, user_id, punishment,
                    max_warns, bot_id, ProtectionType.FLOOD,
                )

        # ─── 2. فحص الحسابات الجديدة ───
        if settings_data.get("anti_new_accounts"):
            days = settings_data.get("new_account_days", 7)
            if detectors.is_new_account(message, days):
                return await self._handle_violation(
                    client, message, chat_id, user_id, punishment,
                    max_warns, bot_id, ProtectionType.NEW_ACCOUNTS,
                )

        # ─── 3. فحص أنواع المحتوى ───
        for prot_type, field, check_func in self._CHECKS:
            if settings_data.get(field) and check_func(message):
                return await self._handle_violation(
                    client, message, chat_id, user_id, punishment,
                    max_warns, bot_id, prot_type,
                )

        return False

    async def _handle_violation(
        self,
        client: Client,
        message: Message,
        chat_id: int,
        user_id: int,
        punishment: str,
        max_warns: int,
        bot_id: int,
        violation_type: ProtectionType,
    ) -> bool:
        """معالجة مخالفة: حذف الرسالة + تطبيق العقوبة + تسجيل."""
        violation_name = PROTECTION_NAMES_AR.get(violation_type, "مخالفة")

        # حذف الرسالة المخالفة
        try:
            await message.delete()
        except Exception as e:
            logger.debug(f"فشل حذف الرسالة المخالفة: {e}")

        # تطبيق العقوبة
        action_result = await warn_engine.apply_punishment(
            client, chat_id, user_id, punishment, max_warns, bot_id,
            reason=violation_name,
        )

        # إرسال تنبيه (يُحذف تلقائياً بعد فترة)
        try:
            mention = f'<a href="tg://user?id={user_id}">المخالف</a>'
            notice = await client.send_message(
                chat_id,
                f"🛡 <b>{violation_name}</b>\n👤 {mention}\n{action_result}",
            )
            # حذف التنبيه بعد 10 ثوانٍ
            import asyncio
            asyncio.create_task(self._delete_after(notice, 10))
        except Exception as e:
            logger.debug(f"فشل إرسال تنبيه الحماية: {e}")

        # تسجيل المخالفة
        await log_repo.log_event(
            EventType.PROTECTION_TRIGGERED.value,
            chat_id=chat_id, target_id=user_id,
            details={"type": violation_type.value, "punishment": punishment},
        )

        return True

    @staticmethod
    async def _delete_after(message: Message, seconds: int) -> None:
        """حذف رسالة بعد عدد ثوانٍ."""
        import asyncio
        await asyncio.sleep(seconds)
        try:
            await message.delete()
        except Exception:
            pass

    @staticmethod
    def _any_protection_enabled(settings_data: dict) -> bool:
        """فحص سريع: هل أي حماية مفعّلة؟"""
        protection_keys = [
            "anti_links", "anti_username", "anti_forward", "anti_photo",
            "anti_video", "anti_files", "anti_audio", "anti_stickers",
            "anti_gif", "anti_bots", "anti_spam", "anti_flood",
            "anti_new_accounts", "anti_invite_links",
        ]
        return any(settings_data.get(k) for k in protection_keys)

    async def check_bot_join(
        self,
        client: Client,
        message: Message,
        bot_id: int,
    ) -> None:
        """
        فحص حماية البوتات عند انضمام أعضاء.
        إن كانت مفعّلة، يُطرد أي بوت ينضم.
        """
        chat_id = message.chat.id
        settings_data = await protection_repo.get_settings(chat_id)
        if not settings_data.get("anti_bots"):
            return

        joined_bots = detectors.is_bot_added(message)
        for bot_user_id in joined_bots:
            try:
                await client.ban_chat_member(chat_id, bot_user_id)
                await client.send_message(
                    chat_id, "🤖 تم حظر بوت تلقائياً (حماية البوتات مفعّلة)"
                )
            except Exception as e:
                logger.debug(f"فشل حظر بوت: {e}")


protection_engine = ProtectionEngine()
