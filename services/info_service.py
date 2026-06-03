services/info_service.py
═══════════════════════════════════════════════════════════════
خدمة المعلومات: معلومات المستخدم/المجموعة/الرتبة/النشاط.
═══════════════════════════════════════════════════════════════
"""

from datetime import datetime

from pyrogram import Client
from pyrogram.types import Message, User

from database.repositories.user_repo import user_repo
from database.repositories.group_repo import group_repo
from services.rank_service import rank_service
from core.logger import setup_logger

logger = setup_logger("info_service")


class InfoService:
    """خدمة المعلومات."""

    @staticmethod
    def _estimate_account_age(user_id: int) -> str:
        """تقدير عمر الحساب من المعرّف (تقريبي)."""
        # نقاط مرجعية تقريبية لمعرّفات تيليجرام
        if user_id < 100_000_000:
            return "حساب قديم جداً (2013-2015)"
        elif user_id < 1_000_000_000:
            return "حساب قديم (2016-2019)"
        elif user_id < 5_000_000_000:
            return "حساب متوسط (2020-2022)"
        else:
            return "حساب حديث (2023+)"

    async def get_user_info(
        self, client: Client, chat_id: int, user: User,
    ) -> str:
        """بناء نص معلومات المستخدم."""
        db_user = await user_repo.get_user(user.id)
        rank_name = await rank_service.get_user_rank_name(chat_id, user.id)
        account_age = self._estimate_account_age(user.id)

        last_activity = "غير معروف"
        if db_user and db_user.get("last_activity"):
            last_activity = db_user["last_activity"].strftime("%Y-%m-%d %H:%M")

        username = f"@{user.username}" if user.username else "لا يوجد"

        return (
            f"👤 <b>معلومات المستخدم</b>\n\n"
            f"الاسم: {user.first_name or ''} {user.last_name or ''}\n"
            f"المعرّف: <code>{user.id}</code>\n"
            f"اليوزر: {username}\n"
            f"الرتبة: {rank_name}\n"
            f"تقدير الحساب: {account_age}\n"
            f"آخر نشاط: {last_activity}\n"
            f"بوت: {'نعم' if user.is_bot else 'لا'}"
        )

    async def get_group_info(self, client: Client, message: Message) -> str:
        """بناء نص معلومات المجموعة."""
        chat = message.chat
        db_group = await group_repo.get_group(chat.id)

        try:
            members = await client.get_chat_members_count(chat.id)
        except Exception:
            members = db_group.get("members_count", 0) if db_group else 0

        joined = "غير معروف"
        if db_group and db_group.get("joined_at"):
            joined = db_group["joined_at"].strftime("%Y-%m-%d")

        username = f"@{chat.username}" if chat.username else "خاصة"

        return (
            f"💬 <b>معلومات المجموعة</b>\n\n"
            f"الاسم: {chat.title}\n"
            f"المعرّف: <code>{chat.id}</code>\n"
            f"اليوزر: {username}\n"
            f"الأعضاء: {members}\n"
            f"النوع: {chat.type.value}\n"
            f"انضم البوت: {joined}"
        )


info_service = InfoService()
