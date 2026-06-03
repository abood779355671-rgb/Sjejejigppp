middlewares/maintenance.py
═══════════════════════════════════════════════════════════════
فحص وضع الصيانة.
عند تفعيله، فقط المطورون يستطيعون استخدام البوت.
يُقرأ من Redis للسرعة (يُفحص في كل رسالة).
═══════════════════════════════════════════════════════════════
"""

from config.constants import RedisKeys
from core.redis_client import redis_client
from database.repositories.user_repo import user_repo


class MaintenanceMiddleware:
    """فحص وضع الصيانة."""

    @staticmethod
    async def is_maintenance() -> bool:
        """هل البوت في وضع الصيانة؟ (يُقرأ من Redis)."""
        value = await redis_client.get(RedisKeys.MAINTENANCE)
        return value == "1"

    @staticmethod
    async def should_block(user_id: int) -> bool:
        """
        هل يجب حظر هذا المستخدم بسبب الصيانة؟

        Returns:
            True إن كانت صيانة والمستخدم ليس مطوراً.
        """
        if not await MaintenanceMiddleware.is_maintenance():
            return False

        # المطورون لا يُحظرون أثناء الصيانة
        is_dev = await user_repo.is_developer(user_id)
        return not is_dev

    @staticmethod
    async def set_maintenance(enabled: bool) -> None:
        """تفعيل/تعطيل وضع الصيانة."""
        if enabled:
            await redis_client.set(RedisKeys.MAINTENANCE, "1")
        else:
            await redis_client.delete(RedisKeys.MAINTENANCE)


maintenance_middleware = MaintenanceMiddleware()
