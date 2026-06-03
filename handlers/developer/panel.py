handlers/developer/panel.py
═══════════════════════════════════════════════════════════════
لوحة المطور التفاعلية + إدارة المطورين.
كل المعالجات محمية بـ @developers_only أو @main_developer_only.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from utils.decorators import developers_only, main_developer_only, private_only
from utils.context import RequestContext
from services.stats_service import stats_service
from services.broadcast_service import broadcast_service
from middlewares.maintenance import maintenance_middleware
from database.repositories.user_repo import user_repo
from database.repositories.log_repo import log_repo
from keyboards.developer_kb import developer_kb
from locales.ar import messages
from config.constants import RANK_NAMES_AR, RankLevel, EventType
from config.settings import settings
from core.redis_client import redis_client
from core.logger import setup_logger

logger = setup_logger("dev_panel")


# ═══════════════════════════════════════════════════════════════
# فتح لوحة المطور (أمر نصي)
# ═══════════════════════════════════════════════════════════════
@developers_only
async def open_panel(client: Client, message: Message):
    """فتح لوحة المطور عبر /dev أو /panel."""
    await message.reply_text(
        messages.DEV_PANEL_TITLE,
        reply_markup=developer_kb.main_panel(),
    )


# ═══════════════════════════════════════════════════════════════
# معالج أزرار اللوحة (Callback Router)
# ═══════════════════════════════════════════════════════════════
@developers_only
async def panel_callback(client: Client, callback: CallbackQuery):
    """
    موجّه أزرار لوحة المطور.
    صيغة البيانات: dev:section:action
    """
    data = callback.data
    parts = data.split(":")

    # ─── إغلاق اللوحة ───
    if data == "dev:close":
        await callback.message.delete()
        return

    # ─── الرجوع للرئيسية ───
    if data == "dev:main":
        await callback.message.edit_text(
            messages.DEV_PANEL_TITLE,
            reply_markup=developer_kb.main_panel(),
        )
        await callback.answer()
        return

    section = parts[1] if len(parts) > 1 else ""
    action = parts[2] if len(parts) > 2 else ""

    # ─── توجيه حسب القسم ───
    if section == "stats":
        await _handle_stats(callback)
    elif section == "broadcast":
        await _handle_broadcast(callback, action)
    elif section == "developers":
        await _handle_developers(callback, action)
    elif section == "errors":
        await _handle_errors(callback)
    elif section == "logs":
        await _handle_logs(callback)
    elif section == "maintenance":
        await _handle_maintenance(callback, action)
    elif section == "backup":
        await _handle_backup(callback, action)
    elif section == "restart":
        await _handle_restart(callback, action)
    else:
        await callback.answer("قيد التطوير")


# ───────────────────────────────────────────────
# قسم الإحصائيات
# ───────────────────────────────────────────────
async def _handle_stats(callback: CallbackQuery):
    """عرض الإحصائيات."""
    stats = await stats_service.get_full_stats()
    text = messages.STATS_TEMPLATE.format(**stats)
    await callback.message.edit_text(
        text,
        reply_markup=developer_kb.back_button(),
    )
    await callback.answer()


# ───────────────────────────────────────────────
# قسم الإذاعة
# ───────────────────────────────────────────────
async def _handle_broadcast(callback: CallbackQuery, action: str):
    """إدارة الإذاعة."""
    if action == "menu":
        await callback.message.edit_text(
            "📢 <b>الإذاعة</b>\n\nاختر نوع الإذاعة:",
            reply_markup=developer_kb.broadcast_menu(),
        )
        await callback.answer()
        return

    # تحديد الهدف وحفظ الحالة لانتظار الرسالة
    if action in ("all", "users", "groups"):
        if await broadcast_service.is_running():
            await callback.answer(messages.BROADCAST_RUNNING, show_alert=True)
            return

        user_id = callback.from_user.id
        # حفظ نوع الإذاعة في FSM
        await redis_client.set_state(user_id, f"broadcast:{action}", ttl=300)
        await callback.message.edit_text(
            messages.BROADCAST_ASK,
            reply_markup=developer_kb.back_button(),
        )
        await callback.answer()


