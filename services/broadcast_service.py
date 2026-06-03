services/broadcast_service.py
═══════════════════════════════════════════════════════════════
خدمة الإذاعة (Broadcast).
ترسل رسالة لكل المستخدمين أو المجموعات على دفعات لتجنب FloodWait.
تستخدم قفلاً في Redis لمنع تشغيل إذاعتين معاً.
═══════════════════════════════════════════════════════════════
"""

import asyncio
from typing import Literal

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError

from database.repositories.user_repo import user_repo
from database.repositories.group_repo import group_repo
from config.constants import RedisKeys, Limits
from core.redis_client import redis_client
from core.logger import setup_logger

logger = setup_logger("broadcast_service")


class BroadcastService:
    """خدمة الإذاعة."""

    @staticmethod
    async def is_running() -> bool:
        """هل هناك إذاعة قيد التنفيذ؟"""
        return await redis_client.exists(RedisKeys.BROADCAST_LOCK)

    @staticmethod
    async def _acquire_lock() -> None:
        """حجز قفل الإذاعة (ينتهي تلقائياً بعد ساعة كإجراء أمان)."""
        await redis_client.set(RedisKeys.BROADCAST_LOCK, "1", ex=3600)

    @staticmethod
    async def _release_lock() -> None:
        """تحرير قفل الإذاعة."""
        await redis_client.delete(RedisKeys.BROADCAST_LOCK)

    async def broadcast(
        self,
        client: Client,
        source_message: Message,
        target: Literal["all", "users", "groups"],
    ) -> dict:
        """
        تنفيذ الإذاعة.

        Args:
            client: عميل البوت.
            source_message: الرسالة المراد نسخها.
            target: الهدف (الكل/المستخدمون/المجموعات).

        Returns:
            تقرير: {success, failed, total}
        """
        await self._acquire_lock()
        try:
            # جمع المعرّفات حسب الهدف
            target_ids: list[int] = []
            if target in ("all", "users"):
                target_ids += await user_repo.get_all_user_ids()
            if target in ("all", "groups"):
                target_ids += await group_repo.get_all_active_group_ids()

            success = 0
            failed = 0

            # الإرسال على دفعات
            for i in range(0, len(target_ids), Limits.BROADCAST_BATCH_SIZE):
                batch = target_ids[i:i + Limits.BROADCAST_BATCH_SIZE]
                results = await asyncio.gather(
                    *[self._send_one(client, cid, source_message) for cid in batch],
                    return_exceptions=True,
                )
                for r in results:
                    if r is True:
                        success += 1
                    else:
                        failed += 1

                # توقف بين الدفعات لتجنب FloodWait
                await asyncio.sleep(Limits.BROADCAST_SLEEP)

            return {
                "success": success,
                "failed": failed,
                "total": len(target_ids),
            }
        finally:
            await self._release_lock()

    @staticmethod
    async def _send_one(
        client: Client,
        chat_id: int,
        source_message: Message,
    ) -> bool:
        """
        إرسال الرسالة لهدف واحد (نسخ بدون علامة التوجيه).

        Returns:
            True عند النجاح.
        """
        try:
            await source_message.copy(chat_id)
            return True
        except FloodWait as e:
            # احترام مهلة تيليجرام ثم إعادة المحاولة مرة واحدة
            await asyncio.sleep(e.value)
            try:
                await source_message.copy(chat_id)
                return True
            except Exception:
                return False
        except RPCError:
            # المستخدم حظر البوت / المجموعة محذوفة، إلخ
            return False
        except Exception as e:
            logger.debug(f"فشل إرسال إذاعة إلى {chat_id}: {e}")
            return False


broadcast_service = BroadcastService()
