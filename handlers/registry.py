handlers/registry.py
═══════════════════════════════════════════════════════════════
تسجيل كل المعالجات في عميل Pyrogram يدوياً.

ترتيب التسجيل مهم:
1. خط الأنابيب (group=-1) يعمل أولاً على كل رسالة.
2. المعالجات المحددة (group=0).
3. معالج FSM للمطور (group=1) - يلتقط النصوص أثناء الحالات.

نستخدم group لضبط ترتيب التنفيذ في Pyrogram.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message

from middlewares.pipeline import middleware_pipeline
from services.stats_service import stats_service
from handlers.common import start_handler, help_handler
from handlers.developer.panel import (
    open_panel,
    panel_callback,
    handle_dev_input,
)
from core.logger import setup_logger

logger = setup_logger("registry")


# ═══════════════════════════════════════════════════════════════
# خط الأنابيب العام (يعمل على كل رسالة أولاً)
# ═══════════════════════════════════════════════════════════════
async def _pipeline_handler(client: Client, message: Message):
    """
    معالج خط الأنابيب (group=-1).
    يفحص الحظر/الصيانة/الفلود ويسجّل المستخدم.
    إن أعاد False، يوقف المعالجة عبر رفع StopPropagation.
    """
    from pyrogram import StopPropagation

    proceed = await middleware_pipeline.process(message)

    # تحديث عدّاد الرسائل
    await stats_service.increment_message_count()

    if not proceed:
        # إيقاف انتشار الرسالة لباقي المعالجات
        raise StopPropagation


def register_all_handlers(app: Client) -> None:
    """
    تسجيل كل المعالجات في العميل.
    تُستدعى مرة واحدة عند الإقلاع.
    """
    # ─── 1. خط الأنابيب (group=-1، يعمل أولاً) ───
    app.add_handler(
        MessageHandler(_pipeline_handler),
        group=-1,
    )

    # ─── 2. الأوامر العامة (group=0) ───
    app.add_handler(
        MessageHandler(start_handler, filters.command("start")),
        group=0,
    )
    app.add_handler(
        MessageHandler(help_handler, filters.command("help")),
        group=0,
    )

    # ─── 3. لوحة المطور ───
    app.add_handler(
        MessageHandler(open_panel, filters.command(["dev", "panel", "تطوير"])),
        group=0,
    )
    app.add_handler(
        CallbackQueryHandler(panel_callback, filters.regex(r"^dev:")),
        group=0,
    )

    # ─── 4. معالج FSM للمطور (group=1، نصوص خاصة) ───
    app.add_handler(
        MessageHandler(
            handle_dev_input,
            filters.private & filters.text & ~filters.command(["start", "help", "dev", "panel"]),
        ),
        group=1,
    )

    logger.info("✅ تم تسجيل جميع المعالجات")
