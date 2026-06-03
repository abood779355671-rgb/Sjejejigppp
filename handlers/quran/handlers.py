handlers/quran/handlers.py
═══════════════════════════════════════════════════════════════
معالجات القرآن والأذكار وأوقات الصلاة.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from services.quran_service import quran_service
from utils.decorators import rate_limited
from core.logger import setup_logger

logger = setup_logger("quran_handlers")


@rate_limited("quran", limit=5, seconds=30)
async def surah_handler(client: Client, message: Message):
    """جلب سورة. الاستخدام: سورة <الرقم>"""
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply_text("❌ أرسل: سورة <رقم السورة 1-114>")
        return

    surah_num = int(parts[1])
    status = await message.reply_text("⏳ جارٍ الجلب...")
    surah = await quran_service.get_surah(surah_num)

    if not surah:
        await status.edit_text("❌ لم يتم العثور على السورة")
        return

    name = surah.get("name", "")
    ayahs = surah.get("ayahs", [])
    text = f"📖 <b>سورة {name}</b>\n\n"
    for ayah in ayahs[:20]:  # أول 20 آية لتجنب الطول
        text += f"{ayah['text']} ﴿{ayah['numberInSurah']}﴾ "

    if len(text) > 4000:
        text = text[:4000] + "..."
    await status.edit_text(text)


async def random_ayah_handler(client: Client, message: Message):
    """آية عشوائية. الاستخدام: آية"""
    ayah = await quran_service.get_random_ayah()
    if not ayah:
        await message.reply_text("❌ تعذّر الجلب")
        return

    surah_name = ayah.get("surah", {}).get("name", "")
    text = f"📖 {ayah['text']}\n\n— سورة {surah_name}، آية {ayah.get('numberInSurah', '')}"
    await message.reply_text(text)


async def zikr_handler(client: Client, message: Message):
    """ذكر عشوائي. الاستخدام: ذكر"""
    zikr = quran_service.get_random_zikr()
    await message.reply_text(f"📿 {zikr}")


async def prayer_times_handler(client: Client, message: Message):
    """أوقات الصلاة. الاستخدام: صلاة <المدينة>"""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("❌ أرسل: صلاة <اسم المدينة>")
        return

    city = parts[1].strip()
    timings = await quran_service.get_prayer_times(city)
    if not timings:
        await message.reply_text("❌ لم يتم العثور على المدينة")
        return

    text = (
        f"🕌 <b>أوقات الصلاة - {city}</b>\n\n"
        f"الفجر: {timings.get('Fajr')}\n"
        f"الشروق: {timings.get('Sunrise')}\n"
        f"الظهر: {timings.get('Dhuhr')}\n"
        f"العصر: {timings.get('Asr')}\n"
        f"المغرب: {timings.get('Maghrib')}\n"
        f"العشاء: {timings.get('Isha')}"
    )
    await message.reply_text(text)
