database/repositories/filter_command_repo.py
═══════════════════════════════════════════════════════════════
مستودع الفلاتر (كلمات/روابط ممنوعة) والأوامر المخصصة.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional

from database.repositories.base_repo import BaseRepository
from core.logger import setup_logger

logger = setup_logger("filter_command_repo")


class FilterRepository(BaseRepository):
    """عمليات الفلاتر."""

    async def add_filter(
        self,
        chat_id: Optional[int],
        word: str,
        filter_type: str = "word",
        action: str = "delete",
    ) -> int:
        """إضافة فلتر."""
        filter_id = await self.db.fetchval(
            """
            INSERT INTO filters (chat_id, filter_word, filter_type, action)
            VALUES ($1, $2, $3, $4)
            RETURNING id;
            """,
            chat_id, word.lower().strip(), filter_type, action,
        )
        return int(filter_id)

    async def delete_filter(self, chat_id: Optional[int], word: str) -> int:
        """حذف فلتر بالكلمة."""
        result = await self.db.execute(
            """
            DELETE FROM filters
            WHERE filter_word = $2
              AND (chat_id = $1 OR ($1 IS NULL AND chat_id IS NULL));
            """,
            chat_id, word.lower().strip(),
        )
        try:
            return int(result.split()[-1])
        except (ValueError, IndexError):
            return 0

    async def get_filters_for_chat(self, chat_id: int) -> list[dict]:
        """جلب فلاتر المجموعة + الفلاتر العامة."""
        rows = await self.db.fetch(
            """
            SELECT * FROM filters
            WHERE chat_id = $1 OR chat_id IS NULL;
            """,
            chat_id,
        )
        return self.records_to_list(rows)

    async def list_filters(self, chat_id: Optional[int]) -> list[dict]:
        """قائمة فلاتر المجموعة."""
        rows = await self.db.fetch(
            """
            SELECT id, filter_word, filter_type, action FROM filters
            WHERE chat_id = $1 OR ($1 IS NULL AND chat_id IS NULL)
            ORDER BY id;
            """,
            chat_id,
        )
        return self.records_to_list(rows)


class CommandRepository(BaseRepository):
    """عمليات الأوامر المخصصة."""

    async def add_command(
        self,
        chat_id: Optional[int],
        command: str,
        response: Optional[str] = None,
        media_file_id: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> None:
        """إضافة أو تحديث أمر مخصص."""
        await self.db.execute(
            """
            INSERT INTO custom_commands
                (chat_id, command, response, media_file_id, created_by)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (chat_id, command) DO UPDATE SET
                response      = EXCLUDED.response,
                media_file_id = EXCLUDED.media_file_id;
            """,
            chat_id, command.lower().strip(), response, media_file_id, created_by,
        )

    async def delete_command(self, chat_id: Optional[int], command: str) -> bool:
        """حذف أمر مخصص."""
        result = await self.db.execute(
            """
            DELETE FROM custom_commands
            WHERE command = $2
              AND (chat_id = $1 OR ($1 IS NULL AND chat_id IS NULL));
            """,
            chat_id, command.lower().strip(),
        )
        return "DELETE 1" in result

    async def get_command(self, chat_id: int, command: str) -> Optional[dict]:
        """
        جلب أمر مخصص (يفضّل أمر المجموعة على العام).
        """
        record = await self.db.fetchrow(
            """
            SELECT * FROM custom_commands
            WHERE command = $2 AND (chat_id = $1 OR chat_id IS NULL)
            ORDER BY chat_id NULLS LAST
            LIMIT 1;
            """,
            chat_id, command.lower().strip(),
        )
        return self.record_to_dict(record)

    async def list_commands(self, chat_id: Optional[int]) -> list[dict]:
        """قائمة الأوامر المخصصة."""
        rows = await self.db.fetch(
            """
            SELECT command, response FROM custom_commands
            WHERE chat_id = $1 OR ($1 IS NULL AND chat_id IS NULL)
            ORDER BY command;
            """,
            chat_id,
        )
        return self.records_to_list(rows)


filter_repo = FilterRepository()
command_repo = CommandRepository()
