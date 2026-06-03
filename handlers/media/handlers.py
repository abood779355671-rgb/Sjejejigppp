handlers/media/handlers.py
═══════════════════════════════════════════════════════════════
معالجات تحميل الوسائط من المنصات.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.media_service import media_service
from utils.decorators import rate_limited
from core.logger import setup_logger

logger = setup_logger("media_handlers")


@rate_limited("media_download", limit=3, seconds=60)
async def download_video_handler(client: Client, message: Message):
    """تحميل فيديو. الاستخدام: تحميل <الرابط>"""
    await _process_download(client, message, audio_only=False)


@rate_limited("media_download", limit=3, seconds=60)
async def download_audio_handler(client: Client, message: Message):
    """تحميل صوت. الاستخدام: صوت <الرابط>"""
    await _process_download(client, message, audio_only=True)


async def _process_download(client: Client, message: Message, audio_only: bool):
    """تنفيذ التحميل المشترك."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("❌ أرسل: تحميل <الرابط>")
        return

    url = parts[1].strip()
    if not media_service.is_supported(url):
        await message.reply_text(
            "❌ الرابط غير مدعوم.\n"
            "المنصات المدعومة: YouTube, TikTok, Instagram, "
            "Facebook, X, Pinterest, SoundCloud"
        )
        return

    status = await message.reply_text("⏳ جارٍ التحميل...")

    result = await media_service.download(url, audio_only=audio_only)
    if not result:
        await status.edit_text("❌ فشل التحميل (الملف كبير جداً أو غير متاح)")
        return

    try:
        await status.edit_text("📤 جارٍ الرفع...")
        if result["type"] == "audio":
            await message.reply_audio(
                result["file_path"], caption=f"🎵 {result['title']}",
            )
        else:
            await message.reply_video(
                result["file_path"], caption=f"🎥 {result['title']}",
            )
        await status.delete()
    except Exception as e:
        logger.debug(f"فشل رفع الوسائط: {e}")
        await status.edit_text("❌ فشل رفع الملف")
    finally:
        media_service.cleanup(result["file_path"])
