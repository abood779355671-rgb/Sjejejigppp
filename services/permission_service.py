services/permission_service.py
═══════════════════════════════════════════════════════════════
محرك الصلاحيات المركزي (Permission Engine).

المسؤوليات:
- تحديد رتبة المستخدم.
- فحص ما إذا كان يملك صلاحية معينة.
- تطبيق "القاعدة الذهبية": لا تعديل لرتبة أعلى أو مساوية.
- ربط كل صلاحية بالحد الأدنى للرتبة المطلوبة.

هذا هو المصدر الوحيد للحقيقة (Single Source of Truth) للصلاحيات.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional

from config.constants import RankLevel
from database.repositories.rank_repo import rank_repo
from database.repositories.user_repo import user_repo
from core.exceptions import (
    InsufficientRank,
    CannotModifyHigherRank,
    PermissionDenied,
)
from core.logger import setup_logger

logger = setup_logger("permission_service")


# ═══════════════════════════════════════════════════════════════
# مصفوفة الصلاحيات (Permission Matrix)
# كل صلاحية مرتبطة بالحد الأدنى للرتبة المطلوبة.
# هذا هو التطبيق البرمجي للجدول الذي صممناه في المرحلة الأولى.
# ═══════════════════════════════════════════════════════════════
PERMISSION_MATRIX: dict[str, int] = {
    # ─── صلاحيات عامة (كل الأعضاء) ───
    "use_replies":          RankLevel.MEMBER,
    "use_whisper":          RankLevel.MEMBER,
    "use_sarahah":          RankLevel.MEMBER,
    "use_media_download":   RankLevel.MEMBER,
    "use_info":             RankLevel.MEMBER,
    "use_quran":            RankLevel.MEMBER,

    # ─── المميز (1) ───
    "bypass_protection":    RankLevel.VIP,

    # ─── الأدمن (2) ───
    "mute":                 RankLevel.ADMIN,
    "unmute":               RankLevel.ADMIN,
    "restrict":             RankLevel.ADMIN,
    "unrestrict":           RankLevel.ADMIN,
    "ban":                  RankLevel.ADMIN,
    "unban":                RankLevel.ADMIN,
    "kick":                 RankLevel.ADMIN,
    "delete_messages":      RankLevel.ADMIN,
    "pin":                  RankLevel.ADMIN,
    "unpin":                RankLevel.ADMIN,
    "warn":                 RankLevel.ADMIN,

    # ─── المدير (3) ───
    "promote_vip":          RankLevel.MANAGER,
    "demote_vip":           RankLevel.MANAGER,
    "promote_admin":        RankLevel.MANAGER,
    "demote_admin":         RankLevel.MANAGER,
    "manage_protection":    RankLevel.MANAGER,
    "manage_welcome":       RankLevel.MANAGER,
    "manage_replies":       RankLevel.MANAGER,
    "manage_filters":       RankLevel.MANAGER,
    "manage_commands":      RankLevel.MANAGER,
    "manage_cleanup":       RankLevel.MANAGER,

    # ─── المالك (4) ───
    "promote_manager":      RankLevel.OWNER,
    "demote_manager":       RankLevel.OWNER,
    "view_logs":            RankLevel.OWNER,

    # ─── المالك الأساسي (5) ───
    "promote_owner":        RankLevel.MAIN_OWNER,
    "demote_owner":         RankLevel.MAIN_OWNER,

    # ─── المطور (6) ───
    "promote_main_owner":   RankLevel.DEVELOPER,
    "demote_main_owner":    RankLevel.DEVELOPER,
    "broadcast":            RankLevel.DEVELOPER,
    "backup":               RankLevel.DEVELOPER,
    "restore":              RankLevel.DEVELOPER,
    "maintenance":          RankLevel.DEVELOPER,
    "restart":              RankLevel.DEVELOPER,
    "global_ban":           RankLevel.DEVELOPER,
    "global_unban":         RankLevel.DEVELOPER,
    "view_bot_stats":       RankLevel.DEVELOPER,
    "view_error_logs":      RankLevel.DEVELOPER,
    "ban_group":            RankLevel.DEVELOPER,

    # ─── المطور الأساسي فقط (7) ───
    "manage_developers":    RankLevel.MAIN_DEVELOPER,
}


