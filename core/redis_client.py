core/redis_client.py
═══════════════════════════════════════════════════════════════
إدارة اتصال Redis باستخدام redis-py (async).

يُستخدم Redis لـ:
- Cache (تقليل ضغط Postgres)
- Rate Limiting / Anti-Flood
- إدارة الحالات (FSM)
- الهمسات المؤقتة
═══════════════════════════════════════════════════════════════
"""

from typing import Optional, Any

import redis.asyncio as aioredis

from config.settings import settings
from core.logger import setup_logger
from core.exceptions import RedisException

logger = setup_logger("redis")


class RedisClient:
    """
    مدير اتصال Redis (Singleton).
    يوفر واجهة مبسطة للعمليات الأكثر استخداماً.
    """

    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None

    # ───────────────────────────────────────────────
    # الاتصال والإغلاق
    # ───────────────────────────────────────────────

    async def connect(self) -> None:
        """إنشاء الاتصال بـ Redis."""
        if self._client is not None:
            logger.warning("اتصال Redis موجود مسبقاً")
            return

        try:
            self._client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,  # إرجاع str بدلاً من bytes
                max_connections=50,
                socket_keepalive=True,
                health_check_interval=30,
            )
            # اختبار الاتصال
            await self._client.ping()
            logger.info("✅ تم الاتصال بـ Redis بنجاح")
        except Exception as e:
            logger.critical(f"❌ فشل الاتصال بـ Redis: {e}")
            raise RedisException(f"فشل الاتصال بـ Redis: {e}")

    async def disconnect(self) -> None:
        """إغلاق الاتصال بأمان."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("تم إغلاق الاتصال بـ Redis")

    @property
    def client(self) -> aioredis.Redis:
        """الحصول على عميل Redis مع التأكد من وجوده."""
        if self._client is None:
            raise RedisException("Redis غير متصل. استدعِ connect() أولاً")
        return self._client

    # ───────────────────────────────────────────────
    # عمليات String
    # ───────────────────────────────────────────────

    async def get(self, key: str) -> Optional[str]:
        """جلب قيمة."""
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> None:
        """
        تخزين قيمة.

        Args:
            key: المفتاح.
            value: القيمة.
            ex: مدة الصلاحية بالثواني (TTL).
        """
        await self.client.set(key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        """حذف مفتاح أو أكثر."""
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """التحقق من وجود مفتاح."""
        return bool(await self.client.exists(key))

    async def expire(self, key: str, seconds: int) -> None:
        """تعيين مدة صلاحية لمفتاح."""
        await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """الوقت المتبقي لمفتاح بالثواني (-1 دائم، -2 غير موجود)."""
        return await self.client.ttl(key)

    # ───────────────────────────────────────────────
    # عمليات العدّاد (للـ Rate Limiting / Flood)
    # ───────────────────────────────────────────────

    async def incr(self, key: str) -> int:
        """زيادة عدّاد بمقدار 1 (يُنشئه بـ 1 إن لم يوجد)."""
        return await self.client.incr(key)

    async def incr_with_expire(self, key: str, ttl: int) -> int:
        """
        زيادة عدّاد مع تعيين مدة الصلاحية في أول مرة فقط.
        نمط شائع لمكافحة الفلود: أول رسالة تبدأ النافذة الزمنية.
        يُنفَّذ كـ Pipeline لضمان الذرية (Atomicity).
        """
        async with self.client.pipeline(transaction=True) as pipe:
            await pipe.incr(key)
            await pipe.expire(key, ttl, nx=True)  # nx: فقط إن لم يكن له TTL
            results = await pipe.execute()
        return results[0]  # القيمة بعد الزيادة

    # ───────────────────────────────────────────────
    # عمليات Hash (للإعدادات المخزنة مؤقتاً)
    # ───────────────────────────────────────────────

    async def hset(self, key: str, mapping: dict) -> None:
        """تخزين حقول متعددة في hash."""
        await self.client.hset(key, mapping=mapping)

    async def hgetall(self, key: str) -> dict:
        """جلب كل حقول hash."""
        return await self.client.hgetall(key)

    async def hget(self, key: str, field: str) -> Optional[str]:
        """جلب حقل واحد من hash."""
        return await self.client.hget(key, field)

    # ───────────────────────────────────────────────
    # عمليات FSM (إدارة الحالات)
    # ───────────────────────────────────────────────

    async def set_state(self, user_id: int, state: str, ttl: int = 600) -> None:
        """تعيين حالة محادثة للمستخدم (مع انتهاء صلاحية افتراضي 10 دقائق)."""
        from config.constants import RedisKeys
        await self.set(RedisKeys.fsm_state(user_id), state, ex=ttl)

    async def get_state(self, user_id: int) -> Optional[str]:
        """جلب حالة المحادثة الحالية للمستخدم."""
        from config.constants import RedisKeys
        return await self.get(RedisKeys.fsm_state(user_id))

    async def clear_state(self, user_id: int) -> None:
        """مسح حالة المحادثة وبياناتها."""
        from config.constants import RedisKeys
        await self.delete(
            RedisKeys.fsm_state(user_id),
            RedisKeys.fsm_data(user_id),
        )


# نسخة Singleton جاهزة للاستيراد
redis_client = RedisClient()
