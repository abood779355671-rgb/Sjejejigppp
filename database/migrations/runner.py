"""
database/migrations/runner.py
═══════════════════════════════════════════════════════════════
مُشغّل الترحيلات.
- ينشئ جدول schema_migrations لتتبع المُطبَّق.
- يقرأ ملفات .sql المرقّمة بالترتيب.
- يطبّق غير المُطبَّق منها داخل Transaction.
═══════════════════════════════════════════════════════════════
"""

from pathlib import Path

from core.database import db
from core.logger import setup_logger

logger = setup_logger("migrations")

# مجلد ملفات الترحيل
MIGRATIONS_DIR = Path(__file__).parent / "sql"


async def _ensure_migrations_table() -> None:
    """إنشاء جدول تتبع الترحيلات إن لم يكن موجوداً."""
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     VARCHAR(255) PRIMARY KEY,
            applied_at  TIMESTAMP DEFAULT NOW()
        );
        """
    )


async def _get_applied_migrations() -> set[str]:
    """جلب أسماء الترحيلات المُطبَّقة مسبقاً."""
    rows = await db.fetch("SELECT version FROM schema_migrations;")
    return {row["version"] for row in rows}


async def run_migrations() -> None:
    """
    تشغيل كل الترحيلات غير المُطبَّقة بالترتيب.
    يُستدعى عند إقلاع البوت.
    """
    await _ensure_migrations_table()
    applied = await _get_applied_migrations()

    if not MIGRATIONS_DIR.exists():
        logger.warning(f"مجلد الترحيلات غير موجود: {MIGRATIONS_DIR}")
        return

    # ترتيب الملفات أبجدياً (مرقّمة: 001_, 002_, ...)
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not sql_files:
        logger.warning("لا توجد ملفات ترحيل")
        return

    applied_count = 0
    for sql_file in sql_files:
        version = sql_file.stem  # اسم الملف دون الامتداد

        if version in applied:
            continue  # مُطبَّق مسبقاً

        sql_content = sql_file.read_text(encoding="utf-8")

        # تطبيق الترحيل داخل Transaction (الكل أو لا شيء)
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(sql_content)
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1);",
                    version,
                )

        logger.info(f"✅ تم تطبيق الترحيل: {version}")
        applied_count += 1

    if applied_count == 0:
        logger.info("قاعدة البيانات محدّثة، لا توجد ترحيلات جديدة")
    else:
        logger.info(f"تم تطبيق {applied_count} ترحيل بنجاح")
