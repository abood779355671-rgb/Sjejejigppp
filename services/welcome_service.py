services/welcome_service.py
═══════════════════════════════════════════════════════════════
خدمة الترحيب: بناء وإرسال رسائل الترحيب والمغادرة.
تدعم المتغيرات الديناميكية والوسائط والأزرار.
═══════════════════════════════════════════════════════════════
"""

import json
from typing import Optional

from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, User

from database.repositories.welcome_repo import welcome_repo
from core.logger import setup_logger

logger = setup_logger("welcome_service")


class WelcomeService:
    """خدمة الترحيب."""

    @staticmethod
    def _format_text(template: str, user: User, chat_title: str, members: int) -> str:
        """
        استبدال المتغيرات في نص الترحيب.

        المتغيرات المدعومة:
        {name} {mention} {username} {id} {group} {count}
        """
        name = user.first_name or "عضو"
        mention = f'<a href="tg://user?id={user.id}">{name}</a>'
        username = f"@{user.username}" if user.username else name

        return (
            template
            .replace("{name}", name)
            .replace("{mention}", mention)
            .replace("{username}", username)
            .replace("{id}", str(user.id))
            .replace("{group}", chat_title or "المجموعة")
            .replace("{count}", str(members))
        )

    @staticmethod
    def _build_buttons(buttons_data: list) -> Optional[InlineKeyboardMarkup]:
        """
        بناء أزرار انلاين من البيانات المخزّنة.
        صيغة كل زر: {"text": "...", "url": "..."}
        """
        if not buttons_data:
            return None
        try:
            rows = []
            for btn in buttons_data:
                if "text" in btn and "url" in btn:
                    rows.append([InlineKeyboardButton(btn["text"], url=btn["url"])])
            return InlineKeyboardMarkup(rows) if rows else None
        except Exception as e:
            logger.debug(f"خطأ في بناء أزرار الترحيب: {e}")
            return None

    async def send_welcome(
        self,
        client: Client,
        chat_id: int,
        user: User,
        chat_title: str,
        members_count: int = 0,
    ) -> None:
        """إرسال رسالة ترحيب لعضو جديد."""
        settings_data = await welcome_repo.get_settings(chat_id)

        if not settings_data.get("is_enabled", True):
            return

        text_template = settings_data.get("welcome_text")
        if not text_template:
            text_template = "أهلاً بك {mention} في {group} 🌹"

        text = self._format_text(text_template, user, chat_title, members_count)

        # الأزرار
        buttons_data = settings_data.get("buttons", [])
        if isinstance(buttons_data, str):
            try:
                buttons_data = json.loads(buttons_data)
            except (json.JSONDecodeError, TypeError):
                buttons_data = []
        markup = self._build_buttons(buttons_data)

        # الوسائط
        media_type = settings_data.get("media_type")
        media_file_id = settings_data.get("media_file_id")

        try:
            if media_type == "photo" and media_file_id:
                await client.send_photo(
                    chat_id, media_file_id, caption=text, reply_markup=markup,
                )
            elif media_type == "video" and media_file_id:
                await client.send_video(
                    chat_id, media_file_id, caption=text, reply_markup=markup,
                )
            else:
                await client.send_message(chat_id, text, reply_markup=markup)
        except Exception as e:
            logger.debug(f"فشل إرسال الترحيب: {e}")

    async def send_goodbye(
        self,
        client: Client,
        chat_id: int,
        user: User,
        chat_title: str,
    ) -> None:
        """إرسال رسالة مغادرة."""
        settings_data = await welcome_repo.get_settings(chat_id)

        if not settings_data.get("goodbye_enabled", False):
            return

        text_template = settings_data.get("goodbye_text")
        if not text_template:
            return

        text = self._format_text(text_template, user, chat_title, 0)
        try:
            await client.send_message(chat_id, text)
        except Exception as e:
            logger.debug(f"فشل إرسال المغادرة: {e}")


welcome_service = WelcomeService()
