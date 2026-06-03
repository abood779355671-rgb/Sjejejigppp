handlers/sarahah/handlers.py
═══════════════════════════════════════════════════════════════
معالجات نظام الصراحة (رسائل مجهولة).
- إنشاء رابط صراحة.
- استقبال رسائل مجهولة عبر deep-link.
- الرد على الرسائل.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
)

from services.whisper_service import whisper_service  # لإعادة الاستخدام
from database.repositories.sarahah_repo import sarahah_repo
from core.redis_client import redis_client
from core.logger import setup_logger

logger = setup_logger("sarahah_handlers")


async def sarahah_link_handler(client: Client, message: Message):
    """إنشاء/عرض رابط الصراحة (في الخاص)."""
    user_id = message.from_user.id
    link_code = await sarahah_repo.get_or_create_link(user_id)
    bot_username = client.bot_info.username if client.bot_info else "bot"

    link = f"https://t.me/{bot_username}?start=sarahah_{link_code}"
    await message.reply_text(
        f"🎭 <b>رابط الصراحة الخاص بك</b>\n\n"
        f"شارك هذا الرابط ليرسل لك أصدقاؤك رسائل مجهولة:\n\n"
        f"<code>{link}</code>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 مشاركة الرابط", url=f"https://t.me/share/url?url={link}")]
        ]),
    )


async def sarahah_start_handler(client: Client, message: Message, link_code: str):
    """
    معالج الدخول عبر رابط صراحة (start=sarahah_CODE).
    يضع المستخدم في حالة كتابة رسالة مجهولة.
    """
    owner_id = await sarahah_repo.get_link_owner(link_code)
    if not owner_id:
        await message.reply_text("❌ رابط الصراحة غير صالح أو منتهي")
        return

    if owner_id == message.from_user.id:
        await message.reply_text("⚠️ لا يمكنك إرسال رسالة لنفسك")
        return

    # حفظ الحالة: ينتظر نص الرسالة المجهولة
    await redis_client.set_state(
        message.from_user.id, f"sarahah_write:{link_code}:{owner_id}", ttl=600,
    )
    await message.reply_text(
        "🎭 <b>أرسل رسالتك المجهولة الآن</b>\n\n"
        "سيتم إرسالها بشكل مجهول تماماً.\n"
        "للإلغاء أرسل /cancel"
    )


async def sarahah_write_handler(client: Client, message: Message):
    """معالج كتابة الرسالة المجهولة (FSM)."""
    user_id = message.from_user.id
    state = await redis_client.get_state(user_id)

    if not state or not state.startswith("sarahah_write:"):
        return

    if message.text and message.text.strip() == "/cancel":
        await redis_client.clear_state(user_id)
        await message.reply_text("✅ تم الإلغاء")
        return

    parts = state.split(":")
    link_code = parts[1]
    owner_id = int(parts[2])
    content = message.text or message.caption or ""

    if not content:
        await message.reply_text("❌ أرسل نصاً فقط")
        return

    await redis_client.clear_state(user_id)

    # حفظ الرسالة
    msg_id = await sarahah_repo.save_message(link_code, owner_id, content)

    # إرسالها لصاحب الرابط مع زر رد
    try:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 رد", callback_data=f"sarahah:reply:{msg_id}:{user_id}")]
        ])
        await client.send_message(
            owner_id,
            f"🎭 <b>رسالة مجهولة جديدة</b>\n\n{content}",
            reply_markup=markup,
        )
        await message.reply_text("✅ تم إرسال رسالتك بشكل مجهول")
    except Exception as e:
        logger.debug(f"فشل إرسال رسالة الصراحة: {e}")
        await message.reply_text("⚠️ تعذّر الإرسال (ربما لم يبدأ المستخدم البوت)")


async def sarahah_reply_callback(client: Client, callback: CallbackQuery):
    """معالج الرد على رسالة مجهولة."""
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("خطأ", show_alert=True)
        return

    msg_id = parts[2]
    sender_id = parts[3]

    # حفظ حالة الرد
    await redis_client.set_state(
        callback.from_user.id, f"sarahah_reply:{sender_id}", ttl=600,
    )
    await callback.message.reply_text(
        "💬 أرسل ردك الآن (سيصل للمرسل المجهول):"
    )
    await callback.answer()


async def sarahah_reply_write_handler(client: Client, message: Message):
    """معالج كتابة الرد على المجهول (FSM)."""
    user_id = message.from_user.id
    state = await redis_client.get_state(user_id)

    if not state or not state.startswith("sarahah_reply:"):
        return

    target_id = int(state.split(":")[1])
    content = message.text or ""
    await redis_client.clear_state(user_id)

    try:
        await client.send_message(
            target_id,
            f"💬 <b>رد على رسالتك المجهولة</b>\n\n{content}",
        )
        await message.reply_text("✅ تم إرسال ردك")
    except Exception:
        await message.reply_text("⚠️ تعذّر إرسال الرد")
