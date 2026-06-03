handlers/common.py
═══════════════════════════════════════════════════════════════
المعالجات العامة: /start و /help.
═══════════════════════════════════════════════════════════════
"""

from pyrogram import Client
from pyrogram.types import Message

from locales.ar import messages
from utils.context import RequestContext


async def start_handler(client: Client, message: Message):
    """معالج /start."""
    ctx = RequestContext.from_update(message)
    if ctx and ctx.is_private:
        name = message.from_user.first_name or "صديقي"
        await message.reply_text(messages.START_PRIVATE.format(name=name))
    else:
        await message.reply_text(messages.START_GROUP)


async def help_handler(client: Client, message: Message):
    """معالج /help."""
    await message.reply_text(messages.HELP)
