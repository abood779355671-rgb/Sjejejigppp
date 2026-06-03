database/repositories/rank_repo.py
═══════════════════════════════════════════════════════════════
مستودع الرتب: إدارة رتب المستخدمين داخل المجموعات.
يستخدم Cache في Redis لتسريع فحص الرتبة (يُنفَّذ في كل أمر إداري).
═══════════════════════════════════════════════════════════════
"""

from typing import Optional

from database.repositories.base_repo import BaseRepository
from config.constants import RedisKeys, RankLevel
from config.settings import settings
from core.logger import setup_logger

logger = setup_logger("rank_repo")


class RankRepository(BaseRepository):
    """عمليات الرتب."""

    async def set_rank(
        self,
        chat_id: int,
        user_id: int,
        rank_level: int,
        promoted_by: Optional[int] = None,
    ) -> None:
        """
        تعيين رتبة لمستخدم في مجموعة.
        يُحدّث قاعدة البيانات ويُبطل الـ Cache.
        """
        await self.db.execute(
            """
            INSERT INTO user_ranks (chat_id, user_id, rank_level, promoted_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (chat_id, user_id) DO UPDATE SET
                rank_level  = EXCLUDED.rank_level,
                promoted_by = EXCLUDED.promoted_by,
                promoted_at = NOW();
            """,
            chat_id, user_id, rank_level, promoted_by,
        )
        # إبطال الـ Cache لإجبار القراءة من القاعدة في المرة القادمة
        await self.redis.delete(RedisKeys.cache_rank(chat_id, user_id))

    async def remove_rank(self, chat_id: int, user_id: int) -> None:
        """إعادة المستخدم لرتبة عضو (حذف سجل الرتبة)."""
        await self.db.execute(
            "DELETE FROM user_ranks WHERE chat_id = $1 AND user_id = $2;",
            chat_id, user_id,
        )
        await self.redis.delete(RedisKeys.cache_rank(chat_id, user_id))

    async def get_rank(self, chat_id: int, user_id: int) -> int:
        """
        جلب رتبة مستخدم في مجموعة (مع Cache).

        ترتيب الأولوية:
        1. المطور الأساسي (من الإعدادات) → أعلى رتبة دائماً.
        2. المطور (من جدول users) → رتبة مطور.
        3. Cache في Redis.
        4. جدول user_ranks في Postgres.
        5. الافتراضي: عضو (0).
        """
        # 1. المطور الأساسي (تجاوز كل شيء)
        if user_id == settings.MAIN_DEVELOPER_ID:
            return RankLevel.MAIN_DEVELOPER

        # 2. فحص Cache
        cache_key = RedisKeys.cache_rank(chat_id, user_id)
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return int(cached)

        # 3. فحص صفة المطور العامة (من جدول users)
        is_dev = await self.db.fetchval(
            "SELECT is_developer FROM users WHERE user_id = $1;",
            user_id,
        )
        if is_dev:
            # تمييز المطور الأساسي عن الثانوي
            is_main = await self.db.fetchval(
                "SELECT is_main_dev FROM users WHERE user_id = $1;",
                user_id,
            )
            level = RankLevel.MAIN_DEVELOPER if is_main else RankLevel.DEVELOPER
            await self.redis.set(cache_key, str(int(level)), ex=settings.CACHE_TTL_RANKS)
            return level

        # 4. فحص الرتبة في المجموعة
        rank = await self.db.fetchval(
            "SELECT rank_level FROM user_ranks WHERE chat_id = $1 AND user_id = $2;",
            chat_id, user_id,
        )
        level = int(rank) if rank is not None else RankLevel.MEMBER

        # 5. تخزين في Cache
        await self.redis.set(cache_key, str(level), ex=settings.CACHE_TTL_RANKS)
        return level

    async def get_users_by_rank(self, chat_id: int, rank_level: int) -> list[dict]:
        """
        جلب كل المستخدمين برتبة معينة في مجموعة.
        يُستخدم لعرض قوائم (المالكين، المدراء، إلخ).
        """
        rows = await self.db.fetch(
            """
            SELECT ur.user_id, ur.rank_level, ur.promoted_at,
                   u.first_name, u.username
            FROM user_ranks ur
            LEFT JOIN users u ON u.user_id = ur.user_id
            WHERE ur.chat_id = $1 AND ur.rank_level = $2
            ORDER BY ur.promoted_at;
            """,
            chat_id, rank_level,
        )
        return self.records_to_list(rows)

    async def get_all_ranked_users(self, chat_id: int) -> list[dict]:
        """
        جلب كل أصحاب الرتب في مجموعة (أعلى من عضو).
        يُستخدم في "قائمة الإداريين".
        """
        rows = await self.db.fetch(
            """
            SELECT ur.user_id, ur.rank_level, ur.promoted_at,
                   u.first_name, u.username
            FROM user_ranks ur
            LEFT JOIN users u ON u.user_id = ur.user_id
            WHERE ur.chat_id = $1 AND ur.rank_level > 0
            ORDER BY ur.rank_level DESC, ur.promoted_at;
            """,
            chat_id,
        )
        return self.records_to_list(rows)


# نسخة جاهزة
rank_repo = RankRepository()
