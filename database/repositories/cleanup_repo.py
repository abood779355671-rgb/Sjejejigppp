database/repositories/cleanup_repo.py
═══════════════════════════════════════════════════════════════
مستودع إعدادات التنظيف التلقائي.
═══════════════════════════════════════════════════════════════
"""

from database.repositories.base_repo import BaseRepository
from config.constants import Limits


class CleanupRepository(BaseRepository):
    """عمليات التنظيف التلقائي."""

    _FIELDS = {"clean_photos", "clean_videos", "clean_files", "clean_albums"}

    async def ensure_settings(self, chat_id: int) -> None:
        await self.db.execute(
            "INSERT INTO auto_cleanup (chat_id) VALUES ($1) ON CONFLICT (chat_id) DO NOTHING;",
            chat_id,
        )

    async def get_settings(self, chat_id: int) -> dict:
        await self.ensure_settings(chat_id)
        record = await self.db.fetchrow(
            "SELECT * FROM auto_cleanup WHERE chat_id = $1;", chat_id,
        )
        return self.record_to_dict(record) or {}

    async def toggle(self, chat_id: int, field: str, value: bool) -> None:
        if field not in self._FIELDS:
            return
        await self.ensure_settings(chat_id)
        await self.db.execute(
            f"UPDATE auto_cleanup SET {field} = $2, updated_at = NOW() WHERE chat_id = $1;",
            chat_id, value,
        )

    async def set_delete_after(self, chat_id: int, seconds: int) -> None:
        await self.ensure_settings(chat_id)
        await self.db.execute(
            "UPDATE auto_cleanup SET delete_after = $2 WHERE chat_id = $1;",
            chat_id, seconds,
        )


cleanup_repo = CleanupRepository()
