core/client.py
═══════════════════════════════════════════════════════════════
تهيئة عميل Pyrogram.
نستخدم فئة فرعية مخصصة لإضافة سلوك خاص عند الإقلاع.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client

from config.settings import settings
from core.logger import setup_logger

logger = setup_logger("client")


class BotClient(Client):
    """
    عميل البوت المخصص.
    يرث من Pyrogram Client مع إعدادات الإنتاج.
    """

    def __init__(self) -> None:
        super().__init__(
            name="bot",                      # اسم ملف الجلسة (bot.session)
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            bot_token=settings.BOT_TOKEN,
            workers=settings.WORKERS,        # عدد المعالجات المتوازية
            plugins=None,                    # سنسجّل المعالجات يدوياً
            sleep_threshold=60,              # مهلة قبل رفع FloodWait
            max_concurrent_transmissions=4,  # رفع/تنزيل متزامن
        )
        # كائن معلومات البوت (يُملأ بعد الإقلاع)
        self.bot_info = None

    async def start(self, *args, **kwargs):
        """تجاوز الإقلاع لجلب معلومات البوت."""
        await super().start(*args, **kwargs)
        self.bot_info = await self.get_me()
        logger.info(
            f"✅ تم تشغيل البوت: @{self.bot_info.username} "
            f"(ID: {self.bot_info.id})"
        )
        return self

    async def stop(self, *args, **kwargs):
        """تجاوز الإيقاف للتسجيل."""
        logger.info("جارٍ إيقاف البوت...")
        await super().stop(*args, **kwargs)
        logger.info("تم إيقاف البوت")


# نسخة Singleton جاهزة
bot = BotClient()
