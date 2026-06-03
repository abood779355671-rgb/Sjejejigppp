services/quran_service.py
═══════════════════════════════════════════════════════════════
خدمة القرآن الكريم وأوقات الصلاة والأذكار.
تستخدم APIs عامة (alquran.cloud / aladhan).
═══════════════════════════════════════════════════════════════
"""

import random
from typing import Optional

import aiohttp

from core.logger import setup_logger

logger = setup_logger("quran_service")

QURAN_API = "https://api.alquran.cloud/v1"
PRAYER_API = "https://api.aladhan.com/v1"


class QuranService:
    """خدمة القرآن."""

    # أذكار مختارة
    AZKAR = [
        "سبحان الله وبحمده، سبحان الله العظيم",
        "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير",
        "أستغفر الله العظيم وأتوب إليه",
        "اللهم صلِّ وسلم على نبينا محمد",
        "لا حول ولا قوة إلا بالله",
        "حسبي الله ونعم الوكيل",
        "اللهم إنك عفو تحب العفو فاعفُ عني",
    ]

    async def _fetch(self, url: str) -> Optional[dict]:
        """طلب HTTP غير متزامن."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.debug(f"فشل طلب API: {e}")
        return None

    async def get_surah(self, surah_number: int) -> Optional[dict]:
        """جلب سورة كاملة برقمها."""
        if not 1 <= surah_number <= 114:
            return None
        data = await self._fetch(f"{QURAN_API}/surah/{surah_number}/ar.alafasy")
        if data and data.get("code") == 200:
            return data["data"]
        return None

    async def get_random_ayah(self) -> Optional[dict]:
        """جلب آية عشوائية."""
        ayah_number = random.randint(1, 6236)  # إجمالي آيات القرآن
        data = await self._fetch(f"{QURAN_API}/ayah/{ayah_number}/ar.asad")
        if data and data.get("code") == 200:
            return data["data"]
        return None

    async def get_tafsir(self, surah: int, ayah: int) -> Optional[str]:
        """جلب تفسير آية."""
        data = await self._fetch(f"{QURAN_API}/ayah/{surah}:{ayah}/ar.muyassar")
        if data and data.get("code") == 200:
            return data["data"].get("text")
        return None

    async def get_prayer_times(self, city: str, country: str = "SA") -> Optional[dict]:
        """جلب أوقات الصلاة لمدينة."""
        url = f"{PRAYER_API}/timingsByCity?city={city}&country={country}&method=4"
        data = await self._fetch(url)
        if data and data.get("code") == 200:
            return data["data"]["timings"]
        return None

    def get_random_zikr(self) -> str:
        """ذكر عشوائي."""
        return random.choice(self.AZKAR)


quran_service = QuranService()
