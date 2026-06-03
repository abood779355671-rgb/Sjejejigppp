handlers/info/handlers.py
═══════════════════════════════════════════════════════════════
معالجات المعلومات (ID/معلومات/الرتبة) والسجلات.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.info_service import info_service
from services.rank_service import rank_service
from utils.target_extractor import target_extractor
from utils.decorators import group_only, require_permission
from database.repositories.log_repo import log_repo
from core.logger import setup_logger

logger = setup_logger("info_handlers")


async def id_handler(client: Client, message: Message):
    """عرض المعرّف. الاستخدام: ايدي / آيدي (أو بالرد)."""
    target = await target_extractor.extract(client, message)
    if target:
        text = (
            f"🆔 <b>المعرّف</b>\n\n"
            f"معرّف المستخدم: <code>{target.user_id}</code>"
        )
    else:
        text = (
            f"🆔 <b>المعرّفات</b>\n\n"
            f"معرّفك: <code>{message.from_user.id}</code>\n"
            f"معرّف المحادثة: <code>{message.chat.id}</code>"
        )
    await message.reply_text(text)


async def user_info_handler(client: Client, message: Message):
    """معلومات المستخدم. الاستخدام: معلوماتي / معلومات (بالرد)."""
    target = await target_extractor.extract(client, message)

    if target:
        try:
            user = await client.get_users(target.user_id)
        except Exception:
            await message.reply_text("❌ تعذّر جلب المعلومات")
            return
    else:
        user = message.from_user

    text = await info_service.get_user_info(client, message.chat.id, user)
    await message.reply_text(text)


@group_only
async def group_info_handler(client: Client, message: Message):
    """معلومات المجموعة. الاستخدام: معلومات المجموعة."""
    text = await info_service.get_group_info(client, message)
    await message.reply_text(text)


@group_only
async def my_rank_handler(client: Client, message: Message):
    """عرض رتبتي. الاستخدام: رتبتي."""
    rank_name = await rank_service.get_user_rank_name(
        message.chat.id, message.from_user.id,
    )
    await message.reply_text(f"🎖 رتبتك: <b>{rank_name}</b>")


@group_only
@require_permission("view_logs")
async def show_logs_handler(client: Client, message: Message):
    """عرض سجل المجموعة. الاستخدام: السجل."""
    events = await log_repo.get_events(chat_id=message.chat.id, limit=15)
    if not events:
        await message.reply_text("📋 لا توجد أحداث مسجّلة")
        return

    event_names = {
        "msg_deleted": "حذف رسالة", "msg_edited": "تعديل رسالة",
        "member_joined": "دخول عضو", "member_left": "خروج عضو",
        "rank_promoted": "رفع رتبة", "rank_demoted": "تنزيل رتبة",
        "user_banned": "حظر", "user_muted": "كتم",
        "protection_triggered": "حماية", "settings_changed": "تغيير إعداد",
    }

    lines = ["📋 <b>سجل العمليات</b>\n"]
    for ev in events:
        ts = ev["created_at"].strftime("%m-%d %H:%M")
        name = event_names.get(ev["event_type"], ev["event_type"])
        lines.append(f"• <code>{ts}</code> | {name}")
    await message.reply_text("\n".join(lines))
