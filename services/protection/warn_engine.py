services/protection/warn_engine.py
═══════════════════════════════════════════════════════════════
محرك الإنذار التصاعدي.
عند مخالفة، يزيد الإنذار. عند بلوغ الحد الأقصى، تُطبَّق العقوبة
المحدّدة (كتم/تقييد/طرد/حظر) ويُعاد تعيين العداد.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client

from database.repositories.moderation_repo import moderation_repo
from services.moderation_service import moderation_service
from config.constants import PunishmentType, PUNISHMENT_NAMES_AR
from core.logger import setup_logger

logger = setup_logger("warn_engine")


class WarnEngine:
    """محرك الإنذار والعقوبات."""

    async def apply_punishment(
        self,
        client: Client,
        chat_id: int,
        user_id: int,
        punishment: str,
        max_warns: int,
        bot_id: int,
        reason: str = "مخالفة الحماية",
    ) -> str:
        """
        تطبيق العقوبة المناسبة على مخالف.

        منطق:
        - إن كانت العقوبة "إنذار": زِد العداد، وعند الحد طبّق الطرد.
        - غير ذلك (كتم/تقييد/طرد/حظر): طبّقها مباشرة.

        Args:
            bot_id: معرّف البوت (كمنفّذ للإجراء، يتجاوز فحص الرتبة).

        Returns:
            رسالة عربية تصف الإجراء المتخذ.
        """
        # العقوبات المباشرة (بدون نظام إنذار)
        if punishment == PunishmentType.MUTE.value:
            await self._direct_mute(client, chat_id, user_id, bot_id, reason)
            return "🔇 تم كتم المخالف"

        if punishment == PunishmentType.RESTRICT.value:
            await self._direct_restrict(client, chat_id, user_id, bot_id)
            return "🚫 تم تقييد المخالف"

        if punishment == PunishmentType.KICK.value:
            await self._direct_kick(client, chat_id, user_id, bot_id)
            return "👢 تم طرد المخالف"

        if punishment == PunishmentType.BAN.value:
            await self._direct_ban(client, chat_id, user_id, bot_id, reason)
            return "🔨 تم حظر المخالف"

        # العقوبة الافتراضية: نظام الإنذار التصاعدي
        return await self._warn_flow(client, chat_id, user_id, max_warns, bot_id, reason)

    async def _warn_flow(
        self,
        client: Client,
        chat_id: int,
        user_id: int,
        max_warns: int,
        bot_id: int,
        reason: str,
    ) -> str:
        """تدفق الإنذار التصاعدي."""
        count = await moderation_repo.add_warn(chat_id, user_id, warned_by=bot_id, reason=reason)

        if count >= max_warns:
            # بلوغ الحد → طرد + إعادة تعيين
            await self._direct_kick(client, chat_id, user_id, bot_id)
            await moderation_repo.reset_warns(chat_id, user_id)
            return f"👢 تم طرد المخالف بعد بلوغ {max_warns} إنذارات"

        return f"⚠️ إنذار ({count}/{max_warns}) - {reason}"

    # ─── دوال التطبيق المباشر (البوت كمنفّذ) ───

    async def _direct_mute(self, client, chat_id, user_id, bot_id, reason):
        from pyrogram.types import ChatPermissions
        try:
            await client.restrict_chat_member(
                chat_id, user_id,
                ChatPermissions(can_send_messages=False),
            )
            await moderation_repo.add_action(
                chat_id, user_id, "mute", issued_by=bot_id, reason=reason,
            )
        except Exception as e:
            logger.debug(f"فشل الكتم التلقائي: {e}")

    async def _direct_restrict(self, client, chat_id, user_id, bot_id):
        from pyrogram.types import ChatPermissions
        try:
            await client.restrict_chat_member(
                chat_id, user_id,
                ChatPermissions(can_send_messages=True, can_send_media_messages=False),
            )
            await moderation_repo.add_action(chat_id, user_id, "restrict", issued_by=bot_id)
        except Exception as e:
            logger.debug(f"فشل التقييد التلقائي: {e}")

    async def _direct_kick(self, client, chat_id, user_id, bot_id):
        try:
            await client.ban_chat_member(chat_id, user_id)
            await client.unban_chat_member(chat_id, user_id)
        except Exception as e:
            logger.debug(f"فشل الطرد التلقائي: {e}")

    async def _direct_ban(self, client, chat_id, user_id, bot_id, reason):
        try:
            await client.ban_chat_member(chat_id, user_id)
            await moderation_repo.add_action(
                chat_id, user_id, "ban", issued_by=bot_id, reason=reason,
            )
        except Exception as e:
            logger.debug(f"فشل الحظر التلقائي: {e}")


warn_engine = WarnEngine()
