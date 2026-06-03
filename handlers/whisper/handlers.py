handlers/whisper/handlers.py
═══════════════════════════════════════════════════════════════
معالجات الهمسات عبر الوضع الانلاين.
الاستخدام: @bot @username نص الهمسة
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,
)

from services.whisper_service import whisper_service
from database.repositories.user_repo import user_repo
from utils.validators import validators
from core.exceptions import ValidationError
from core.logger import setup_logger

logger = setup_logger("whisper_handlers")


async def whisper_inline_handler(client: Client, inline_query: InlineQuery):
    """
    معالج الاستعلام الانلاين للهمسات.
    الصيغة: @username نص الهمسة
    """
    query = inline_query.query.strip()
    from_user = inline_query.from_user

    if not query:
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title="💬 إرسال همسة",
                    description="اكتب: @يوزر نص الهمسة",
                    input_message_content=InputTextMessageContent(
                        "💬 لإرسال همسة اكتب: @يوزر ثم نص الهمسة"
                    ),
                )
            ],
            cache_time=1,
        )
        return

    parts = query.split(maxsplit=1)
    if len(parts) < 2 or not parts[0].startswith("@"):
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title="⚠️ صيغة خاطئة",
                    description="الصيغة: @يوزر نص الهمسة",
                    input_message_content=InputTextMessageContent(
                        "⚠️ الصيغة الصحيحة: @يوزر نص الهمسة"
                    ),
                )
            ],
            cache_time=1,
        )
        return

    target_username_raw = parts[0]
    content = parts[1]

    try:
        target_username = validators.validate_username(target_username_raw)
    except ValidationError:
        await inline_query.answer(results=[], cache_time=1)
        return

    # البحث عن المستهدف في القاعدة
    target_user = await user_repo.get_user_by_username(target_username)
    target_id = target_user["user_id"] if target_user else None

    # إنشاء الهمسة
    whisper_id = await whisper_service.create_whisper(
        from_id=from_user.id,
        from_name=from_user.first_name or "مجهول",
        target_id=target_id,
        target_username=target_username,
        content=content,
        ttl=3600,
        self_destruct=True,
    )

    # زر فتح الهمسة
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("👁 عرض الهمسة", callback_data=f"whisper:read:{whisper_id}")]
    ])

    await inline_query.answer(
        results=[
            InlineQueryResultArticle(
                title=f"💬 همسة إلى @{target_username}",
                description=f"اضغط للإرسال — {content[:30]}...",
                input_message_content=InputTextMessageContent(
                    f"🔒 <b>همسة سرية</b>\n"
                    f"إلى: @{target_username}\n"
                    f"من: {from_user.first_name}\n\n"
                    f"<i>فقط المستهدف يمكنه رؤيتها</i>"
                ),
                reply_markup=markup,
            )
        ],
        cache_time=1,
    )


async def whisper_callback_handler(client: Client, callback: CallbackQuery):
    """معالج فتح الهمسة."""
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("خطأ", show_alert=True)
        return

    whisper_id = parts[2]
    result = await whisper_service.read_whisper(
        whisper_id,
        callback.from_user.id,
        callback.from_user.username,
    )

    if result["allowed"]:
        await callback.answer(
            f"💬 {result['message']}", show_alert=True,
        )
    else:
        await callback.answer(result["message"], show_alert=True)
