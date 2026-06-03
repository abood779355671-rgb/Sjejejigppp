config/settings.py
═══════════════════════════════════════════════════════════════
نظام إدارة الإعدادات المركزي باستخدام Pydantic Settings.
يقوم بتحميل المتغيرات من ملف .env مع فحص الأنواع والتحقق منها.
═══════════════════════════════════════════════════════════════
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    فئة الإعدادات الرئيسية.
    كل متغير هنا يُقرأ تلقائياً من ملف .env أو من متغيرات البيئة.
    Pydantic يتحقق من الأنواع ويرفع خطأ واضح عند وجود قيمة خاطئة.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # تجاهل المتغيرات غير المعرّفة بدلاً من رفع خطأ
    )

    # ═══ Telegram API ═══
    API_ID: int = Field(..., description="معرف API من my.telegram.org")
    API_HASH: str = Field(..., description="هاش API")
    BOT_TOKEN: str = Field(..., description="توكن البوت من BotFather")

    # ═══ Bot Identity ═══
    BOT_USERNAME: str = Field(default="", description="معرف البوت بدون @")
    BOT_NAME: str = Field(default="البوت العربي", description="اسم البوت")

    # ═══ Main Developer ═══
    MAIN_DEVELOPER_ID: int = Field(..., description="معرف المطور الأساسي")

    # ═══ PostgreSQL ═══
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)

    # ═══ Redis ═══
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    # ═══ Application ═══
    TIMEZONE: str = Field(default="Asia/Riyadh")
    LOG_LEVEL: str = Field(default="INFO")
    WORKERS: int = Field(default=8)

    # ═══ Rate Limiting ═══
    RATE_LIMIT_MESSAGES: int = Field(default=20)
    RATE_LIMIT_SECONDS: int = Field(default=10)

    # ═══ Cache TTL ═══
    CACHE_TTL_SETTINGS: int = Field(default=300)
    CACHE_TTL_RANKS: int = Field(default=600)

    # ═══ Backup ═══
    BACKUP_CHANNEL_ID: Optional[int] = Field(default=None)

    # ───────────────────────────────────────────────
    # خصائص محسوبة (Computed Properties)
    # ───────────────────────────────────────────────

    @property
    def postgres_dsn(self) -> str:
        """
        رابط اتصال PostgreSQL لـ asyncpg.
        مثال: postgresql://user:pass@host:port/db
        """
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def postgres_sqlalchemy_dsn(self) -> str:
        """
        رابط اتصال PostgreSQL لـ SQLAlchemy + asyncpg (يُستخدم في Alembic والـ ORM).
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        """
        رابط اتصال Redis.
        إن وُجدت كلمة مرور تُضاف للرابط.
        """
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ───────────────────────────────────────────────
    # المُحقّقات (Validators)
    # ───────────────────────────────────────────────

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """التأكد من أن مستوى التسجيل صالح."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL يجب أن يكون أحد: {allowed}")
        return v_upper


@lru_cache()
def get_settings() -> Settings:
    """
    دالة الحصول على الإعدادات (Singleton عبر lru_cache).
    تُحمَّل الإعدادات مرة واحدة فقط وتُخزَّن في الذاكرة.
    هذا يمنع إعادة قراءة ملف .env في كل استدعاء.
    """
    return Settings()


# نسخة جاهزة للاستيراد المباشر في باقي المشروع
settings = get_settings()
