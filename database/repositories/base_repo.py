database/repositories/base_repo.py
═══════════════════════════════════════════════════════════════
المستودع الأساسي الذي ترث منه كل المستودعات.
يوفّر وصولاً موحّداً لقاعدة البيانات و Redis،
ودوال مساعدة لتحويل سجلات asyncpg إلى dict.
═══════════════════════════════════════════════════════════════
"""

from typing import Optional, Any

import asyncpg

from core.database import db
from core.redis_client import redis_client


class BaseRepository:
    """
    الأساس لكل المستودعات.
    لا يحتوي منطق عمل، فقط أدوات وصول للبيانات.
    """

    def __init__(self) -> None:
        self.db = db
        self.redis = redis_client

    # ───────────────────────────────────────────────
    # أدوات تحويل
    # ───────────────────────────────────────────────

    @staticmethod
    def record_to_dict(record: Optional[asyncpg.Record]) -> Optional[dict]:
        """تحويل سجل asyncpg واحد إلى dict (أو None)."""
        return dict(record) if record is not None else None

    @staticmethod
    def records_to_list(records: list[asyncpg.Record]) -> list[dict]:
        """تحويل قائمة سجلات إلى قائمة dict."""
        return [dict(r) for r in records]
