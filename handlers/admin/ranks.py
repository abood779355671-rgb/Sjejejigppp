handlers/admin/ranks.py
═══════════════════════════════════════════════════════════════
معالجات رفع وتنزيل الرتب بالعربية الطبيعية.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.rank_service import rank_service
from utils.decorators import group_only
from utils.target_extractor import target_extractor
from config.constants import RankLevel
from locales.ar import messages
from core.exceptions import BotException


async def _get_target_or_reply(client: Client, message: Message):
    target = await target_extractor.extract(client, message)
    if target is None:
        await message.reply_text(messages.REPLY_REQUIRED)
        return None
    return target


def _make_promote_handler(rank_level: int):
    """مصنع معالجات الرفع (يولّد معالجاً لكل رتبة)."""
    @group_only
    async def handler(client: Client, message: Message):
        target = await _get_target_or_reply(client, message)
        if not target:
            return
        try:
            result = await rank_service.promote(
                message.chat.id, message.from_user.id,
                target.user_id, rank_level,
            )
            await message.reply_text(f"{result}\n👤 {target.mention}")
        except BotException as e:
            await message.reply_text(f"❌ {e.message}")
    return handler


def _make_demote_handler(from_rank: int):
    """مصنع معالجات التنزيل."""
    @group_only
    async def handler(client: Client, message: Message):
        target = await _get_target_or_reply(client, message)
        if not target:
            return
        try:
            result = await rank_service.demote(
                message.chat.id, message.from_user.id,
                target.user_id, from_rank,
            )
            await message.reply_text(f"{result}\n👤 {target.mention}")
        except BotException as e:
            await message.reply_text(f"❌ {e.message}")
    return handler


# توليد كل المعالجات
promote_vip_handler       = _make_promote_handler(RankLevel.VIP)
promote_admin_handler     = _make_promote_handler(RankLevel.ADMIN)
promote_manager_handler   = _make_promote_handler(RankLevel.MANAGER)
promote_owner_handler     = _make_promote_handler(RankLevel.OWNER)
promote_main_owner_handler = _make_promote_handler(RankLevel.MAIN_OWNER)

demote_vip_handler        = _make_demote_handler(RankLevel.VIP)
demote_admin_handler      = _make_demote_handler(RankLevel.ADMIN)
demote_manager_handler    = _make_demote_handler(RankLevel.MANAGER)
demote_owner_handler      = _make_demote_handler(RankLevel.OWNER)
demote_main_owner_handler = _make_demote_handler(RankLevel.MAIN_OWNER)
