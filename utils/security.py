utils/security.py
═══════════════════════════════════════════════════════════════
أدوات أمنية إضافية:
- Rate Limiting متقدم.
- كشف أنماط الـ SQL Injection في المدخلات (طبقة دفاع ثانية).
- تنظيف HTML لمنع الحقن.
═══════════════════════════════════════════════════════════════
"""

import re
import html

from core.logger import setup_logger

logger = setup_logger("security")


# أنماط مشبوهة بحقن SQL (طبقة دفاع إضافية فوق Parameterized Queries)
_SQL_INJECTION_PATTERNS = [
    re.compile(r"(\bUNION\b.*\bSELECT\b)", re.IGNORECASE),
    re.compile(r"(\bDROP\b.*\bTABLE\b)", re.IGNORECASE),
    re.compile(r"(;.*--)", re.IGNORECASE),
    re.compile(r"(\bOR\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
]


class Security:
    """أدوات الأمان."""

    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """
        كشف محاولات SQL Injection المحتملة.
        ملاحظة: الحماية الأساسية من Parameterized Queries،
        هذه طبقة كشف إضافية للتسجيل والمراقبة.
        """
        for pattern in _SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning(f"نمط SQL مشبوه مكتشف: {text[:100]}")
                return True
        return False

    @staticmethod
    def escape_html(text: str) -> str:
        """تنظيف HTML لمنع الحقن في رسائل البوت."""
        return html.escape(text)

    @staticmethod
    def sanitize_for_display(text: str, max_length: int = 4096) -> str:
        """تنظيف نص للعرض الآمن."""
        text = html.escape(text.strip())
        if len(text) > max_length:
            text = text[:max_length] + "..."
        return text

    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """فحص أمان اسم ملف (منع path traversal)."""
        return not (".." in filename or "/" in filename or "\\" in filename)


security = Security()
