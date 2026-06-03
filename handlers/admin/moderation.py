handlers/admin/moderation.py
═══════════════════════════════════════════════════════════════
معالجات أوامر الإدارة بالعربية الطبيعية.
حظر / فك حظر / كتم / فك كتم / تقييد / طرد / تثبيت / مسح.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.moderation_service import moderation_service
from utils.decorators import group_only
from utils.target_extractor import target_extractor
from utils.validators import validators
from locales.ar import messages
from core.exceptions import BotException
from core.logger import setup_logger

logger = setup_logger("moderation_handler")


def _extract_duration_and_reason(message: Message) -> tuple:
    """
    استخراج المدة والسبب من نص الرسالة.
    صيغة: <الأمر> [هدف] [مدة] [سبب...]
    """
    text = message.text or ""
    parts = text.split()
    duration = None
    reason_parts = []

    # تجاهل الأمر والهدف، نبحث عن مدة وسبب
    for part in parts[1:]:
        d = validators.validate_duration(part)
        if d is not None and duration is None:
            duration = d
        elif not part.startswith("@") and not part.lstrip("-").isdigit():
            reason_parts.append(part)

    reason = " ".join(reason_parts) if reason_parts else None
    return duration, reason


async def _get_target_or_reply(client: Client, message: Message):
    """استخراج الهدف أو الرد بخطأ."""
    target = await target_extractor.extract(client, message)
    if target is None:
        await message.reply_text(messages.REPLY_REQUIRED)
        return None
    return target


# ═══════════════════════════════════════════════════════════════
# الحظر
# ═══════════════════════════════════════════════════════════════
@group_only
async def ban_handler(client: Client, message: Message):
    target = await _get_target_or_reply(client, message)
    if not target:
        return
    duration, reason = _extract_duration_and_reason(message)
    try:
        result = await moderation_service.ban(
            client, message.chat.id, message.from_user.id,
            target.user_id, reason=reason, duration=duration,
        )
        await message.reply_text(f"{result}\n👤 {target.mention}")
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


@group_only
async def unban_handler(client: Client, message: Message):
    target = await _get_target_or_reply(client, message)
    if not target:
        return
    try:
        result = await moderation_service.unban(
            client, message.chat.id, message.from_user.id, target.user_id,
        )
        await message.reply_text(f"{result}\n👤 {target.mention}")
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


# ═══════════════════════════════════════════════════════════════
# الكتم
# ═══════════════════════════════════════════════════════════════
@group_only
async def mute_handler(client: Client, message: Message):
    target = await _get_target_or_reply(client, message)
    if not target:
        return
    duration, reason = _extract_duration_and_reason(message)
    try:
        result = await moderation_service.mute(
            client, message.chat.id, message.from_user.id,
            target.user_id, reason=reason, duration=duration,
        )
        await message.reply_text(f"{result}\n👤 {target.mention}")
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


@group_only
async def unmute_handler(client: Client, message: Message):
    target = await _get_target_or_reply(client, message)
    if not target:
        return
    try:
        result = await moderation_service.unmute(
            client, message.chat.id, message.from_user.id, target.user_id,
        )
        await message.reply_text(f"{result}\n👤 {target.mention}")
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


# ═══════════════════════════════════════════════════════════════
# التقييد
# ═══════════════════════════════════════════════════════════════
@group_only
async def restrict_handler(client: Client, message: Message):
    target = await _get_target_or_reply(client, message)
    if not target:
        return
    duration, _ = _extract_duration_and_reason(message)
    try:
        result = await moderation_service.restrict(
            client, message.chat.id, message.from_user.id,
            target.user_id, duration=duration,
        )
        await message.reply_text(f"{result}\n👤 {target.mention}")
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


@group_only
async def unrestrict_handler(client: Client, message: Message):
    target = await _get_target_or_reply(client, message)
    if not target:
        return
    try:
        result = await moderation_service.unrestrict(
            client, message.chat.id, message.from_user.id, target.user_id,
        )
        await message.reply_text(f"{result}\n👤 {target.mention}")
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


# ═══════════════════════════════════════════════════════════════
# الطرد
# ═══════════════════════════════════════════════════════════════
@group_only
async def kick_handler(client: Client, message: Message):
    target = await _get_target_or_reply(client, message)
    if not target:
        return
    try:
        result = await moderation_service.kick(
            client, message.chat.id, message.from_user.id, target.user_id,
        )
        await message.reply_text(f"{result}\n👤 {target.mention}")
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


# ═══════════════════════════════════════════════════════════════
# التثبيت
# ═══════════════════════════════════════════════════════════════
@group_only
async def pin_handler(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("❌ يجب الرد على الرسالة المراد تثبيتها")
        return
    try:
        result = await moderation_service.pin(
            client, message.chat.id, message.from_user.id,
            message.reply_to_message.id,
        )
        await message.reply_text(result)
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


@group_only
async def unpin_handler(client: Client, message: Message):
    msg_id = message.reply_to_message.id if message.reply_to_message else None
    try:
        result = await moderation_service.unpin(
            client, message.chat.id, message.from_user.id, msg_id,
        )
        await message.reply_text(result)
    except BotException as e:
        await message.reply_text(f"❌ {e.message}")


# ═══════════════════════════════════════════════════════════════
# مسح الرسائل
# ═══════════════════════════════════════════════════════════════
@group_only
async def purge_handler(client: Client, message: Message):
    """مسح الرسائل من الرسالة المردود عليها حتى الأمر."""
    from services.permission_service import permission_service
    from core.exceptions import PermissionDenied

    try:
        await permission_service.require_permission(
            message.chat.id, message.from_user.id, "delete_messages"
        )
    except PermissionDenied as e:
        await message.reply_text(f"❌ {e.message}")
        return

    if not message.reply_to_message:
        await message.reply_text("❌ رد على الرسالة لبدء المسح منها")
        return

    start_id = message.reply_to_message.id
    end_id = message.id
    message_ids = list(range(start_id, end_id + 1))

    # تيليجرام يحذف حتى 100 رسالة دفعة واحدة
    deleted = 0
    for i in range(0, len(message_ids), 100):
        batch = message_ids[i:i + 100]
        try:
            await client.delete_messages(message.chat.id, batch)
            deleted += len(batch)
        except Exception as e:
            logger.debug(f"خطأ في المسح: {e}")

    confirm = await client.send_message(message.chat.id, f"🗑 تم مسح {deleted} رسالة")
    # حذف رسالة التأكيد بعد 3 ثوانٍ
    import asyncio
    await asyncio.sleep(3)
    try:
        await confirm.delete()
    except Exception:
        pass
