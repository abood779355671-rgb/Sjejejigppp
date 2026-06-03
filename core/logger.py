core/logger.py
═══════════════════════════════════════════════════════════════
نظام التسجيل (Logging) المركزي.
- يكتب السجلات إلى الكونسول والملفات.
- تدوير الملفات تلقائياً (Rotating) لمنع امتلاء القرص.
- تنسيق واضح مع التوقيت.
═══════════════════════════════════════════════════════════════
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import settings


# مجلد السجلات
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


# تنسيق السجلات
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)-25s | "
    "%(funcName)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "bot") -> logging.Logger:
    """
    إنشاء وتهيئة logger.

    Args:
        name: اسم الـ logger (عادة اسم الموديول).

    Returns:
        كائن logger مهيأ.
    """
    logger = logging.getLogger(name)

    # تجنب إضافة handlers مكررة عند إعادة الاستدعاء
    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # ─── Handler للكونسول ───
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.LOG_LEVEL)
    logger.addHandler(console_handler)

    # ─── Handler لملف السجلات العام (مع تدوير) ───
    # 10 ميجا لكل ملف، يحتفظ بآخر 5 ملفات
    file_handler = RotatingFileHandler(
        filename=LOGS_DIR / "bot.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(settings.LOG_LEVEL)
    logger.addHandler(file_handler)

    # ─── Handler منفصل للأخطاء فقط ───
    error_handler = RotatingFileHandler(
        filename=LOGS_DIR / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    # منع انتشار السجلات للـ root logger (تجنب التكرار)
    logger.propagate = False

    return logger


def configure_third_party_loggers() -> None:
    """
    ضبط مستوى تسجيل المكتبات الخارجية لتقليل الضوضاء.
    Pyrogram مثلاً تُصدر سجلات كثيرة جداً في وضع DEBUG.
    """
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


# logger افتراضي جاهز للاستيراد
log = setup_logger("bot")
