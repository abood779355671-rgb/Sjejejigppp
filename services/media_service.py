services/media_service.py
═══════════════════════════════════════════════════════════════
خدمة تحميل الوسائط من المنصات (YouTube/TikTok/Instagram/...).
تستخدم yt-dlp الذي يدعم مئات المواقع.
═══════════════════════════════════════════════════════════════
"""

import asyncio
import os
import tempfile
from typing import Optional

import yt_dlp

from core.logger import setup_logger

logger = setup_logger("media_service")


class MediaService:
    """خدمة تحميل الوسائط."""

    SUPPORTED_DOMAINS = [
        "youtube.com", "youtu.be", "tiktok.com", "instagram.com",
        "facebook.com", "fb.watch", "twitter.com", "x.com",
        "pinterest.com", "soundcloud.com",
    ]

    def is_supported(self, url: str) -> bool:
        """فحص ما إذا كان الرابط مدعوماً."""
        return any(domain in url.lower() for domain in self.SUPPORTED_DOMAINS)

    async def download(
        self, url: str, audio_only: bool = False, max_filesize_mb: int = 50,
    ) -> Optional[dict]:
        """
        تحميل وسائط من رابط.

        Returns:
            dict: {"file_path", "title", "type"} أو None.
        """
        # تشغيل yt-dlp في thread منفصل (غير متزامن)
        return await asyncio.to_thread(
            self._download_sync, url, audio_only, max_filesize_mb,
        )

    def _download_sync(
        self, url: str, audio_only: bool, max_filesize_mb: int,
    ) -> Optional[dict]:
        """التحميل الفعلي (متزامن، يُشغّل في thread)."""
        temp_dir = tempfile.mkdtemp(prefix="media_")
        max_bytes = max_filesize_mb * 1024 * 1024

        ydl_opts = {
            "outtmpl": os.path.join(temp_dir, "%(title).50s.%(ext)s"),
            "max_filesize": max_bytes,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
        }

        if audio_only:
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            ydl_opts["format"] = f"best[filesize<{max_filesize_mb}M]/best"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

                if audio_only:
                    base = os.path.splitext(file_path)[0]
                    file_path = base + ".mp3"

                if not os.path.exists(file_path):
                    return None

                return {
                    "file_path": file_path,
                    "title": info.get("title", "ملف"),
                    "type": "audio" if audio_only else "video",
                    "duration": info.get("duration", 0),
                }
        except Exception as e:
            logger.debug(f"فشل تحميل الوسائط: {e}")
            return None

    @staticmethod
    def cleanup(file_path: str) -> None:
        """حذف الملف المؤقت بعد الإرسال."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # حذف المجلد المؤقت
                parent = os.path.dirname(file_path)
                if os.path.isdir(parent):
                    os.rmdir(parent)
        except Exception as e:
            logger.debug(f"فشل حذف الملف المؤقت: {e}")


media_service = MediaService()
