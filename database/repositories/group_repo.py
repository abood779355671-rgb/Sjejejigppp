database/repositories/group_repo.py
═══════════════════════════════════════════════════════════════
مستودع المجموعات: عمليات قاعدة البيانات المتعلقة بالمجموعات.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional

from database.repositories.base_repo import BaseRepository
from core.logger import setup_logger

logger = setup_logger("group_repo")


class GroupRepository(BaseRepository):
    """عمليات المجموعات."""

    async def upsert_group(
        self,
        chat_id: int,
        title: Optional[str] = None,
        username: Optional[str] = None,
        chat_type: Optional[str] = None,
        added_by: Optional[int] = None,
    ) -> None:
        """
        إدراج مجموعة جديدة أو تحديث بياناتها.
        عند إعادة الانضمام تُعاد is_active إلى TRUE.
        """
        await self.db.execute(
            """
            INSERT INTO groups (chat_id, title, username, chat_type, added_by, is_active)
            VALUES ($1, $2, $3, $4, $5, TRUE)
            ON CONFLICT (chat_id) DO UPDATE SET
                title     = EXCLUDED.title,
                username  = EXCLUDED.username,
                is_active = TRUE,
                left_at   = NULL;
            """,
            chat_id, title, username, chat_type, added_by,
        )

    async def get_group(self, chat_id: int) -> Optional[dict]:
        """جلب مجموعة بمعرّفها."""
        record = await self.db.fetchrow(
            "SELECT * FROM groups WHERE chat_id = $1;",
            chat_id,
        )
        return self.record_to_dict(record)

    async def set_inactive(self, chat_id: int) -> None:
        """تعليم المجموعة كغير نشطة (عند خروج البوت منها)."""
        await self.db.execute(
            """
            UPDATE groups
            SET is_active = FALSE, left_at = NOW()
            WHERE chat_id = $1;
            """,
            chat_id,
        )

    async def set_banned(self, chat_id: int, banned: bool) -> None:
        """حظر/فك حظر مجموعة من استخدام البوت."""
        await self.db.execute(
            "UPDATE groups SET is_banned = $2 WHERE chat_id = $1;",
            chat_id, banned,
        )

    async def update_members_count(self, chat_id: int, count: int) -> None:
        """تحديث عدد الأعضاء."""
        await self.db.execute(
            "UPDATE groups SET members_count = $2 WHERE chat_id = $1;",
            chat_id, count,
        )

    async def get_total_groups(self) -> int:
        """العدد الكلي للمجموعات النشطة (للإحصائيات)."""
        return await self.db.fetchval(
            "SELECT COUNT(*) FROM groups WHERE is_active = TRUE;"
        ) or 0

    async def get_all_active_group_ids(self) -> list[int]:
        """جلب معرّفات كل المجموعات النشطة (للإذاعة)."""
        rows = await self.db.fetch(
            """
            SELECT chat_id FROM groups
            WHERE is_active = TRUE AND is_banned = FALSE;
            """
        )
        return [row["chat_id"] for row in rows]


# نسخة جاهزة
group_repo = GroupRepository()