# ───────────────────────────────────────────────
# قسم المطورين
# ───────────────────────────────────────────────
async def _handle_developers(callback: CallbackQuery, action: str):
    """إدارة المطورين."""
    user_id = callback.from_user.id

    if action == "menu":
        await callback.message.edit_text(
            "👨‍💻 <b>إدارة المطورين</b>",
            reply_markup=developer_kb.developers_menu(),
        )
        await callback.answer()

    elif action == "list":
        developers = await user_repo.get_all_developers()
        lines = ["👨‍💻 <b>قائمة المطورين</b>\n"]
        for dev in developers:
            tag = "👑 أساسي" if dev["is_main_dev"] else "🔹 مطور"
            name = dev.get("first_name") or "مستخدم"
            lines.append(f"{tag} | {name} (<code>{dev['user_id']}</code>)")
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=developer_kb.back_button(),
        )
        await callback.answer()

    elif action in ("add", "remove"):
        # إدارة المطورين للمطور الأساسي فقط
        if not await user_repo.is_main_developer(user_id):
            await callback.answer(messages.MAIN_DEV_ONLY, show_alert=True)
            return
        state = "dev_add" if action == "add" else "dev_remove"
        await redis_client.set_state(user_id, state, ttl=300)
        verb = "إضافته" if action == "add" else "حذفه"
        await callback.message.edit_text(
            f"أرسل معرّف المستخدم المراد {verb} (ID رقمي):",
            reply_markup=developer_kb.back_button(),
        )
        await callback.answer()


# ───────────────────────────────────────────────
# قسم الأخطاء
# ───────────────────────────────────────────────
async def _handle_errors(callback: CallbackQuery):
    """عرض آخر الأخطاء."""
    errors = await log_repo.get_recent_errors(limit=10)
    if not errors:
        text = "✅ لا توجد أخطاء مسجّلة"
    else:
        lines = ["🐞 <b>آخر الأخطاء</b>\n"]
        for err in errors:
            ts = err["created_at"].strftime("%m-%d %H:%M")
            msg = (err.get("message") or "")[:60]
            lines.append(f"• <code>{ts}</code> | {err['error_type']}\n  {msg}")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=developer_kb.back_button())
    await callback.answer()


# ───────────────────────────────────────────────
# قسم السجلات
# ───────────────────────────────────────────────
async def _handle_logs(callback: CallbackQuery):
    """عرض آخر أحداث السجل."""
    events = await log_repo.get_events(limit=10)
    if not events:
        text = "📋 لا توجد أحداث مسجّلة"
    else:
        lines = ["📋 <b>سجل العمليات</b>\n"]
        for ev in events:
            ts = ev["created_at"].strftime("%m-%d %H:%M")
            lines.append(f"• <code>{ts}</code> | {ev['event_type']}")
        text = "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=developer_kb.back_button())
    await callback.answer()


# ───────────────────────────────────────────────
# قسم الصيانة
# ───────────────────────────────────────────────
async def _handle_maintenance(callback: CallbackQuery, action: str):
    """إدارة وضع الصيانة."""
    if action == "menu":
        is_on = await maintenance_middleware.is_maintenance()
        status = "🟢 مفعّل" if is_on else "🔴 معطّل"
        await callback.message.edit_text(
            f"🛠 <b>وضع الصيانة</b>\n\nالحالة: {status}",
            reply_markup=developer_kb.maintenance_menu(is_on),
        )
        await callback.answer()

    elif action == "on":
        await maintenance_middleware.set_maintenance(True)
        await callback.answer("تم تفعيل الصيانة", show_alert=True)
        await callback.message.edit_text(
            messages.MAINTENANCE_ON,
            reply_markup=developer_kb.maintenance_menu(True),
        )

    elif action == "off":
        await maintenance_middleware.set_maintenance(False)
        await callback.answer("تم إيقاف الصيانة", show_alert=True)
        await callback.message.edit_text(
            messages.MAINTENANCE_OFF,
            reply_markup=developer_kb.maintenance_menu(False),
        )


# ───────────────────────────────────────────────
# قسم النسخ الاحتياطي (الواجهة - التنفيذ في المرحلة 11)
# ───────────────────────────────────────────────
async def _handle_backup(callback: CallbackQuery, action: str):
    """إدارة النسخ الاحتياطي."""
    if action == "menu":
        await callback.message.edit_text(
            "💾 <b>النسخ الاحتياطي</b>",
            reply_markup=developer_kb.backup_menu(),
        )
        await callback.answer()
    else:
        await callback.answer("سيُفعّل في مرحلة لاحقة", show_alert=True)


