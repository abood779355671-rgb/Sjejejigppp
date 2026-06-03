handlers/content/handlers.py
═══════════════════════════════════════════════════════════════
معالجات إضافة/حذف الردود والفلاتر والأوامر المخصصة،
ومعالج المطابقة التلقائية.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.reply_service import reply_service
from services.filter_service import filter_service
from database.repositories.reply_repo import reply_repo
from database.repositories.filter_command_repo import filter_repo, command_repo
from utils.decorators import group_only, require_permission
from config.constants import MatchType, ReplyType
from utils.validators import validators
from core.exceptions import ValidationError
from core.logger import setup_logger

logger = setup_logger("content_handlers")


# ═══════════════════════════════════════════════════════════════
# إضافة رد
# ═══════════════════════════════════════════════════════════════
@group_only
@require_permission("manage_replies")
async def add_reply_handler(client: Client, message: Message):
    """
    إضافة رد. الاستخدام:
    "اضف رد <المحفّز> <الرد>" (نصي)
    أو بالرد على وسائط: "اضف رد <المحفّز>"
    """
    chat_id = message.chat.id
    reply = message.reply_to_message

    # رد على وسائط
    if reply:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.reply_text("❌ الاستخدام: اضف رد <الكلمة> (بالرد على الوسائط)")
            return
        trigger = parts[2].strip()

        if reply.photo:
            await reply_repo.add_reply(
                chat_id, trigger, MatchType.CONTAINS.value, ReplyType.PHOTO.value,
                media_file_id=reply.photo.file_id, created_by=message.from_user.id,
            )
        elif reply.video:
            await reply_repo.add_reply(
                chat_id, trigger, MatchType.CONTAINS.value, ReplyType.VIDEO.value,
                media_file_id=reply.video.file_id, created_by=message.from_user.id,
            )
        elif reply.animation:
            await reply_repo.add_reply(
                chat_id, trigger, MatchType.CONTAINS.value, ReplyType.GIF.value,
                media_file_id=reply.animation.file_id, created_by=message.from_user.id,
            )
        elif reply.voice or reply.audio:
            fid = reply.voice.file_id if reply.voice else reply.audio.file_id
            await reply_repo.add_reply(
                chat_id, trigger, MatchType.CONTAINS.value, ReplyType.AUDIO.value,
                media_file_id=fid, created_by=message.from_user.id,
            )
        else:
            await message.reply_text("❌ نوع وسائط غير مدعوم")
            return
        await message.reply_text(f"✅ تم إضافة رد وسائط للكلمة: {trigger}")
        return

    # رد نصي: اضف رد <المحفّز> <الرد>
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.reply_text("❌ الاستخدام: اضف رد <الكلمة> <الرد>")
        return
    trigger = parts[2].strip()
    content = parts[3].strip()
    await reply_repo.add_reply(
        chat_id, trigger, MatchType.CONTAINS.value, ReplyType.TEXT.value,
        content=content, created_by=message.from_user.id,
    )
    await message.reply_text(f"✅ تم إضافة رد للكلمة: {trigger}")


@group_only
@require_permission("manage_replies")
async def delete_reply_handler(client: Client, message: Message):
    """حذف رد. الاستخدام: حذف رد <الكلمة>"""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("❌ الاستخدام: حذف رد <الكلمة>")
        return
    trigger = parts[2].strip()
    count = await reply_repo.delete_by_trigger(message.chat.id, trigger)
    if count:
        await message.reply_text(f"✅ تم حذف {count} رد")
    else:
        await message.reply_text("❌ لا يوجد رد بهذه الكلمة")


@group_only
async def list_replies_handler(client: Client, message: Message):
    """عرض قائمة الردود."""
    replies = await reply_repo.list_replies(message.chat.id)
    if not replies:
        await message.reply_text("لا توجد ردود")
        return
    lines = ["📋 <b>الردود</b>\n"]
    for r in replies:
        lines.append(f"• {r['trigger_text']} ({r['reply_type']})")
    await message.reply_text("\n".join(lines))


