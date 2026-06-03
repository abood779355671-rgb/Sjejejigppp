core/database.py
═══════════════════════════════════════════════════════════════
إدارة اتصال PostgreSQL باستخدام asyncpg مع Connection Pool.

لماذا Connection Pool؟
- إنشاء اتصال جديد لكل استعلام مكلف جداً (بطيء).
- الـ Pool يحتفظ بمجموعة اتصالات جاهزة لإعادة الاستخدام.
- يدعم آلاف الطلبات المتزامنة بكفاءة.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional, Any

import asyncpg

from config.settings import settings
from core.logger import setup_logger
from core.exceptions import DatabaseConnectionError, DatabaseException

logger = setup_logger("database")


class Database:
    """
    مدير اتصال قاعدة البيانات (Singleton).
    يوفر واجهة آمنة لتنفيذ الاستعلامات عبر Pool.
    """

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

    # ───────────────────────────────────────────────
    # الاتصال والإغلاق
    # ───────────────────────────────────────────────

    async def connect(self) -> None:
        """
        إنشاء Connection Pool.
        يُستدعى مرة واحدة عند إقلاع البوت.
        """
        if self._pool is not None:
            logger.warning("الاتصال بقاعدة البيانات موجود مسبقاً")
            return

        try:
            self._pool = await asyncpg.create_pool(
                dsn=settings.postgres_dsn,
                min_size=5,          # حد أدنى من الاتصالات الجاهزة
                max_size=20,         # حد أقصى (يُضبط حسب السيرفر)
                max_inactive_connection_lifetime=300,  # إغلاق الخامل بعد 5 دقائق
                command_timeout=60,  # مهلة تنفيذ الاستعلام
            )
            logger.info("✅ تم الاتصال بقاعدة بيانات PostgreSQL بنجاح")
        except Exception as e:
            logger.critical(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
            raise DatabaseConnectionError(f"فشل الاتصال بقاعدة البيانات: {e}")

    async def disconnect(self) -> None:
        """إغلاق Connection Pool بأمان عند إيقاف البوت."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("تم إغلاق الاتصال بقاعدة البيانات")

    @property
    def pool(self) -> asyncpg.Pool:
        """الحصول على الـ Pool مع التأكد من وجوده."""
        if self._pool is None:
            raise DatabaseConnectionError("قاعدة البيانات غير متصلة. استدعِ connect() أولاً")
        return self._pool

    # ───────────────────────────────────────────────
    # تنفيذ الاستعلامات (آمنة ضد SQL Injection)
    # كل الاستعلامات تستخدم Parameterized Queries ($1, $2)
    # ───────────────────────────────────────────────

    async def execute(self, query: str, *args: Any) -> str:
        """
        تنفيذ استعلام دون إرجاع نتائج (INSERT/UPDATE/DELETE).

        Args:
            query: استعلام SQL مع placeholders ($1, $2, ...).
            *args: القيم التي تُمرّر بأمان.

        Returns:
            حالة التنفيذ (مثل "INSERT 0 1").
        """
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"خطأ في execute: {e} | Query: {query[:100]}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {e}")

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """
        جلب عدة صفوف.

        Returns:
            قائمة من السجلات (Records).
        """
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error(f"خطأ في fetch: {e} | Query: {query[:100]}")
            raise DatabaseException(f"خطأ في جلب البيانات: {e}")

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        """
        جلب صف واحد فقط.

        Returns:
            سجل واحد أو None.
        """
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error(f"خطأ في fetchrow: {e} | Query: {query[:100]}")
            raise DatabaseException(f"خطأ في جلب البيانات: {e}")

    async def fetchval(self, query: str, *args: Any) -> Any:
        """
        جلب قيمة واحدة (خلية واحدة).
        مفيد لـ COUNT، EXISTS، إلخ.

        Returns:
            قيمة مفردة.
        """
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"خطأ في fetchval: {e} | Query: {query[:100]}")
            raise DatabaseException(f"خطأ في جلب القيمة: {e}")

    async def executemany(self, query: str, args_list: list) -> None:
        """
        تنفيذ نفس الاستعلام لعدة مجموعات من القيم (دفعة واحدة).
        مفيد جداً للإدراج الجماعي (Bulk Insert).
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.executemany(query, args_list)
        except Exception as e:
            logger.error(f"خطأ في executemany: {e}")
            raise DatabaseException(f"خطأ في التنفيذ الجماعي: {e}")

    def transaction(self):
        """
        الحصول على سياق Transaction.
        الاستخدام:
            async with db.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(...)
                    await conn.execute(...)
        يضمن تنفيذ كل العمليات معاً أو لا شيء (Atomicity).
        """
        return self.pool.acquire()


# نسخة Singleton جاهزة للاستيراد
db = Database()