# ───────────────────────────────────────────────
# قسم إعادة التشغيل
# ───────────────────────────────────────────────
async def _handle_restart(callback: CallbackQuery, action: str):
    """إعادة تشغيل البوت."""
    if action == "confirm":
        await callback.message.edit_text(
            "⚠️ هل أنت متأكد من إعادة التشغيل؟",
            reply_markup=developer_kb.restart_confirm(),
        )
        await callback.answer()

    elif action == "yes":
        await callback.answer("جارٍ إعادة التشغيل...", show_alert=True)
        await callback.message.edit_text(messages.RESTART_STARTED)
        import os, sys
        # إعادة تشغيل العملية (تعمل تحت مدير عمليات مثل Docker/systemd)
        os.execv(sys.executable, [sys.executable] + sys.argv)


# ═══════════════════════════════════════════════════════════════
# معالج إدخالات المطور (FSM) - الإذاعة وإدارة المطورين
# ═══════════════════════════════════════════════════════════════
@developers_only
@private_only
async def handle_dev_input(client: Client, message: Message):
    """
    معالج النصوص أثناء حالة FSM نشطة للمطور.
    يُستدعى عند وجود حالة broadcast:* أو dev_add/dev_remove.
    """
    user_id = message.from_user.id
    state = await redis_client.get_state(user_id)

    if not state:
        return  # لا حالة نشطة، تجاهل

    # إلغاء
    if message.text and message.text.strip() == "/cancel":
        await redis_client.clear_state(user_id)
        await message.reply_text(messages.CANCELLED)
        return

    # ─── الإذاعة ───
    if state.startswith("broadcast:"):
        target = state.split(":")[1]
        await redis_client.clear_state(user_id)
        await message.reply_text(messages.BROADCAST_STARTED)
        report = await broadcast_service.broadcast(client, message, target)
        await message.reply_text(messages.BROADCAST_DONE.format(**report))
        await log_repo.log_event(
            EventType.SETTINGS_CHANGED.value,
            actor_id=user_id,
            details={"action": "broadcast", "target": target, **report},
        )
        return

    # ─── إضافة مطور ───
    if state == "dev_add":
        await redis_client.clear_state(user_id)
        await _process_add_developer(message)
        return

    # ─── حذف مطور ───
    if state == "dev_remove":
        await redis_client.clear_state(user_id)
        await _process_remove_developer(message)
        return


async def _process_add_developer(message: Message):
    """تنفيذ إضافة مطور بعد استلام المعرّف."""
    from utils.validators import validators
    from core.exceptions import ValidationError

    try:
        target_id = validators.validate_user_id(message.text)
    except ValidationError:
        await message.reply_text("❌ معرّف غير صالح")
        return

    if await user_repo.is_developer(target_id):
        await message.reply_text(messages.DEV_ALREADY)
        return

    # التأكد من وجود المستخدم في القاعدة (تسجيله إن لزم)
    await user_repo.upsert_user(user_id=target_id)
    await user_repo.set_developer(target_id, True)

    user = await user_repo.get_user(target_id)
    name = (user.get("first_name") if user else None) or "مستخدم"
    await message.reply_text(messages.DEV_ADDED.format(name=name, user_id=target_id))
    await log_repo.log_event(
        EventType.RANK_PROMOTED.value,
        actor_id=message.from_user.id,
        target_id=target_id,
        details={"role": "developer"},
    )


async def _process_remove_developer(message: Message):
    """تنفيذ حذف مطور بعد استلام المعرّف."""
    from utils.validators import validators
    from core.exceptions import ValidationError

    try:
        target_id = validators.validate_user_id(message.text)
    except ValidationError:
        await message.reply_text("❌ معرّف غير صالح")
        return

    # لا يمكن حذف المطور الأساسي
    if target_id == settings.MAIN_DEVELOPER_ID or await user_repo.is_main_developer(target_id):
        await message.reply_text(messages.DEV_CANNOT_REMOVE_MAIN)
        return

    if not await user_repo.is_developer(target_id):
        await message.reply_text(messages.DEV_NOT_DEV)
        return

    await user_repo.set_developer(target_id, False)
    user = await user_repo.get_user(target_id)
    name = (user.get("first_name") if user else None) or "مستخدم"
    await message.reply_text(messages.DEV_REMOVED.format(name=name, user_id=target_id))
    await log_repo.log_event(
        EventType.RANK_DEMOTED.value,
        actor_id=message.from_user.id,
        target_id=target_id,
        details={"role": "developer"},
    )
