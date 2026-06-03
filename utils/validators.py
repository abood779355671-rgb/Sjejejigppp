utils/validators.py
═══════════════════════════════════════════════════════════════
التحقق من صحة وتنظيف المدخلات.

ملاحظة أمنية: الحماية الأساسية من SQL Injection تأتي من
Parameterized Queries في طبقة قاعدة البيانات. هذه الطبقة
إضافية للتحقق المنطقي وتنظيف المدخلات قبل الاستخدام.
═══════════════════════════════════════════════════════════════
"""

import re
from typing import Optional

from core.exceptions import ValidationError


# نمط معرّف تيليجرام الرقمي
USER_ID_PATTERN = re.compile(r"^-?\d{5,15}$")
# نمط اليوزر
USERNAME_PATTERN = re.compile(r"^@?[a-zA-Z][a-zA-Z0-9_]{4,31}$")


class Validators:
    """دوال التحقق من المدخلات."""

    @staticmethod
    def validate_user_id(value: str) -> int:
        """
        التحقق من معرّف مستخدم رقمي وتحويله إلى int.

        Raises:
            ValidationError: إن كان غير صالح.
        """
        value = value.strip()
        if not USER_ID_PATTERN.match(value):
            raise ValidationError("معرّف المستخدم غير صالح")
        return int(value)

    @staticmethod
    def validate_username(value: str) -> str:
        """
        التحقق من يوزر تيليجرام وإرجاعه بدون @.

        Raises:
            ValidationError: إن كان غير صالح.
        """
        value = value.strip()
        if not USERNAME_PATTERN.match(value):
            raise ValidationError("اليوزر غير صالح")
        return value.lstrip("@").lower()

    @staticmethod
    def sanitize_text(text: str, max_length: int = 4096) -> str:
        """
        تنظيف النص: إزالة المسافات الزائدة والاقتصاص للحد الأقصى.

        Args:
            text: النص المُدخل.
            max_length: الحد الأقصى للطول.
        """
        text = text.strip()
        if len(text) > max_length:
            text = text[:max_length]
        return text

    @staticmethod
    def validate_regex(pattern: str) -> str:
        """
        التحقق من صحة تعبير Regex (يُستخدم في الردود).
        يمنع تخزين أنماط فاسدة تُعطّل البوت لاحقاً.

        Raises:
            ValidationError: إن كان النمط غير صالح.
        """
        try:
            re.compile(pattern)
            return pattern
        except re.error:
            raise ValidationError("تعبير Regex غير صالح")

    @staticmethod
    def validate_duration(text: str) -> Optional[int]:
        """
        تحويل مدة نصية إلى ثوانٍ.
        أمثلة: 30s, 5m, 2h, 1d.

        Returns:
            عدد الثواني أو None إن كان غير صالح.
        """
        text = text.strip().lower()
        match = re.match(r"^(\d+)([smhd])$", text)
        if not match:
            return None

        amount = int(match.group(1))
        unit = match.group(2)
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return amount * multipliers[unit]


validators = Validators()