class PermissionService:
    """خدمة إدارة الصلاحيات."""

    # ───────────────────────────────────────────────
    # جلب الرتبة
    # ───────────────────────────────────────────────

    async def get_user_rank(self, chat_id: int, user_id: int) -> int:
        """
        جلب رتبة المستخدم (واجهة موحّدة).
        يفوّض إلى rank_repo الذي يتعامل مع Cache والمطورين.
        """
        return await rank_repo.get_rank(chat_id, user_id)

    # ───────────────────────────────────────────────
    # فحص الصلاحيات
    # ───────────────────────────────────────────────

    async def has_permission(
        self,
        chat_id: int,
        user_id: int,
        permission: str,
    ) -> bool:
        """
        فحص ما إذا كان المستخدم يملك صلاحية معينة.

        Args:
            chat_id: المجموعة.
            user_id: المستخدم.
            permission: اسم الصلاحية (من PERMISSION_MATRIX).

        Returns:
            True إن كان مسموحاً.
        """
        required_level = PERMISSION_MATRIX.get(permission)
        if required_level is None:
            logger.warning(f"صلاحية غير معرّفة: {permission}")
            return False

        user_level = await self.get_user_rank(chat_id, user_id)
        return user_level >= required_level

    async def require_permission(
        self,
        chat_id: int,
        user_id: int,
        permission: str,
    ) -> None:
        """
        التأكد من الصلاحية أو رفع استثناء.
        تُستخدم داخل الخدمات والمعالجات.

        Raises:
            PermissionDenied: إن لم يملك الصلاحية.
        """
        if not await self.has_permission(chat_id, user_id, permission):
            raise PermissionDenied(
                f"ليس لديك صلاحية: {permission}"
            )

    async def require_rank(
        self,
        chat_id: int,
        user_id: int,
        min_level: int,
    ) -> None:
        """
        التأكد من أن رتبة المستخدم >= المستوى المطلوب.

        Raises:
            InsufficientRank: إن كانت الرتبة أقل.
        """
        user_level = await self.get_user_rank(chat_id, user_id)
        if user_level < min_level:
            raise InsufficientRank()

    # ───────────────────────────────────────────────
    # القاعدة الذهبية: حماية تصعيد الصلاحيات
    # ───────────────────────────────────────────────

    async def can_modify_target(
        self,
        chat_id: int,
        actor_id: int,
        target_id: int,
    ) -> bool:
        """
        فحص ما إذا كان المنفّذ يستطيع تعديل (رفع/تنزيل/حظر/كتم) الهدف.

        القاعدة الذهبية:
        - لا يمكن تعديل رتبة أعلى من رتبتك.
        - لا يمكن تعديل رتبة مساوية لرتبتك.
        - المطور الأساسي يستطيع تعديل الجميع.

        Returns:
            True إن كان التعديل مسموحاً.
        """
        # المطور الأساسي يتجاوز كل القيود
        if await user_repo.is_main_developer(actor_id):
            return True

        actor_level = await self.get_user_rank(chat_id, actor_id)
        target_level = await self.get_user_rank(chat_id, target_id)

        # يجب أن تكون رتبة المنفّذ أعلى تماماً من الهدف
        return actor_level > target_level

    async def require_can_modify(
        self,
        chat_id: int,
        actor_id: int,
        target_id: int,
    ) -> None:
        """
        التأكد من إمكانية التعديل أو رفع استثناء.

        Raises:
            CannotModifyHigherRank: إن كان الهدف أعلى أو مساوياً.
        """
        # لا يمكن للمستخدم تعديل نفسه في الأوامر الإدارية
        if actor_id == target_id:
            raise CannotModifyHigherRank("لا يمكنك تنفيذ هذا الإجراء على نفسك")

        if not await self.can_modify_target(chat_id, actor_id, target_id):
            raise CannotModifyHigherRank()

    async def can_assign_rank(
        self,
        chat_id: int,
        actor_id: int,
        target_rank: int,
    ) -> bool:
        """
        فحص ما إذا كان المنفّذ يستطيع منح رتبة معينة.

        القاعدة: لا يمكن منح رتبة أعلى من رتبتك أو مساوية لها.
        مثال: المالك(4) لا يستطيع تعيين مالك آخر(4)، فقط مدير فأقل.

        Returns:
            True إن كان مسموحاً.
        """
        if await user_repo.is_main_developer(actor_id):
            return True

        actor_level = await self.get_user_rank(chat_id, actor_id)
        return actor_level > target_rank


# نسخة جاهزة
permission_service = PermissionService()
