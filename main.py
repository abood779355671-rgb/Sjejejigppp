main.py
═══════════════════════════════════════════════════════════════
نقطة تشغيل البوت الرئيسية.

دورة الحياة:
1. تهيئة uvloop (أداء أعلى).
2. الاتصال بـ PostgreSQL و Redis.
3. تشغيل الترحيلات.
4. ضمان المطور الأساسي.
5. تشغيل المُجدول والمهام الدورية.
6. تسجيل المعالجات.
7. تشغيل البوت.
8. إيقاف نظيف عند الإغلاق.
═══════════════════════════════════════════════════════════════
"""

import asyncio
import sys

# تفعيل uvloop على الأنظمة المدعومة (أداء أعلى)
try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

from core.client import bot
from core.database import db
from core.redis_client import redis_client
from core.scheduler import scheduler
from core.logger import setup_logger, configure_third_party_loggers
from config.settings import settings
from database.migrations.runner import run_migrations
from database.repositories.user_repo import user_repo
from services.stats_service import stats_service
from database.repositories.log_repo import log_repo
from handlers.registry import register_all_handlers

logger = setup_logger("main")


# ═══════════════════════════════════════════════════════════════
# المهام الدورية
# ═══════════════════════════════════════════════════════════════
def setup_scheduled_jobs() -> None:
    """إعداد المهام المجدولة."""
    # حفظ الإحصائيات كل 10 دقائق
    scheduler.add_interval_job(
        stats_service.persist_daily_stats,
        seconds=600,
        job_id="persist_stats",
    )
    # تنظيف السجلات القديمة كل 24 ساعة
    scheduler.add_interval_job(
        lambda: asyncio.create_task(log_repo.clear_old_logs(days=30)),
        seconds=86400,
        job_id="clean_logs",
    )


# ═══════════════════════════════════════════════════════════════
# الإقلاع
# ═══════════════════════════════════════════════════════════════
async def startup() -> None:
    """تهيئة كل المكوّنات قبل تشغيل البوت."""
    logger.info("═══════════════════════════════════")
    logger.info("🚀 بدء إقلاع البوت...")

    configure_third_party_loggers()

    # 1. قواعد البيانات
    await db.connect()
    await redis_client.connect()

    # 2. الترحيلات
    await run_migrations()

    # 3. ضمان المطور الأساسي
    await user_repo.set_main_developer(settings.MAIN_DEVELOPER_ID)
    logger.info(f"✅ المطور الأساسي: {settings.MAIN_DEVELOPER_ID}")

    # 4. المُجدول
    setup_scheduled_jobs()
    scheduler.start()

    # 5. المعالجات
    register_all_handlers(bot)

    logger.info("✅ اكتمل الإقلاع")
    logger.info("═══════════════════════════════════")


# ═══════════════════════════════════════════════════════════════
# الإيقاف
# ═══════════════════════════════════════════════════════════════
async def shutdown() -> None:
    """إيقاف نظيف لكل المكوّنات."""
    logger.info("جارٍ الإيقاف النظيف...")
    scheduler.shutdown()
    await redis_client.disconnect()
    await db.disconnect()
    logger.info("✅ تم الإيقاف النظيف")


# ═══════════════════════════════════════════════════════════════
# الدالة الرئيسية
# ═══════════════════════════════════════════════════════════════
async def main() -> None:
    """الدالة الرئيسية."""
    await startup()

    try:
        await bot.start()
        logger.info("🟢 البوت يعمل الآن...")
        # إبقاء البوت يعمل حتى الإيقاف
        from pyrogram import idle
        await idle()
    finally:
        await bot.stop()
        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم الإيقاف بواسطة المستخدم (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"❌ خطأ فادح: {e}", exc_info=True)
        sys.exit(1)
