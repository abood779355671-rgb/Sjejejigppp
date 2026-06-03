handlers/memes/handlers.py
═══════════════════════════════════════════════════════════════
نظام الميمز والأصوات.
مكتبة أصوات تُخزَّن كـ file_id في قاعدة البيانات مع تصنيفات.
نعيد استخدام جدول replies بنوع خاص أو جدول منفصل.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from core.database import db
from utils.decorators import developers_only
from core.logger import setup_logger

logger = setup_logger("memes_handlers")


async def _ensure_memes_table():
    """إنشاء جدول الأصوات إن لم يوجد."""
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS sound_library (
            id          BIGSERIAL PRIMARY KEY,
            name        VARCHAR(128) NOT NULL,
            category    VARCHAR(64) DEFAULT 'عام',
            file_id     VARCHAR(255) NOT NULL,
            file_type   VARCHAR(20) DEFAULT 'voice',
            added_by    BIGINT,
            created_at  TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_sound_name ON sound_library(name);
        CREATE INDEX IF NOT EXISTS idx_sound_category ON sound_library(category);
        """
    )


@developers_only
async def add_sound_handler(client: Client, message: Message):
    """
    إضافة صوت للمكتبة (للمطورين).
    بالرد على صوت: اضف صوت <الاسم> [التصنيف]
    """
    reply = message.reply_to_message
    if not reply or not (reply.voice or reply.audio):
        await message.reply_text("❌ رد على رسالة صوتية")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply_text("❌ الاستخدام: اضف صوت <الاسم> [التصنيف]")
        return

    name_category = parts[2].split(maxsplit=1)
    name = name_category[0]
    category = name_category[1] if len(name_category) > 1 else "عام"

    file_id = reply.voice.file_id if reply.voice else reply.audio.file_id
    file_type = "voice" if reply.voice else "audio"

    await _ensure_memes_table()
    await db.execute(
        """
        INSERT INTO sound_library (name, category, file_id, file_type, added_by)
        VALUES ($1, $2, $3, $4, $5);
        """,
        name, category, file_id, file_type, message.from_user.id,
    )
    await message.reply_text(f"✅ تم إضافة الصوت: {name} ({category})")


async def search_sound_handler(client: Client, message: Message):
    """البحث عن صوت وإرساله. الاستخدام: صوت <الاسم>"""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return

    query = parts[1].strip()
    await _ensure_memes_table()

    record = await db.fetchrow(
        """
        SELECT file_id, file_type, name FROM sound_library
        WHERE name ILIKE $1 ORDER BY RANDOM() LIMIT 1;
        """,
        f"%{query}%",
    )
    if not record:
        await message.reply_text("❌ لم يتم العثور على الصوت")
        return

    try:
        if record["file_type"] == "voice":
            await message.reply_voice(record["file_id"])
        else:
            await message.reply_audio(record["file_id"])
    except Exception as e:
        logger.debug(f"فشل إرسال الصوت: {e}")


async def list_categories_handler(client: Client, message: Message):
    """قائمة تصنيفات الأصوات. الاستخدام: تصنيفات"""
    await _ensure_memes_table()
    rows = await db.fetch(
        "SELECT category, COUNT(*) as cnt FROM sound_library GROUP BY category;"
    )
    if not rows:
        await message.reply_text("لا توجد أصوات في المكتبة")
        return

    lines = ["🎵 <b>تصنيفات الأصوات</b>\n"]
    for row in rows:
        lines.append(f"• {row['category']}: {row['cnt']} صوت")
    await message.reply_text("\n".join(lines))
