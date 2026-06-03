handlers/welcome/handlers.py
═══════════════════════════════════════════════════════════════
معالجات الترحيب والمغادرة + أوامر الإعداد.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.welcome_service import welcome_service
from database.repositories.welcome_repo import welcome_repo
from utils.decorators import group_only, require_permission
from core.redis_client import redis_client
from core.logger import setup_logger

logger = setup_logger("welcome_handlers")


# ═══════════════════════════════════════════════════════════════
# معالج الأعضاء الجدد والمغادرين
# ═══════════════════════════════════════════════════════════════
async def new_member_handler(client: Client, message: Message):
    """ترحيب بالأعضاء الجدد."""
    if not message.new_chat_members:
        return

    chat_id = message.chat.id
    chat_title = message.chat.title or ""
    members_count = await client.get_chat_members_count(chat_id)

    for member in message.new_chat_members:
        if member.is_bot:
            continue  # لا نرحّب بالبوتات
        await welcome_service.send_welcome(
            client, chat_id, member, chat_title, members_count,
        )


async def left_member_handler(client: Client, message: Message):
    """وداع للأعضاء المغادرين."""
    if not message.left_chat_member:
        return
    if message.left_chat_member.is_bot:
        return

    await welcome_service.send_goodbye(
        client, message.chat.id, message.left_chat_member,
        message.chat.title or "",
    )


# ═══════════════════════════════════════════════════════════════
# أوامر إعداد الترحيب
# ═══════════════════════════════════════════════════════════════
@group_only
@require_permission("manage_welcome")
async def set_welcome_handler(client: Client, message: Message):
    """
    تعيين رسالة الترحيب.
    الاستخدام: "ضع ترحيب <النص>" أو بالرد على وسائط.
    """
    chat_id = message.chat.id

    # إن كان رداً على صورة/فيديو، نحفظها كوسائط ترحيب
    reply = message.reply_to_message
    if reply and (reply.photo or reply.video):
        if reply.photo:
            await welcome_repo.set_welcome_media(chat_id, "photo", reply.photo.file_id)
        elif reply.video:
            await welcome_repo.set_welcome_media(chat_id, "video", reply.video.file_id)
        caption = reply.caption or message.text.split(maxsplit=2)[-1] if len(message.text.split()) > 2 else None
        if caption:
            await welcome_repo.set_welcome_text(chat_id, caption)
        await message.reply_text("✅ تم تعيين وسائط ونص الترحيب")
        return

    # نص فقط
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text(
            "❌ الاستخدام: ضع ترحيب <النص>\n\n"
            "المتغيرات: {name} {mention} {group} {count} {id}"
        )
        return

    text = parts[2]
    await welcome_repo.set_welcome_text(chat_id, text)
    await message.reply_text("✅ تم تعيين رسالة الترحيب")


@group_only
@require_permission("manage_welcome")
async def set_rules_handler(client: Client, message: Message):
    """تعيين قوانين المجموعة."""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("❌ الاستخدام: ضع قوانين <النص>")
        return
    await welcome_repo.set_rules(message.chat.id, parts[2])
    await message.reply_text("✅ تم تعيين القوانين")


@group_only
async def show_rules_handler(client: Client, message: Message):
    """عرض قوانين المجموعة."""
    settings_data = await welcome_repo.get_settings(message.chat.id)
    rules = settings_data.get("rules_text")
    if rules:
        await message.reply_text(f"📜 <b>قوانين المجموعة</b>\n\n{rules}")
    else:
        await message.reply_text("لا توجد قوانين معيّنة")


@group_only
@require_permission("manage_welcome")
async def set_goodbye_handler(client: Client, message: Message):
    """تعيين رسالة المغادرة."""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("❌ الاستخدام: ضع مغادرة <النص>")
        return
    await welcome_repo.set_goodbye(message.chat.id, parts[2], enabled=True)
    await message.reply_text("✅ تم تعيين رسالة المغادرة")


@group_only
@require_permission("manage_welcome")
async def toggle_welcome_handler(client: Client, message: Message):
    """تفعيل/تعطيل الترحيب."""
    text = message.text.strip()
    enabled = "تفعيل" in text
    await welcome_repo.toggle_welcome(message.chat.id, enabled)
    status = "تفعيل" if enabled else "تعطيل"
    await message.reply_text(f"✅ تم {status} الترحيب")
