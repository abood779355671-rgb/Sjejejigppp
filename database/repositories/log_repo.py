database/repositories/log_repo.py
═══════════════════════════════════════════════════════════════
مستودع السجلات: تسجيل الأحداث (Audit) والأخطاء.
═══════════════════════════════════════════════════════════════
"""

import json
import traceback as tb_module
from typing import Optional

from database.repositories.base_repo import BaseRepository
from core.logger import setup_logger

logger = setup_logger("log_repo")


class LogRepository(BaseRepository):
    """عمليات السجلات."""

    async def log_event(
        self,
        event_type: str,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        actor_id: Optional[int] = None,
        target_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> None:
        """
        تسجيل حدث في سجل التدقيق (Audit Log).

        Args:
            event_type: نوع الحدث (من EventType).
            chat_id: المجموعة.
            user_id: المستخدم المرتبط.
            actor_id: منفّذ الإجراء.
            target_id: المستهدف.
            details: تفاصيل إضافية (تُخزَّن كـ JSONB).
        """
        await self.db.execute(
            """
            INSERT INTO event_logs
                (event_type, chat_id, user_id, actor_id, target_id, details)
            VALUES ($1, $2, $3, $4, $5, $6);
            """,
            event_type, chat_id, user_id, actor_id, target_id,
            json.dumps(details or {}, ensure_ascii=False),
        )

    async def get_events(
        self,
        chat_id: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        جلب الأحداث مع تصفية اختيارية.
        نبني الاستعلام ديناميكياً بأمان (Parameterized).
        """
        conditions = []
        params = []
        idx = 1

        if chat_id is not None:
            conditions.append(f"chat_id = ${idx}")
            params.append(chat_id)
            idx += 1

        if event_type is not None:
            conditions.append(f"event_type = ${idx}")
            params.append(event_type)
            idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        query = f"""
            SELECT * FROM event_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${idx};
        """
        rows = await self.db.fetch(query, *params)
        return self.records_to_list(rows)

    async def log_error(
        self,
        error_type: str,
        message: str,
        traceback: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> None:
        """
        تسجيل خطأ في جدول error_logs.
        إن لم يُمرَّر traceback يُلتقط تلقائياً.
        """
        if traceback is None:
            traceback = tb_module.format_exc()

        try:
            await self.db.execute(
                """
                INSERT INTO error_logs
                    (error_type, message, traceback, chat_id, user_id)
                VALUES ($1, $2, $3, $4, $5);
                """,
                error_type, message, traceback, chat_id, user_id,
            )
        except Exception as e:
            # إن فشل تسجيل الخطأ في القاعدة، نسجله في الملف فقط
            logger.error(f"فشل تسجيل الخطأ في القاعدة: {e}")

    async def get_recent_errors(self, limit: int = 20) -> list[dict]:
        """جلب آخر الأخطاء (للوحة المطور)."""
        rows = await self.db.fetch(
            """
            SELECT id, error_type, message, chat_id, user_id, created_at
            FROM error_logs
            ORDER BY created_at DESC
            LIMIT $1;
            """,
            limit,
        )
        return self.records_to_list(rows)

    async def clear_old_logs(self, days: int = 30) -> int:
        """
        حذف السجلات الأقدم من عدد أيام (صيانة دورية).
        يُستدعى من مهمة مجدولة.
        """
        result = await self.db.execute(
            """
            DELETE FROM event_logs
            WHERE created_at < NOW() - ($1 || ' days')::INTERVAL;
            """,
            str(days),
        )
        # استخراج عدد الصفوف المحذوفة من "DELETE N"
        try:
            return int(result.split()[-1])
        except (ValueError, IndexError):
            return 0


# نسخة جاهزة
log_repo = LogRepository()
