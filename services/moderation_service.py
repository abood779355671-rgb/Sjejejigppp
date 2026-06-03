services/moderation_service.py
═══════════════════════════════════════════════════════════════
خدمة الإدارة: حظر/كتم/طرد/تقييد/تثبيت.
تتعامل مع Pyrogram لتطبيق الإجراء فعلياً في تيليجرام،
وتسجّله في قاعدة البيانات والسجل.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional
from datetime import datetime, timedelta

from pyrogram import Client
from pyrogram.types import ChatPermissions
from pyrogram.errors import RPCError

from database.repositories.moderation_repo import moderation_repo
from database.repositories.log_repo import log_repo
from services.permission_service import permission_service
from config.constants import ModerationAction, EventType
from core.exceptions import BotException
from core.logger import setup_logger

logger = setup_logger("moderation_service")


# صلاحيات الكتم الكامل (لا شيء مسموح)
_MUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_send_polls=False,
    can_add_web_page_previews=False,
)

# صلاحيات العضو العادي (فك الكتم)
_FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_send_polls=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
)


class ModerationService:
    """خدمة الإدارة."""

    # ───────────────────────────────────────────────
    # الحظر
    # ───────────────────────────────────────────────

    async def ban(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        target_id: int,
        reason: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> str:
        """حظر مستخدم من المجموعة."""
        await permission_service.require_permission(chat_id, actor_id, "ban")
        await permission_service.require_can_modify(chat_id, actor_id, target_id)

        expires_at = None
        until_date = None
        if duration:
            expires_at = datetime.utcnow() + timedelta(seconds=duration)
            until_date = expires_at

        try:
            await client.ban_chat_member(chat_id, target_id, until_date=until_date)
        except RPCError as e:
            raise BotException(f"تعذّر الحظر: {e}")

        await moderation_repo.add_action(
            chat_id, target_id, ModerationAction.BAN.value,
            issued_by=actor_id, reason=reason, expires_at=expires_at,
        )
        await log_repo.log_event(
            EventType.USER_BANNED.value,
            chat_id=chat_id, actor_id=actor_id, target_id=target_id,
            details={"reason": reason, "duration": duration},
        )
        return "✅ تم حظر المستخدم"

    async def unban(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        target_id: int,
    ) -> str:
        """فك حظر مستخدم."""
        await permission_service.require_permission(chat_id, actor_id, "unban")

        try:
            await client.unban_chat_member(chat_id, target_id)
        except RPCError as e:
            raise BotException(f"تعذّر فك الحظر: {e}")

        await moderation_repo.remove_action(chat_id, target_id, ModerationAction.BAN.value)
        return "✅ تم فك حظر المستخدم"

    # ───────────────────────────────────────────────
    # الكتم
    # ───────────────────────────────────────────────

    async def mute(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        target_id: int,
        reason: Optional[str] = None,
        duration: Optional[int] = None,
    ) -> str:
        """كتم مستخدم."""
        await permission_service.require_permission(chat_id, actor_id, "mute")
        await permission_service.require_can_modify(chat_id, actor_id, target_id)

        expires_at = None
        until_date = None
        if duration:
            expires_at = datetime.utcnow() + timedelta(seconds=duration)
            until_date = expires_at

        try:
            await client.restrict_chat_member(
                chat_id, target_id, _MUTED_PERMISSIONS, until_date=until_date,
            )
        except RPCError as e:
            raise BotException(f"تعذّر الكتم: {e}")

        await moderation_repo.add_action(
            chat_id, target_id, ModerationAction.MUTE.value,
            issued_by=actor_id, reason=reason, expires_at=expires_at,
        )
        await log_repo.log_event(
            EventType.USER_MUTED.value,
            chat_id=chat_id, actor_id=actor_id, target_id=target_id,
            details={"reason": reason, "duration": duration},
        )
        return "✅ تم كتم المستخدم"

    async def unmute(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        target_id: int,
    ) -> str:
        """فك كتم مستخدم."""
        await permission_service.require_permission(chat_id, actor_id, "unmute")

        try:
            await client.restrict_chat_member(chat_id, target_id, _FULL_PERMISSIONS)
        except RPCError as e:
            raise BotException(f"تعذّر فك الكتم: {e}")

        await moderation_repo.remove_action(chat_id, target_id, ModerationAction.MUTE.value)
        return "✅ تم فك كتم المستخدم"

    # ───────────────────────────────────────────────
    # التقييد (كتم جزئي - منع الوسائط فقط)
    # ───────────────────────────────────────────────

    async def restrict(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        target_id: int,
        duration: Optional[int] = None,
    ) -> str:
        """تقييد مستخدم (منع الوسائط، السماح بالنص)."""
        await permission_service.require_permission(chat_id, actor_id, "restrict")
        await permission_service.require_can_modify(chat_id, actor_id, target_id)

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_send_polls=False,
            can_add_web_page_previews=False,
        )
        expires_at = None
        until_date = None
        if duration:
            expires_at = datetime.utcnow() + timedelta(seconds=duration)
            until_date = expires_at

        try:
            await client.restrict_chat_member(
                chat_id, target_id, permissions, until_date=until_date,
            )
        except RPCError as e:
            raise BotException(f"تعذّر التقييد: {e}")

        await moderation_repo.add_action(
            chat_id, target_id, ModerationAction.RESTRICT.value,
            issued_by=actor_id, expires_at=expires_at,
        )
        return "✅ تم تقييد المستخدم (ممنوع من الوسائط)"

    async def unrestrict(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        target_id: int,
    ) -> str:
        """فك تقييد مستخدم."""
        await permission_service.require_permission(chat_id, actor_id, "unrestrict")

        try:
            await client.restrict_chat_member(chat_id, target_id, _FULL_PERMISSIONS)
        except RPCError as e:
            raise BotException(f"تعذّر فك التقييد: {e}")

        await moderation_repo.remove_action(chat_id, target_id, ModerationAction.RESTRICT.value)
        return "✅ تم فك تقييد المستخدم"

    # ───────────────────────────────────────────────
    # الطرد
    # ───────────────────────────────────────────────

    async def kick(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        target_id: int,
    ) -> str:
        """طرد مستخدم (حظر ثم فك فوري ليتمكن من العودة)."""
        await permission_service.require_permission(chat_id, actor_id, "kick")
        await permission_service.require_can_modify(chat_id, actor_id, target_id)

        try:
            await client.ban_chat_member(chat_id, target_id)
            await client.unban_chat_member(chat_id, target_id)
        except RPCError as e:
            raise BotException(f"تعذّر الطرد: {e}")

        await log_repo.log_event(
            EventType.USER_BANNED.value,
            chat_id=chat_id, actor_id=actor_id, target_id=target_id,
            details={"action": "kick"},
        )
        return "✅ تم طرد المستخدم"

    # ───────────────────────────────────────────────
    # التثبيت
    # ───────────────────────────────────────────────

    async def pin(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        message_id: int,
    ) -> str:
        """تثبيت رسالة."""
        await permission_service.require_permission(chat_id, actor_id, "pin")
        try:
            await client.pin_chat_message(chat_id, message_id, disable_notification=False)
        except RPCError as e:
            raise BotException(f"تعذّر التثبيت: {e}")
        return "📌 تم تثبيت الرسالة"

    async def unpin(
        self,
        client: Client,
        chat_id: int,
        actor_id: int,
        message_id: Optional[int] = None,
    ) -> str:
        """إلغاء تثبيت رسالة (أو الكل)."""
        await permission_service.require_permission(chat_id, actor_id, "unpin")
        try:
            if message_id:
                await client.unpin_chat_message(chat_id, message_id)
            else:
                await client.unpin_all_chat_messages(chat_id)
        except RPCError as e:
            raise BotException(f"تعذّر إلغاء التثبيت: {e}")
        return "✅ تم إلغاء التثبيت"

    # ───────────────────────────────────────────────
    # فك العقوبات المؤقتة المنتهية (مهمة مجدولة)
    # ───────────────────────────────────────────────

    async def process_expired_actions(self, client: Client) -> int:
        """
        فك العقوبات المؤقتة المنتهية.
        يُستدعى من المُجدول دورياً.

        Returns:
            عدد العقوبات التي فُكّت.
        """
        expired = await moderation_repo.get_expired_actions()
        count = 0
        for action in expired:
            try:
                chat_id = action["chat_id"]
                user_id = action["user_id"]
                atype = action["action_type"]

                if atype == ModerationAction.BAN.value:
                    await client.unban_chat_member(chat_id, user_id)
                elif atype in (ModerationAction.MUTE.value, ModerationAction.RESTRICT.value):
                    await client.restrict_chat_member(chat_id, user_id, _FULL_PERMISSIONS)

                await moderation_repo.deactivate_action_by_id(action["id"])
                count += 1
            except Exception as e:
                logger.debug(f"فشل فك عقوبة منتهية: {e}")
                # نلغيها من القاعدة على أي حال لتجنب المحاولة المتكررة
                await moderation_repo.deactivate_action_by_id(action["id"])
        return count


moderation_service = ModerationService()
