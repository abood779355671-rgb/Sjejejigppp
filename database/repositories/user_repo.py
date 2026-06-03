database/repositories/user_repo.py
═══════════════════════════════════════════════════════════════
مستودع المستخدمين: كل عمليات قاعدة البيانات المتعلقة بالمستخدمين.
يتضمن Cache للحظر العام عبر Redis للفحص فائق السرعة.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional
from datetime import datetime

from database.repositories.base_repo import BaseRepository
from config.constants import RedisKeys
from core.logger import setup_logger

logger = setup_logger("user_repo")


class UserRepository(BaseRepository):
    """عمليات المستخدمين."""

    # ───────────────────────────────────────────────
    # إنشاء / تحديث (Upsert)
    # ───────────────────────────────────────────────

    async def upsert_user(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: str = "ar",
        is_bot: bool = False,
        account_created: Optional[datetime] = None,
    ) -> None:
        """
        إدراج مستخدم جديد أو تحديث بياناته إن كان موجوداً.
        يُستدعى في كل رسالة (عبر middleware) لإبقاء البيانات محدّثة.

        ملاحظة: نحدّث last_activity دائماً، لكن لا نلمس
        الحقول الحساسة (is_developer, is_globally_banned).
        """
        await self.db.execute(
            """
            INSERT INTO users (
                user_id, first_name, last_name, username,
                language_code, is_bot, account_created, last_activity
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                first_name    = EXCLUDED.first_name,
                last_name     = EXCLUDED.last_name,
                username      = EXCLUDED.username,
                last_activity = NOW();
            """,
            user_id, first_name, last_name, username,
            language_code, is_bot, account_created,
        )

    # ───────────────────────────────────────────────
    # جلب
    # ───────────────────────────────────────────────

    async def get_user(self, user_id: int) -> Optional[dict]:
        """جلب مستخدم بمعرّفه."""
        record = await self.db.fetchrow(
            "SELECT * FROM users WHERE user_id = $1;",
            user_id,
        )
        return self.record_to_dict(record)

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """جلب مستخدم باليوزر (بدون @)."""
        username = username.lstrip("@").lower()
        record = await self.db.fetchrow(
            "SELECT * FROM users WHERE LOWER(username) = $1;",
            username,
        )
        return self.record_to_dict(record)

    async def get_total_users(self) -> int:
        """العدد الكلي للمستخدمين (للإحصائيات)."""
        return await self.db.fetchval("SELECT COUNT(*) FROM users;") or 0

    async def get_all_user_ids(self) -> list[int]:
        """
        جلب كل معرّفات المستخدمين (للإذاعة).
        يستثني المحظورين عالمياً والبوتات.
        """
        rows = await self.db.fetch(
            """
            SELECT user_id FROM users
            WHERE is_globally_banned = FALSE AND is_bot = FALSE;
            """
        )
        return [row["user_id"] for row in rows]

    # ───────────────────────────────────────────────
    # نظام المطور
    # ───────────────────────────────────────────────

    async def set_developer(self, user_id: int, is_dev: bool) -> None:
        """تعيين أو إزالة صفة المطور."""
        await self.db.execute(
            "UPDATE users SET is_developer = $2 WHERE user_id = $1;",
            user_id, is_dev,
        )

    async def set_main_developer(self, user_id: int) -> None:
        """
        تعيين المطور الأساسي.
        يُستدعى عند الإقلاع لضمان أن MAIN_DEVELOPER_ID مطوّر أساسي.
        """
        await self.db.execute(
            """
            INSERT INTO users (user_id, is_developer, is_main_dev)
            VALUES ($1, TRUE, TRUE)
            ON CONFLICT (user_id) DO UPDATE SET
                is_developer = TRUE,
                is_main_dev  = TRUE;
            """,
            user_id,
        )

    async def is_developer(self, user_id: int) -> bool:
        """هل المستخدم مطوّر (أساسي أو ثانوي)؟"""
        result = await self.db.fetchval(
            "SELECT is_developer FROM users WHERE user_id = $1;",
            user_id,
        )
        return bool(result)

    async def is_main_developer(self, user_id: int) -> bool:
        """هل المستخدم المطوّر الأساسي؟"""
        result = await self.db.fetchval(
            "SELECT is_main_dev FROM users WHERE user_id = $1;",
            user_id,
        )
        return bool(result)

    async def get_all_developers(self) -> list[dict]:
        """قائمة كل المطورين."""
        rows = await self.db.fetch(
            """
            SELECT user_id, first_name, username, is_main_dev
            FROM users WHERE is_developer = TRUE
            ORDER BY is_main_dev DESC;
            """
        )
        return self.records_to_list(rows)

    # ───────────────────────────────────────────────
    # الحظر العام (مع Cache في Redis)
    # ───────────────────────────────────────────────

    async def set_global_ban(
        self,
        user_id: int,
        banned: bool,
        reason: Optional[str] = None,
    ) -> None:
        """
        تطبيق أو إزالة الحظر العام.
        يُحدّث قاعدة البيانات و Redis معاً.
        """
        await self.db.execute(
            """
            UPDATE users
            SET is_globally_banned = $2, global_ban_reason = $3
            WHERE user_id = $1;
            """,
            user_id, banned, reason,
        )

        # تحديث Cache في Redis
        key = RedisKeys.global_ban(user_id)
        if banned:
            await self.redis.set(key, "1")
        else:
            await self.redis.delete(key)

    async def is_globally_banned(self, user_id: int) -> bool:
        """
        فحص الحظر العام (يقرأ من Redis أولاً للسرعة).
        نمط Cache-Aside:
        1. ابحث في Redis.
        2. إن لم يوجد، اقرأ من Postgres وخزّن النتيجة.
        """
        key = RedisKeys.global_ban(user_id)

        # 1. فحص Redis
        cached = await self.redis.get(key)
        if cached is not None:
            return cached == "1"

        # 2. فحص Postgres
        result = await self.db.fetchval(
            "SELECT is_globally_banned FROM users WHERE user_id = $1;",
            user_id,
        )
        banned = bool(result)

        # 3. تخزين النتيجة (المحظور فقط، مع TTL للمحظور)
        if banned:
            await self.redis.set(key, "1", ex=3600)

        return banned

    # ───────────────────────────────────────────────
    # النشاط
    # ───────────────────────────────────────────────

    async def update_last_activity(self, user_id: int) -> None:
        """تحديث آخر نشاط للمستخدم."""
        await self.db.execute(
            "UPDATE users SET last_activity = NOW() WHERE user_id = $1;",
            user_id,
        )


# نسخة جاهزة
user_repo = UserRepository()
