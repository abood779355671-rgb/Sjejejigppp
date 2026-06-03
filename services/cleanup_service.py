services/cleanup_service.py
═══════════════════════════════════════════════════════════════
خدمة التنظيف التلقائي: حذف الوسائط بعد مدة محددة.
═══════════════════════════════════════════════════════════════
"""

import asyncio

from pyrogram import Client
from pyrogram.types import Message

from database.repositories.cleanup_repo import cleanup_repo
from core.logger import setup_logger

logger = setup_logger("cleanup_service")


class CleanupService:
    """خدمة التنظيف التلقائي."""

    async def check_and_schedule(self, client: Client, message: Message) -> None:
        """
        فحص رسالة: إن كانت من نوع مُفعّل تنظيفه، جدول حذفها.
        """
        chat_id = message.chat.id
        settings_data = await cleanup_repo.get_settings(chat_id)

        # هل أي تنظيف مفعّل؟
        if not any([
            settings_data.get("clean_photos"),
            settings_data.get("clean_videos"),
            settings_data.get("clean_files"),
            settings_data.get("clean_albums"),
        ]):
            return

        should_delete = False
        if settings_data.get("clean_photos") and message.photo:
            should_delete = True
        elif settings_data.get("clean_videos") and (message.video or message.video_note):
            should_delete = True
        elif settings_data.get("clean_files") and message.document:
            should_delete = True
        elif settings_data.get("clean_albums") and message.media_group_id:
            should_delete = True

        if should_delete:
            delay = settings_data.get("delete_after", 60)
            asyncio.create_task(self._delete_after(message, delay))

    @staticmethod
    async def _delete_after(message: Message, seconds: int) -> None:
        """حذف رسالة بعد مدة."""
        await asyncio.sleep(seconds)
        try:
            await message.delete()
        except Exception as e:
            logger.debug(f"فشل حذف رسالة التنظيف: {e}")


cleanup_service = CleanupService()
