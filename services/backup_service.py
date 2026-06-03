services/backup_service.py
═══════════════════════════════════════════════════════════════
خدمة النسخ الاحتياطي والاستعادة باستخدام pg_dump/pg_restore.
يرسل النسخة إلى قناة النسخ الاحتياطي على تيليجرام.
═══════════════════════════════════════════════════════════════
"""

import asyncio
import os
import gzip
import tempfile
from datetime import datetime

from pyrogram import Client

from config.settings import settings
from core.logger import setup_logger

logger = setup_logger("backup_service")


class BackupService:
    """خدمة النسخ الاحتياطي."""

    async def create_backup(self) -> str:
        """
        إنشاء نسخة احتياطية مضغوطة من قاعدة البيانات.

        Returns:
            مسار ملف النسخة المضغوط.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = tempfile.gettempdir()
        sql_file = os.path.join(temp_dir, f"backup_{timestamp}.sql")
        gz_file = sql_file + ".gz"

        # تنفيذ pg_dump
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

        cmd = [
            "pg_dump",
            "-h", settings.POSTGRES_HOST,
            "-p", str(settings.POSTGRES_PORT),
            "-U", settings.POSTGRES_USER,
            "-d", settings.POSTGRES_DB,
            "-f", sql_file,
            "--no-owner", "--no-acl",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"فشل pg_dump: {stderr.decode()}")
            raise Exception("فشل إنشاء النسخة الاحتياطية")

        # ضغط الملف
        await asyncio.to_thread(self._compress, sql_file, gz_file)
        os.remove(sql_file)

        logger.info(f"تم إنشاء نسخة احتياطية: {gz_file}")
        return gz_file

    @staticmethod
    def _compress(src: str, dst: str) -> None:
        """ضغط ملف بـ gzip."""
        with open(src, "rb") as f_in:
            with gzip.open(dst, "wb") as f_out:
                f_out.writelines(f_in)

    async def send_backup_to_channel(self, client: Client) -> bool:
        """إنشاء نسخة وإرسالها لقناة النسخ الاحتياطي."""
        if not settings.BACKUP_CHANNEL_ID:
            logger.warning("لم يُحدّد BACKUP_CHANNEL_ID")
            return False

        try:
            backup_file = await self.create_backup()
            await client.send_document(
                settings.BACKUP_CHANNEL_ID,
                backup_file,
                caption=f"💾 نسخة احتياطية\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )
            os.remove(backup_file)
            return True
        except Exception as e:
            logger.error(f"فشل إرسال النسخة الاحتياطية: {e}")
            return False

    async def restore_backup(self, gz_file_path: str) -> bool:
        """
        استعادة نسخة احتياطية.
        تحذير: يستبدل البيانات الحالية.
        """
        sql_file = gz_file_path.replace(".gz", "")
        try:
            # فك الضغط
            await asyncio.to_thread(self._decompress, gz_file_path, sql_file)

            env = os.environ.copy()
            env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

            cmd = [
                "psql",
                "-h", settings.POSTGRES_HOST,
                "-p", str(settings.POSTGRES_PORT),
                "-U", settings.POSTGRES_USER,
                "-d", settings.POSTGRES_DB,
                "-f", sql_file,
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd, env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            os.remove(sql_file)

            if process.returncode != 0:
                logger.error(f"فشل الاستعادة: {stderr.decode()}")
                return False
            return True
        except Exception as e:
            logger.error(f"فشل استعادة النسخة: {e}")
            return False

    @staticmethod
    def _decompress(src: str, dst: str) -> None:
        """فك ضغط gzip."""
        with gzip.open(src, "rb") as f_in:
            with open(dst, "wb") as f_out:
                f_out.writelines(f_in)


backup_service = BackupService()
