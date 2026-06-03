core/scheduler.py
═══════════════════════════════════════════════════════════════
مُجدول المهام الدورية باستخدام APScheduler.
يُستخدم لـ:
- حفظ الإحصائيات اللحظية في قاعدة البيانات.
- إنهاء العقوبات المؤقتة (كتم/حظر مؤقت).
- تنظيف السجلات القديمة.
- النسخ الاحتياطي التلقائي.
═══════════════════════════════════════════════════════════════
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from core.logger import setup_logger

logger = setup_logger("scheduler")


class BotScheduler:
    """مدير المهام المجدولة."""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

    def start(self) -> None:
        """بدء المُجدول."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("✅ تم تشغيل المُجدول")

    def shutdown(self) -> None:
        """إيقاف المُجدول بأمان."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("تم إيقاف المُجدول")

    def add_interval_job(
        self,
        func,
        seconds: int,
        job_id: str,
        **kwargs,
    ) -> None:
        """
        إضافة مهمة تتكرر كل عدد ثوانٍ.

        Args:
            func: الدالة (async).
            seconds: الفاصل الزمني.
            job_id: معرّف فريد (يمنع التكرار).
        """
        self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            replace_existing=True,
            **kwargs,
        )
        logger.info(f"تمت إضافة مهمة دورية: {job_id} (كل {seconds}ث)")

    @property
    def scheduler(self) -> AsyncIOScheduler:
        return self._scheduler


# نسخة Singleton جاهزة
scheduler = BotScheduler()
