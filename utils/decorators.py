utils/decorators.py
═══════════════════════════════════════════════════════════════
المُزخرفات (Decorators) لحماية المعالجات.

- @require_permission: يتطلب صلاحية معينة.
- @require_rank: يتطلب رتبة دنيا.
- @developers_only: للمطورين فقط.
- @main_developer_only: للمطور الأساسي فقط.
- @group_only / @private_only: تقييد نوع المحادثة.
- @rate_limited: تحديد معدل الاستخدام.

كل decorator يستخرج السياق، يفحص الشرط، ويرد برسالة عربية عند الرفض.
═══════════════════════════════════════════════════════════════
"""

import functools
from typing import Callable, Union

from pyrogram import Client
from pyrogram.types import Message, CallbackQuery

from services.permission_service import permission_service
from database.repositories.user_repo import user_repo
from config.constants import RedisKeys, RANK_NAMES_AR, RankLevel
from core.redis_client import redis_client
from core.logger import setup_logger
from utils.context import RequestContext

logger = setup_logger("decorators")


# ───────────────────────────────────────────────
# دالة مساعدة للرد على المستخدم (تعمل مع النوعين)
# ───────────────────────────────────────────────
async def _reply(update: Union[Message, CallbackQuery], text: str) -> None:
    """الرد على المستخدم سواء كان Message أو CallbackQuery."""
    try:
        if isinstance(update, CallbackQuery):
            await update.answer(text, show_alert=True)
        else:
            await update.reply_text(text, quote=True)
    except Exception as e:
        logger.error(f"فشل الرد على المستخدم: {e}")


# ═══════════════════════════════════════════════════════════════
# @require_permission
# ═══════════════════════════════════════════════════════════════
def require_permission(permission: str):
    """
    Decorator يتطلب صلاحية معينة من PERMISSION_MATRIX.

    الاستخدام:
        @require_permission("ban")
        async def ban_handler(client, message): ...
    """
    def decorator(handler: Callable):
        @functools.wraps(handler)
        async def wrapper(client: Client, update: Union[Message, CallbackQuery], *args, **kwargs):
            ctx = RequestContext.from_update(update)
            if ctx is None:
                return

            allowed = await permission_service.has_permission(
                ctx.chat_id, ctx.user_id, permission
            )
            if not allowed:
                await _reply(update, "❌ ليس لديك صلاحية كافية لتنفيذ هذا الأمر")
                return

            return await handler(client, update, *args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════
# @require_rank
# ═══════════════════════════════════════════════════════════════
def require_rank(min_level: int):
    """
    Decorator يتطلب رتبة دنيا.

    الاستخدام:
        @require_rank(RankLevel.ADMIN)
        async def handler(client, message): ...
    """
    def decorator(handler: Callable):
        @functools.wraps(handler)
        async def wrapper(client: Client, update: Union[Message, CallbackQuery], *args, **kwargs):
            ctx = RequestContext.from_update(update)
            if ctx is None:
                return

            user_level = await permission_service.get_user_rank(
                ctx.chat_id, ctx.user_id
            )
            if user_level < min_level:
                rank_name = RANK_NAMES_AR.get(RankLevel(min_level), "أعلى")
                await _reply(
                    update,
                    f"❌ هذا الأمر يتطلب رتبة ({rank_name}) على الأقل",
                )
                return

            return await handler(client, update, *args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════
# @developers_only
# ═══════════════════════════════════════════════════════════════
def developers_only(handler: Callable):
    """
    Decorator يقصر الأمر على المطورين (أساسي أو ثانوي).

    الاستخدام:
        @developers_only
        async def handler(client, message): ...
    """
    @functools.wraps(handler)
    async def wrapper(client: Client, update: Union[Message, CallbackQuery], *args, **kwargs):
        ctx = RequestContext.from_update(update)
        if ctx is None:
            return

        if not await user_repo.is_developer(ctx.user_id):
            await _reply(update, "❌ هذا الأمر مخصص للمطورين فقط")
            return

        return await handler(client, update, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════
# @main_developer_only
# ═══════════════════════════════════════════════════════════════
def main_developer_only(handler: Callable):
    """
    Decorator يقصر الأمر على المطور الأساسي فقط.
    يُستخدم لإدارة المطورين (إضافة/حذف مطور).
    """
    @functools.wraps(handler)
    async def wrapper(client: Client, update: Union[Message, CallbackQuery], *args, **kwargs):
        ctx = RequestContext.from_update(update)
        if ctx is None:
            return

        if not await user_repo.is_main_developer(ctx.user_id):
            await _reply(update, "❌ هذا الأمر مخصص للمطور الأساسي فقط")
            return

        return await handler(client, update, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════
# @group_only
# ═══════════════════════════════════════════════════════════════
def group_only(handler: Callable):
    """Decorator يقصر الأمر على المجموعات فقط."""
    @functools.wraps(handler)
    async def wrapper(client: Client, update: Union[Message, CallbackQuery], *args, **kwargs):
        ctx = RequestContext.from_update(update)
        if ctx is None:
            return

        if not ctx.is_group:
            await _reply(update, "❌ هذا الأمر يعمل داخل المجموعات فقط")
            return

        return await handler(client, update, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════
# @private_only
# ═══════════════════════════════════════════════════════════════
def private_only(handler: Callable):
    """Decorator يقصر الأمر على المحادثة الخاصة فقط."""
    @functools.wraps(handler)
    async def wrapper(client: Client, update: Union[Message, CallbackQuery], *args, **kwargs):
        ctx = RequestContext.from_update(update)
        if ctx is None:
            return

        if not ctx.is_private:
            await _reply(update, "❌ هذا الأمر يعمل في الخاص فقط")
            return

        return await handler(client, update, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════
# @rate_limited
# ═══════════════════════════════════════════════════════════════
def rate_limited(action: str, limit: int = 5, seconds: int = 10):
    """
    Decorator لتحديد معدل استخدام أمر معين.

    الاستخدام:
        @rate_limited("download", limit=3, seconds=60)
        async def download_handler(client, message): ...

    Args:
        action: اسم الإجراء (لبناء مفتاح Redis).
        limit: العدد المسموح.
        seconds: خلال كم ثانية.
    """
    def decorator(handler: Callable):
        @functools.wraps(handler)
        async def wrapper(client: Client, update: Union[Message, CallbackQuery], *args, **kwargs):
            ctx = RequestContext.from_update(update)
            if ctx is None:
                return

            # المطورون معفون من حدود المعدل
            if await user_repo.is_developer(ctx.user_id):
                return await handler(client, update, *args, **kwargs)

            key = RedisKeys.rate_limit(ctx.user_id, action)
            current = await redis_client.incr_with_expire(key, seconds)

            if current > limit:
                ttl = await redis_client.ttl(key)
                await _reply(
                    update,
                    f"⏳ لقد تجاوزت الحد المسموح، انتظر {ttl} ثانية",
                )
                return

            return await handler(client, update, *args, **kwargs)
        return wrapper
    return decorator
