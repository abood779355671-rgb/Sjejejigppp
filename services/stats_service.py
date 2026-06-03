services/stats_service.py
═══════════════════════════════════════════════════════════════
خدمة الإحصائيات.
- إحصائيات لحظية من قاعدة البيانات.
- عدّاد الرسائل اليومية عبر Redis (يُحفظ دورياً).
═══════════════════════════════════════════════════════════════
"""

import time
from datetime import date

from database.repositories.user_repo import user_repo
from database.repositories.group_repo import group_repo
from core.database import db
from core.redis_client import redis_client
from core.logger import setup_logger

logger = setup_logger("stats_service")

# وقت بدء تشغيل البوت (لحساب uptime)
_START_TIME = time.time()


class StatsService:
    """خدمة الإحصائيات."""

    @staticmethod
    def _today_key() -> str:
        """مفتاح Redis لعدّاد رسائل اليوم."""
        return f"stats:messages:{date.today().isoformat()}"

    async def increment_message_count(self) -> None:
        """زيادة عدّاد الرسائل اليومي (يُستدعى من خط الأنابيب)."""
        key = self._today_key()
        await redis_client.incr(key)
        # ضمان انتهاء صلاحية بعد يومين (تنظيف تلقائي)
        await redis_client.expire(key, 172800)

    async def get_today_messages(self) -> int:
        """جلب عدد رسائل اليوم."""
        value = await redis_client.get(self._today_key())
        return int(value) if value else 0

    async def persist_daily_stats(self) -> None:
        """
        حفظ الإحصائيات اليومية من Redis إلى Postgres.
        يُستدعى من مهمة مجدولة (كل ساعة مثلاً).
        """
        today = date.today()
        messages = await self.get_today_messages()

        await db.execute(
            """
            INSERT INTO daily_stats (stat_date, chat_id, messages_count)
            VALUES ($1, NULL, $2)
            ON CONFLICT (stat_date, chat_id) DO UPDATE SET
                messages_count = EXCLUDED.messages_count;
            """,
            today, messages,
        )
        logger.info(f"تم حفظ إحصائيات اليوم: {messages} رسالة")

    def get_uptime(self) -> str:
        """حساب وقت التشغيل بصيغة مقروءة."""
        seconds = int(time.time() - _START_TIME)
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}ي")
        if hours:
            parts.append(f"{hours}س")
        parts.append(f"{minutes}د")
        return " ".join(parts)

    async def get_full_stats(self) -> dict:
        """جمع كل الإحصائيات للوحة المطور."""
        users = await user_repo.get_total_users()
        groups = await group_repo.get_total_groups()
        today_messages = await self.get_today_messages()
        developers = len(await user_repo.get_all_developers())

        return {
            "users": users,
            "groups": groups,
            "today_messages": today_messages,
            "developers": developers,
            "uptime": self.get_uptime(),
        }


stats_service = StatsService()
