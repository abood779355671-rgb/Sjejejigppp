middlewares/ban_check.py
═══════════════════════════════════════════════════════════════
فحص الحظر العام.
يتجاهل البوت أي رسالة من مستخدم محظور عالمياً.
يُقرأ من Redis (Cache) للسرعة القصوى.
═══════════════════════════════════════════════════════════════
"""

from database.repositories.user_repo import user_repo


class BanCheckMiddleware:
    """فحص الحظر العام."""

    @staticmethod
    async def is_blocked(user_id: int) -> bool:
        """
        هل المستخدم محظور عالمياً؟

        Returns:
            True إن كان محظوراً (يجب تجاهله).
        """
        return await user_repo.is_globally_banned(user_id)


ban_check_middleware = BanCheckMiddleware()
