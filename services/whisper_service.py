services/whisper_service.py
═══════════════════════════════════════════════════════════════
خدمة الهمسات: رسائل سرية لشخص معين عبر الوضع الانلاين (Inline Mode).
- همسة لشخص محدد (لا يراها غيره).
- همسة مؤقتة (تنتهي بعد مدة).
- همسة ذاتية التدمير (تُحذف بعد القراءة).

تُخزَّن في Redis مع TTL لأنها مؤقتة بطبيعتها.
═══════════════════════════════════════════════════════════════
"""

import uuid
import json
from typing import Optional

from config.constants import RedisKeys
from core.redis_client import redis_client
from core.logger import setup_logger

logger = setup_logger("whisper_service")


class WhisperService:
    """خدمة الهمسات."""

    @staticmethod
    def _generate_id() -> str:
        """توليد معرّف فريد للهمسة."""
        return uuid.uuid4().hex[:16]

    async def create_whisper(
        self,
        from_id: int,
        from_name: str,
        target_id: Optional[int],
        target_username: Optional[str],
        content: str,
        ttl: int = 3600,
        self_destruct: bool = False,
    ) -> str:
        """
        إنشاء همسة وإرجاع معرّفها.

        Args:
            from_id: مرسل الهمسة.
            target_id: المستهدف (إن عُرف معرّفه).
            target_username: يوزر المستهدف.
            content: محتوى الهمسة.
            ttl: مدة الصلاحية بالثواني.
            self_destruct: هل تُحذف بعد القراءة؟

        Returns:
            معرّف الهمسة.
        """
        whisper_id = self._generate_id()
        data = {
            "from_id": str(from_id),
            "from_name": from_name,
            "target_id": str(target_id) if target_id else "",
            "target_username": (target_username or "").lower(),
            "content": content,
            "self_destruct": "1" if self_destruct else "0",
        }
        await redis_client.set(
            RedisKeys.whisper(whisper_id),
            json.dumps(data, ensure_ascii=False),
            ex=ttl,
        )
        return whisper_id

    async def read_whisper(
        self,
        whisper_id: str,
        reader_id: int,
        reader_username: Optional[str],
    ) -> dict:
        """
        قراءة همسة.

        Returns:
            dict: {"allowed": bool, "content": str, "message": str}
        """
        raw = await redis_client.get(RedisKeys.whisper(whisper_id))
        if not raw:
            return {"allowed": False, "content": "", "message": "⏳ انتهت صلاحية الهمسة"}

        data = json.loads(raw)
        target_id = data.get("target_id", "")
        target_username = data.get("target_username", "")

        # التحقق من أن القارئ هو المستهدف (أو المرسل)
        is_target = False
        if target_id and str(reader_id) == target_id:
            is_target = True
        elif target_username and reader_username and reader_username.lower() == target_username:
            is_target = True
        elif str(reader_id) == data.get("from_id"):
            is_target = True  # المرسل يستطيع رؤية همسته

        if not is_target:
            return {
                "allowed": False, "content": "",
                "message": "🔒 هذه الهمسة ليست موجّهة إليك",
            }

        # الحذف الذاتي
        if data.get("self_destruct") == "1":
            await redis_client.delete(RedisKeys.whisper(whisper_id))

        return {
            "allowed": True,
            "content": data["content"],
            "message": data["content"],
            "from_name": data.get("from_name", "مجهول"),
        }


whisper_service = WhisperService()
