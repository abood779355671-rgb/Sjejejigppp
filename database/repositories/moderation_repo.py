database/repositories/moderation_repo.py
═══════════════════════════════════════════════════════════════
مستودع إجراءات الإدارة والإنذارات.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional
from datetime import datetime

from database.repositories.base_repo import BaseRepository
from core.logger import setup_logger

logger = setup_logger("moderation_repo")


class ModerationRepository(BaseRepository):
    """عمليات الإدارة (حظر/كتم/تقييد) والإنذارات."""

    # ───────────────────────────────────────────────
    # إجراءات الإدارة
    # ───────────────────────────────────────────────

    async def add_action(
        self,
        chat_id: int,
        user_id: int,
        action_type: str,
        issued_by: int,
        reason: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """
        تسجيل إجراء إداري (حظر/كتم/تقييد).
        يُلغي أي إجراء نشط سابق من نفس النوع قبل إضافة الجديد.
        """
        # إلغاء الإجراءات النشطة السابقة من نفس النوع
        await self.db.execute(
            """
            UPDATE moderation_actions
            SET is_active = FALSE
            WHERE chat_id = $1 AND user_id = $2
              AND action_type = $3 AND is_active = TRUE;
            """,
            chat_id, user_id, action_type,
        )
        # إضافة الإجراء الجديد
        await self.db.execute(
            """
            INSERT INTO moderation_actions
                (chat_id, user_id, action_type, reason, issued_by, expires_at, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, TRUE);
            """,
            chat_id, user_id, action_type, reason, issued_by, expires_at,
        )

    async def remove_action(
        self,
        chat_id: int,
        user_id: int,
        action_type: str,
    ) -> None:
        """إلغاء إجراء نشط (فك حظر/كتم/تقييد)."""
        await self.db.execute(
            """
            UPDATE moderation_actions
            SET is_active = FALSE
            WHERE chat_id = $1 AND user_id = $2
              AND action_type = $3 AND is_active = TRUE;
            """,
            chat_id, user_id, action_type,
        )

    async def is_action_active(
        self,
        chat_id: int,
        user_id: int,
        action_type: str,
    ) -> bool:
        """فحص ما إذا كان هناك إجراء نشط."""
        result = await self.db.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM moderation_actions
                WHERE chat_id = $1 AND user_id = $2
                  AND action_type = $3 AND is_active = TRUE
            );
            """,
            chat_id, user_id, action_type,
        )
        return bool(result)

    async def get_expired_actions(self) -> list[dict]:
        """
        جلب الإجراءات المؤقتة المنتهية (لفكها تلقائياً).
        يُستدعى من مهمة مجدولة.
        """
        rows = await self.db.fetch(
            """
            SELECT id, chat_id, user_id, action_type
            FROM moderation_actions
            WHERE is_active = TRUE
              AND expires_at IS NOT NULL
              AND expires_at <= NOW();
            """
        )
        return self.records_to_list(rows)

    async def deactivate_action_by_id(self, action_id: int) -> None:
        """إلغاء إجراء بمعرّفه (بعد انتهاء مدته)."""
        await self.db.execute(
            "UPDATE moderation_actions SET is_active = FALSE WHERE id = $1;",
            action_id,
        )

    # ───────────────────────────────────────────────
    # الإنذارات
    # ───────────────────────────────────────────────

    async def add_warn(
        self,
        chat_id: int,
        user_id: int,
        warned_by: int,
        reason: Optional[str] = None,
    ) -> int:
        """
        إضافة إنذار وإرجاع العدد الجديد.
        يستخدم Upsert ذرّي لزيادة العدّاد.
        """
        new_count = await self.db.fetchval(
            """
            INSERT INTO warns (chat_id, user_id, count, reason, warned_by)
            VALUES ($1, $2, 1, $3, $4)
            ON CONFLICT (chat_id, user_id) DO UPDATE SET
                count     = warns.count + 1,
                reason    = EXCLUDED.reason,
                warned_by = EXCLUDED.warned_by,
                updated_at = NOW()
            RETURNING count;
            """,
            chat_id, user_id, reason, warned_by,
        )
        return int(new_count)

    async def get_warns(self, chat_id: int, user_id: int) -> int:
        """جلب عدد إنذارات مستخدم."""
        count = await self.db.fetchval(
            "SELECT count FROM warns WHERE chat_id = $1 AND user_id = $2;",
            chat_id, user_id,
        )
        return int(count) if count else 0

    async def reset_warns(self, chat_id: int, user_id: int) -> None:
        """إعادة تعيين إنذارات مستخدم (حذفها)."""
        await self.db.execute(
            "DELETE FROM warns WHERE chat_id = $1 AND user_id = $2;",
            chat_id, user_id,
        )


# نسخة جاهزة
moderation_repo = ModerationRepository()
