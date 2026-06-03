core/error_handler.py
═══════════════════════════════════════════════════════════════
معالج الأخطاء العام (Global Error Handler).
يلتقط كل استثناء غير معالَج، يسجّله، ولا يكشف تفاصيله للمستخدم.
═══════════════════════════════════════════════════════════════
"""

import functools
import traceback
from typing import Callable

from pyrogram.types import Message, CallbackQuery

from database.repositories.log_repo import log_repo
from core.exceptions import BotException
from core.logger import setup_logger

logger = setup_logger("error_handler")


def safe_handler(handler: Callable):
    """
    Decorator يغلّف أي معالج بحماية شاملة من الأخطاء.
    - أخطاء BotException: تُعرض رسالتها العربية للمستخدم.
    - الأخطاء الأخرى: تُسجَّل ولا تُكشف.
    """
    @functools.wraps(handler)
    async def wrapper(client, update, *args, **kwargs):
        try:
            return await handler(client, update, *args, **kwargs)
        except BotException as e:
            # خطأ معروف، نعرض رسالته
            await _notify_user(update, f"❌ {e.message}")
        except Exception as e:
            # خطأ غير متوقع
            tb = traceback.format_exc()
            logger.error(f"خطأ غير معالَج في {handler.__name__}: {e}\n{tb}")

            chat_id = None
            user_id = None
            try:
                if isinstance(update, CallbackQuery):
                    user_id = update.from_user.id
                    chat_id = update.message.chat.id if update.message else None
                elif isinstance(update, Message):
                    user_id = update.from_user.id if update.from_user else None
                    chat_id = update.chat.id
            except Exception:
                pass

            # تسجيل الخطأ في قاعدة البيانات
            await log_repo.log_error(
                error_type=type(e).__name__,
                message=str(e),
                traceback=tb,
                chat_id=chat_id,
                user_id=user_id,
            )
            await _notify_user(update, "❌ حدث خطأ، تم تسجيله وسيُراجَع")

    return wrapper


async def _notify_user(update, text: str) -> None:
    """إبلاغ المستخدم بالخطأ بأمان."""
    try:
        if isinstance(update, CallbackQuery):
            await update.answer(text, show_alert=True)
        elif isinstance(update, Message):
            await update.reply_text(text)
    except Exception:
        pass
