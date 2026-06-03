handlers/protection/panel.py
═══════════════════════════════════════════════════════════════
لوحة تحكم الحماية التفاعلية (للمدير فأعلى).
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message, CallbackQuery

from utils.decorators import group_only, require_permission
from database.repositories.protection_repo import protection_repo
from database.repositories.log_repo import log_repo
from services.permission_service import permission_service
from keyboards.protection_kb import protection_kb
from config.constants import EventType
from core.logger import setup_logger

logger = setup_logger("protection_panel")


@group_only
@require_permission("manage_protection")
async def open_protection_panel(client: Client, message: Message):
    """فتح لوحة الحماية."""
    settings_data = await protection_repo.get_settings(message.chat.id)
    await message.reply_text(
        "🛡 <b>لوحة الحماية</b>\n\n"
        "اضغط على أي نوع لتفعيله أو تعطيله:",
        reply_markup=protection_kb.main_panel(settings_data),
    )


async def protection_callback(client: Client, callback: CallbackQuery):
    """موجّه أزرار لوحة الحماية."""
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    # فحص الصلاحية
    if not await permission_service.has_permission(chat_id, user_id, "manage_protection"):
        await callback.answer("❌ ليس لديك صلاحية", show_alert=True)
        return

    data = callback.data
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    # إغلاق
    if action == "close":
        await callback.message.delete()
        return

    # رجوع للرئيسية
    if action == "main":
        settings_data = await protection_repo.get_settings(chat_id)
        await callback.message.edit_reply_markup(
            protection_kb.main_panel(settings_data)
        )
        await callback.answer()
        return

    # تبديل نوع حماية
    if action == "toggle":
        field = parts[2]
        settings_data = await protection_repo.get_settings(chat_id)
        current = settings_data.get(field, False)
        new_value = not current
        await protection_repo.toggle_protection(chat_id, field, new_value)

        # تسجيل
        await log_repo.log_event(
            EventType.SETTINGS_CHANGED.value,
            chat_id=chat_id, actor_id=user_id,
            details={"protection": field, "value": new_value},
        )

        # تحديث اللوحة
        updated = await protection_repo.get_settings(chat_id)
        await callback.message.edit_reply_markup(
            protection_kb.main_panel(updated)
        )
        status = "تفعيل" if new_value else "تعطيل"
        await callback.answer(f"تم {status} الحماية")
        return

    # قائمة العقوبات
    if action == "punishment":
        await callback.message.edit_reply_markup(
            protection_kb.punishment_menu()
        )
        await callback.answer()
        return

    # تعيين عقوبة
    if action == "setpunish":
        punishment = parts[2]
        await protection_repo.update_punishment(chat_id, punishment)
        settings_data = await protection_repo.get_settings(chat_id)
        await callback.message.edit_reply_markup(
            protection_kb.main_panel(settings_data)
        )
        await callback.answer("تم تحديث العقوبة")
        return