# ═══════════════════════════════════════════════════════════════
# الفلاتر
# ═══════════════════════════════════════════════════════════════
@group_only
@require_permission("manage_filters")
async def add_filter_handler(client: Client, message: Message):
    """إضافة فلتر. الاستخدام: اضف فلتر <الكلمة>"""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("❌ الاستخدام: اضف فلتر <الكلمة>")
        return
    word = parts[2].strip()
    await filter_repo.add_filter(message.chat.id, word)
    await message.reply_text(f"✅ تم إضافة الفلتر: {word}")


@group_only
@require_permission("manage_filters")
async def delete_filter_handler(client: Client, message: Message):
    """حذف فلتر. الاستخدام: حذف فلتر <الكلمة>"""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("❌ الاستخدام: حذف فلتر <الكلمة>")
        return
    word = parts[2].strip()
    count = await filter_repo.delete_filter(message.chat.id, word)
    if count:
        await message.reply_text(f"✅ تم حذف الفلتر")
    else:
        await message.reply_text("❌ لا يوجد فلتر بهذه الكلمة")


@group_only
async def list_filters_handler(client: Client, message: Message):
    """عرض قائمة الفلاتر."""
    filters_list = await filter_repo.list_filters(message.chat.id)
    if not filters_list:
        await message.reply_text("لا توجد فلاتر")
        return
    lines = ["🚫 <b>الفلاتر</b>\n"]
    for f in filters_list:
        lines.append(f"• {f['filter_word']}")
    await message.reply_text("\n".join(lines))


# ═══════════════════════════════════════════════════════════════
# الأوامر المخصصة
# ═══════════════════════════════════════════════════════════════
@group_only
@require_permission("manage_commands")
async def add_command_handler(client: Client, message: Message):
    """إضافة أمر مخصص. الاستخدام: اضف امر <الأمر> <الرد>"""
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.reply_text("❌ الاستخدام: اضف امر <الأمر> <الرد>")
        return
    command = parts[2].strip()
    response = parts[3].strip()
    await command_repo.add_command(
        message.chat.id, command, response=response, created_by=message.from_user.id,
    )
    await message.reply_text(f"✅ تم إضافة الأمر: {command}")


@group_only
@require_permission("manage_commands")
async def delete_command_handler(client: Client, message: Message):
    """حذف أمر مخصص. الاستخدام: حذف امر <الأمر>"""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("❌ الاستخدام: حذف امر <الأمر>")
        return
    command = parts[2].strip()
    deleted = await command_repo.delete_command(message.chat.id, command)
    if deleted:
        await message.reply_text("✅ تم حذف الأمر")
    else:
        await message.reply_text("❌ لا يوجد أمر بهذا الاسم")


# ═══════════════════════════════════════════════════════════════
# معالج المطابقة التلقائية (الفلاتر ثم الأوامر ثم الردود)
# ═══════════════════════════════════════════════════════════════
async def auto_content_handler(client: Client, message: Message):
    """
    معالج المحتوى التلقائي على رسائل المجموعات:
    1. فحص الفلاتر (حذف إن خالف).
    2. فحص الأوامر المخصصة.
    3. فحص الردود.
    """
    from pyrogram import StopPropagation

    # 1. الفلاتر
    if await filter_service.check_message(client, message):
        raise StopPropagation

    text = message.text or message.caption
    if not text:
        return

    # 2. الأوامر المخصصة (الكلمة الأولى)
    first_word = text.split()[0].lower().strip() if text.split() else ""
    cmd = await command_repo.get_command(message.chat.id, first_word)
    if cmd:
        if cmd.get("media_file_id"):
            try:
                await message.send_cached_media(cmd["media_file_id"], caption=cmd.get("response") or "")
            except Exception:
                await message.reply_text(cmd.get("response") or "")
        else:
            await message.reply_text(cmd.get("response") or "")
        return

    # 3. الردود التلقائية
    await reply_service.find_and_send(client, message)
