database/repositories/protection_repo.py
═══════════════════════════════════════════════════════════════
مستودع إعدادات الحماية لكل مجموعة.
يستخدم Cache في Redis (Cache-Aside) لأن إعدادات الحماية
تُقرأ في كل رسالة — يجب أن تكون فائقة السرعة.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional

from database.repositories.base_repo import BaseRepository
from config.constants import RedisKeys
from config.settings import settings
from config.constants import Limits
from core.logger import setup_logger

logger = setup_logger("protection_repo")


# قائمة أعمدة الحماية المنطقية (للتحقق والتحديث الآمن)
_PROTECTION_FIELDS = {
    "anti_links", "anti_username", "anti_forward", "anti_photo",
    "anti_video", "anti_files", "anti_audio", "anti_stickers",
    "anti_gif", "anti_bots", "anti_spam", "anti_flood",
    "anti_new_accounts", "anti_invite_links",
}


class ProtectionRepository(BaseRepository):
    """عمليات إعدادات الحماية."""

    async def ensure_settings(self, chat_id: int) -> None:
        """ضمان وجود صف إعدادات للمجموعة (إنشاؤه بالقيم الافتراضية)."""
        await self.db.execute(
            """
            INSERT INTO protection_settings (chat_id)
            VALUES ($1)
            ON CONFLICT (chat_id) DO NOTHING;
            """,
            chat_id,
        )

    async def get_settings(self, chat_id: int) -> dict:
        """
        جلب إعدادات الحماية (مع Cache).

        نمط Cache-Aside:
        1. ابحث في Redis.
        2. إن لم توجد، اقرأ من Postgres وخزّن.
        """
        cache_key = RedisKeys.cache_protection(chat_id)

        # 1. فحص Cache
        cached = await self.redis.hgetall(cache_key)
        if cached:
            return self._deserialize(cached)

        # 2. قراءة من Postgres
        await self.ensure_settings(chat_id)
        record = await self.db.fetchrow(
            "SELECT * FROM protection_settings WHERE chat_id = $1;",
            chat_id,
        )
        data = self.record_to_dict(record) or {}

        # 3. تخزين في Cache (تحويل القيم إلى نصوص)
        if data:
            serialized = {k: str(v) for k, v in data.items() if v is not None}
            await self.redis.hset(cache_key, serialized)
            await self.redis.expire(cache_key, settings.CACHE_TTL_SETTINGS)

        return data

    async def toggle_protection(self, chat_id: int, field: str, value: bool) -> None:
        """
        تفعيل/تعطيل نوع حماية.
        يتحقق من اسم الحقل لمنع SQL Injection عبر اسم العمود.
        """
        if field not in _PROTECTION_FIELDS:
            logger.warning(f"محاولة تعديل حقل حماية غير صالح: {field}")
            return

        await self.ensure_settings(chat_id)
        # اسم العمود مُتحقَّق منه ضد القائمة البيضاء، والقيمة parameterized
        await self.db.execute(
            f"""
            UPDATE protection_settings
            SET {field} = $2, updated_at = NOW()
            WHERE chat_id = $1;
            """,
            chat_id, value,
        )
        # إبطال الـ Cache
        await self.redis.delete(RedisKeys.cache_protection(chat_id))

    async def update_punishment(self, chat_id: int, punishment: str) -> None:
        """تحديث نوع العقوبة الافتراضية."""
        await self.ensure_settings(chat_id)
        await self.db.execute(
            """
            UPDATE protection_settings
            SET punishment = $2, updated_at = NOW()
            WHERE chat_id = $1;
            """,
            chat_id, punishment,
        )
        await self.redis.delete(RedisKeys.cache_protection(chat_id))

    async def update_numeric(self, chat_id: int, field: str, value: int) -> None:
        """تحديث إعداد رقمي (flood_limit/max_warns/...)."""
        allowed = {"flood_limit", "flood_seconds", "max_warns", "new_account_days"}
        if field not in allowed:
            return
        await self.ensure_settings(chat_id)
        await self.db.execute(
            f"""
            UPDATE protection_settings
            SET {field} = $2, updated_at = NOW()
            WHERE chat_id = $1;
            """,
            chat_id, value,
        )
        await self.redis.delete(RedisKeys.cache_protection(chat_id))

    @staticmethod
    def _deserialize(cached: dict) -> dict:
        """تحويل قيم Redis النصية إلى أنواعها الصحيحة."""
        result = {}
        bool_fields = _PROTECTION_FIELDS
        int_fields = {"chat_id", "flood_limit", "flood_seconds", "max_warns", "new_account_days"}

        for key, value in cached.items():
            if key in bool_fields:
                result[key] = value.lower() == "true"
            elif key in int_fields:
                try:
                    result[key] = int(value)
                except ValueError:
                    result[key] = 0
            else:
                result[key] = value
        return result


# نسخة جاهزة
protection_repo = ProtectionRepository()
