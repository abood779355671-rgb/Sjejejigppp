services/rank_service.py
═══════════════════════════════════════════════════════════════
خدمة الرتب: رفع وتنزيل الرتب مع تطبيق القاعدة الذهبية.
كل عملية تتحقق من الصلاحيات قبل التنفيذ وتُسجَّل في السجل.
═══════════════════════════════════════════════════════════════
"""

from database.repositories.rank_repo import rank_repo
from database.repositories.user_repo import user_repo
from database.repositories.log_repo import log_repo
from services.permission_service import permission_service
from config.constants import RankLevel, RANK_NAMES_AR, EventType
from core.exceptions import CannotModifyHigherRank, PermissionDenied
from core.logger import setup_logger

logger = setup_logger("rank_service")


# خريطة: اسم الصلاحية المطلوبة لمنح كل رتبة
_PROMOTE_PERMISSION = {
    RankLevel.VIP: "promote_vip",
    RankLevel.ADMIN: "promote_admin",
    RankLevel.MANAGER: "promote_manager",
    RankLevel.OWNER: "promote_owner",
    RankLevel.MAIN_OWNER: "promote_main_owner",
}

_DEMOTE_PERMISSION = {
    RankLevel.VIP: "demote_vip",
    RankLevel.ADMIN: "demote_admin",
    RankLevel.MANAGER: "demote_manager",
    RankLevel.OWNER: "demote_owner",
    RankLevel.MAIN_OWNER: "demote_main_owner",
}


class RankService:
    """خدمة إدارة الرتب."""

    async def promote(
        self,
        chat_id: int,
        actor_id: int,
        target_id: int,
        target_rank: int,
    ) -> str:
        """
        رفع مستخدم لرتبة.

        التحققات:
        1. المنفّذ يملك صلاحية منح هذه الرتبة.
        2. لا يرفع نفسه.
        3. لا يمنح رتبة أعلى/مساوية لرتبته (القاعدة الذهبية).
        4. لا يعدّل هدفاً أعلى منه.

        Returns:
            رسالة نجاح عربية.

        Raises:
            PermissionDenied / CannotModifyHigherRank.
        """
        # 1. صلاحية منح هذه الرتبة
        permission = _PROMOTE_PERMISSION.get(target_rank)
        if permission is None:
            raise PermissionDenied("رتبة غير صالحة")
        await permission_service.require_permission(chat_id, actor_id, permission)

        # 2. لا يرفع نفسه
        if actor_id == target_id:
            raise CannotModifyHigherRank("لا يمكنك تعديل رتبتك بنفسك")

        # 3. القاعدة الذهبية: لا يمنح رتبة >= رتبته
        if not await permission_service.can_assign_rank(chat_id, actor_id, target_rank):
            raise CannotModifyHigherRank(
                "لا يمكنك منح رتبة أعلى من رتبتك أو مساوية لها"
            )

        # 4. لا يعدّل هدفاً أعلى منه
        await permission_service.require_can_modify(chat_id, actor_id, target_id)

        # تنفيذ
        await user_repo.upsert_user(user_id=target_id)
        await rank_repo.set_rank(chat_id, target_id, target_rank, promoted_by=actor_id)

        # تسجيل
        await log_repo.log_event(
            EventType.RANK_PROMOTED.value,
            chat_id=chat_id,
            actor_id=actor_id,
            target_id=target_id,
            details={"rank": int(target_rank)},
        )

        rank_name = RANK_NAMES_AR[RankLevel(target_rank)]
        return f"✅ تم رفع المستخدم إلى رتبة ({rank_name})"

    async def demote(
        self,
        chat_id: int,
        actor_id: int,
        target_id: int,
        from_rank: int,
    ) -> str:
        """
        تنزيل مستخدم من رتبة (يعيده عضواً).

        Args:
            from_rank: الرتبة المراد التنزيل منها (لتحديد الصلاحية).

        Returns:
            رسالة نجاح عربية.
        """
        # 1. صلاحية التنزيل من هذه الرتبة
        permission = _DEMOTE_PERMISSION.get(from_rank)
        if permission is None:
            raise PermissionDenied("رتبة غير صالحة")
        await permission_service.require_permission(chat_id, actor_id, permission)

        # 2. لا ينزّل نفسه
        if actor_id == target_id:
            raise CannotModifyHigherRank("لا يمكنك تنزيل نفسك")

        # 3. لا يعدّل هدفاً أعلى منه
        await permission_service.require_can_modify(chat_id, actor_id, target_id)

        # تنفيذ
        await rank_repo.remove_rank(chat_id, target_id)

        # تسجيل
        await log_repo.log_event(
            EventType.RANK_DEMOTED.value,
            chat_id=chat_id,
            actor_id=actor_id,
            target_id=target_id,
            details={"from_rank": int(from_rank)},
        )

        rank_name = RANK_NAMES_AR[RankLevel(from_rank)]
        return f"✅ تم تنزيل المستخدم من رتبة ({rank_name})"

    async def get_user_rank_name(self, chat_id: int, user_id: int) -> str:
        """جلب اسم رتبة المستخدم العربي."""
        level = await rank_repo.get_rank(chat_id, user_id)
        return RANK_NAMES_AR.get(RankLevel(level), "عضو")


rank_service = RankService()
