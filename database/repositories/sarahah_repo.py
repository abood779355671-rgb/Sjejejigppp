database/repositories/sarahah_repo.py
═══════════════════════════════════════════════════════════════
مستودع نظام الصراحة (رسائل مجهولة).
═══════════════════════════════════════════════════════════════
"""

import secrets
from typing import Optional

from database.repositories.base_repo import BaseRepository
from core.logger import setup_logger

logger = setup_logger("sarahah_repo")


class SarahahRepository(BaseRepository):
    """عمليات الصراحة."""

    async def get_or_create_link(self, user_id: int) -> str:
        """
        جلب رابط الصراحة للمستخدم أو إنشاؤه.

        Returns:
            كود الرابط الفريد.
        """
        existing = await self.db.fetchval(
            "SELECT link_code FROM sarahah_links WHERE user_id = $1 AND is_active = TRUE;",
            user_id,
        )
        if existing:
            return existing

        # توليد كود فريد آمن
        link_code = secrets.token_urlsafe(8)
        await self.db.execute(
            """
            INSERT INTO sarahah_links (user_id, link_code, is_active)
            VALUES ($1, $2, TRUE);
            """,
            user_id, link_code,
        )
        return link_code

    async def get_link_owner(self, link_code: str) -> Optional[int]:
        """جلب صاحب رابط الصراحة."""
        return await self.db.fetchval(
            "SELECT user_id FROM sarahah_links WHERE link_code = $1 AND is_active = TRUE;",
            link_code,
        )

    async def save_message(
        self, link_code: str, receiver_id: int, content: str,
    ) -> Optional[int]:
        """حفظ رسالة مجهولة."""
        link_id = await self.db.fetchval(
            "SELECT id FROM sarahah_links WHERE link_code = $1;",
            link_code,
        )
        if not link_id:
            return None

        msg_id = await self.db.fetchval(
            """
            INSERT INTO sarahah_messages (link_id, receiver_id, content)
            VALUES ($1, $2, $3)
            RETURNING id;
            """,
            link_id, receiver_id, content,
        )
        return int(msg_id)

    async def mark_read(self, message_id: int) -> None:
        """تعليم رسالة كمقروءة."""
        await self.db.execute(
            "UPDATE sarahah_messages SET is_read = TRUE WHERE id = $1;",
            message_id,
        )


sarahah_repo = SarahahRepository()
