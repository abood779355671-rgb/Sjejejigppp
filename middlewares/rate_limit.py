middlewares/rate_limit.py
═══════════════════════════════════════════════════════════════
مكافحة الفلود (Anti-Flood) و Rate Limiting العام.

يستخدم نمط النافذة الزمنية (Sliding Window) عبر Redis:
- عدّاد لكل مستخدم لكل مجموعة.
- يزداد مع كل رسالة، ينتهي بعد عدد ثوانٍ.
- عند تجاوز الحد → يُعتبر فلود.
═══════════════════════════════════════════════════════════════
"""

from config.constants import RedisKeys
from config.settings import settings
from core.redis_client import redis_client
from database.repositories.user_repo import user_repo


class RateLimitMiddleware:
    """مكافحة الفلود العام (على مستوى البوت)."""

    @staticmethod
    async def check_global_flood(user_id: int) -> bool:
        """
        فحص الفلود العام للمستخدم (حماية البوت نفسه من الإغراق).

        Returns:
            True إن تجاوز المستخدم الحد (يجب التجاهل/التحذير).
        """
        # المطورون معفون
        if await user_repo.is_developer(user_id):
            return False

        key = RedisKeys.rate_limit(user_id, "global")
        current = await redis_client.incr_with_expire(
            key, settings.RATE_LIMIT_SECONDS
        )
        return current > settings.RATE_LIMIT_MESSAGES

    @staticmethod
    async def check_group_flood(
        chat_id: int,
        user_id: int,
        limit: int,
        seconds: int,
    ) -> bool:
        """
        فحص الفلود داخل مجموعة (حسب إعدادات الحماية لكل مجموعة).

        Args:
            chat_id: المجموعة.
            user_id: المستخدم.
            limit: عدد الرسائل المسموح.
            seconds: خلال كم ثانية.

        Returns:
            True إن تجاوز الحد.
        """
        key = RedisKeys.flood(chat_id, user_id)
        current = await redis_client.incr_with_expire(key, seconds)
        return current > limit

    @staticmethod
    async def reset_flood(chat_id: int, user_id: int) -> None:
        """إعادة تعيين عدّاد الفلود (بعد تطبيق عقوبة)."""
        await redis_client.delete(RedisKeys.flood(chat_id, user_id))


rate_limit_middleware = RateLimitMiddleware()
