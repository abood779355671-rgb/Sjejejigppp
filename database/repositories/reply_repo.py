database/repositories/reply_repo.py
═══════════════════════════════════════════════════════════════
مستودع الردود التلقائية.
يدعم: نصية/وسائط/Regex/كلمات مفتاحية/عشوائية.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional

from database.repositories.base_repo import BaseRepository
from core.logger import setup_logger

logger = setup_logger("reply_repo")


class ReplyRepository(BaseRepository):
    """عمليات الردود."""

    async def add_reply(
        self,
        chat_id: Optional[int],
        trigger: str,
        match_type: str,
        reply_type: str,
        content: Optional[str] = None,
        media_file_id: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> int:
        """إضافة رد وإرجاع معرّفه."""
        reply_id = await self.db.fetchval(
            """
            INSERT INTO replies
                (chat_id, trigger_text, match_type, reply_type,
                 reply_content, media_file_id, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id;
            """,
            chat_id, trigger, match_type, reply_type,
            content, media_file_id, created_by,
        )
        return int(reply_id)

    async def delete_reply(self, reply_id: int, chat_id: Optional[int]) -> bool:
        """حذف رد (يتحقق من المجموعة لمنع حذف ردود مجموعة أخرى)."""
        result = await self.db.execute(
            """
            DELETE FROM replies
            WHERE id = $1 AND (chat_id = $2 OR ($2 IS NULL AND chat_id IS NULL));
            """,
            reply_id, chat_id,
        )
        return "DELETE 1" in result

    async def delete_by_trigger(self, chat_id: Optional[int], trigger: str) -> int:
        """حذف كل الردود بكلمة محفّزة معينة."""
        result = await self.db.execute(
            """
            DELETE FROM replies
            WHERE trigger_text = $2
              AND (chat_id = $1 OR ($1 IS NULL AND chat_id IS NULL));
            """,
            chat_id, trigger,
        )
        try:
            return int(result.split()[-1])
        except (ValueError, IndexError):
            return 0

    async def get_replies_for_chat(self, chat_id: int) -> list[dict]:
        """
        جلب كل الردود المطبّقة على مجموعة:
        الردود الخاصة بها + الردود العامة (chat_id IS NULL).
        """
        rows = await self.db.fetch(
            """
            SELECT * FROM replies
            WHERE chat_id = $1 OR chat_id IS NULL
            ORDER BY chat_id NULLS LAST;
            """,
            chat_id,
        )
        return self.records_to_list(rows)

    async def list_replies(self, chat_id: Optional[int]) -> list[dict]:
        """قائمة ردود مجموعة (للعرض)."""
        rows = await self.db.fetch(
            """
            SELECT id, trigger_text, match_type, reply_type
            FROM replies
            WHERE chat_id = $1 OR ($1 IS NULL AND chat_id IS NULL)
            ORDER BY id;
            """,
            chat_id,
        )
        return self.records_to_list(rows)


reply_repo = ReplyRepository()
