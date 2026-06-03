database/repositories/welcome_repo.py
═══════════════════════════════════════════════════════════════
مستودع إعدادات الترحيب والمغادرة لكل مجموعة.
═══════════════════════════════════════════════════════════════
"""

import json
from typing import Optional

from database.repositories.base_repo import BaseRepository
from config.constants import RedisKeys
from config.settings import settings
from core.logger import setup_logger

logger = setup_logger("welcome_repo")


class WelcomeRepository(BaseRepository):
    """عمليات الترحيب."""

    async def ensure_settings(self, chat_id: int) -> None:
        """ضمان وجود صف إعدادات ترحيب."""
        await self.db.execute(
            """
            INSERT INTO welcome_settings (chat_id)
            VALUES ($1)
            ON CONFLICT (chat_id) DO NOTHING;
            """,
            chat_id,
        )

    async def get_settings(self, chat_id: int) -> dict:
        """جلب إعدادات الترحيب (مع Cache)."""
        cache_key = RedisKeys.cache_welcome(chat_id)
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        await self.ensure_settings(chat_id)
        record = await self.db.fetchrow(
            "SELECT * FROM welcome_settings WHERE chat_id = $1;",
            chat_id,
        )
        data = self.record_to_dict(record) or {}

        # تحويل buttons من JSON إذا كانت نصاً
        if isinstance(data.get("buttons"), str):
            try:
                data["buttons"] = json.loads(data["buttons"])
            except (json.JSONDecodeError, TypeError):
                data["buttons"] = []

        # تخزين في Cache (نحوّل datetime لنص قابل للتسلسل)
        cacheable = {
            k: (v.isoformat() if hasattr(v, "isoformat") else v)
            for k, v in data.items()
        }
        await self.redis.set(
            cache_key, json.dumps(cacheable, ensure_ascii=False, default=str),
            ex=settings.CACHE_TTL_SETTINGS,
        )
        return data

    async def set_welcome_text(self, chat_id: int, text: str) -> None:
        """تعيين نص الترحيب."""
        await self.ensure_settings(chat_id)
        await self.db.execute(
            """
            UPDATE welcome_settings
            SET welcome_text = $2, is_enabled = TRUE, updated_at = NOW()
            WHERE chat_id = $1;
            """,
            chat_id, text,
        )
        await self.redis.delete(RedisKeys.cache_welcome(chat_id))

    async def set_welcome_media(
        self, chat_id: int, media_type: str, file_id: str,
    ) -> None:
        """تعيين وسائط الترحيب (صورة/فيديو)."""
        await self.ensure_settings(chat_id)
        await self.db.execute(
            """
            UPDATE welcome_settings
            SET media_type = $2, media_file_id = $3, updated_at = NOW()
            WHERE chat_id = $1;
            """,
            chat_id, media_type, file_id,
        )
        await self.redis.delete(RedisKeys.cache_welcome(chat_id))

    async def set_rules(self, chat_id: int, rules: str) -> None:
        """تعيين قوانين المجموعة."""
        await self.ensure_settings(chat_id)
        await self.db.execute(
            "UPDATE welcome_settings SET rules_text = $2 WHERE chat_id = $1;",
            chat_id, rules,
        )
        await self.redis.delete(RedisKeys.cache_welcome(chat_id))

    async def set_goodbye(self, chat_id: int, text: str, enabled: bool = True) -> None:
        """تعيين رسالة المغادرة."""
        await self.ensure_settings(chat_id)
        await self.db.execute(
            """
            UPDATE welcome_settings
            SET goodbye_text = $2, goodbye_enabled = $3 WHERE chat_id = $1;
            """,
            chat_id, text, enabled,
        )
        await self.redis.delete(RedisKeys.cache_welcome(chat_id))

    async def set_buttons(self, chat_id: int, buttons: list) -> None:
        """تعيين أزرار الترحيب الانلاين."""
        await self.ensure_settings(chat_id)
        await self.db.execute(
            "UPDATE welcome_settings SET buttons = $2 WHERE chat_id = $1;",
            chat_id, json.dumps(buttons, ensure_ascii=False),
        )
        await self.redis.delete(RedisKeys.cache_welcome(chat_id))

    async def toggle_welcome(self, chat_id: int, enabled: bool) -> None:
        """تفعيل/تعطيل الترحيب."""
        await self.ensure_settings(chat_id)
        await self.db.execute(
            "UPDATE welcome_settings SET is_enabled = $2 WHERE chat_id = $1;",
            chat_id, enabled,
        )
        await self.redis.delete(RedisKeys.cache_welcome(chat_id))


welcome_repo = WelcomeRepository()
