handlers/content/commands_map.py
═══════════════════════════════════════════════════════════════
خريطة أوامر المحتوى العربية (ردود/فلاتر/أوامر).
═══════════════════════════════════════════════════════════════
"""

import re
from pyrogram import filters

from handlers.content import handlers as content
from handlers.welcome import handlers as welcome


def arabic_command(words: list[str]):
    """فلتر يطابق كلمة عربية في بداية الرسالة."""
    escaped = "|".join(re.escape(w) for w in words)
    pattern = rf"^({escaped})(\s|$)"
    return filters.text & filters.regex(pattern)


# ملاحظة: الأوامر الأطول والأكثر تحديداً أولاً
CONTENT_COMMANDS = [
    # ─── الردود ───
    (arabic_command(["اضف رد منطقي", "أضف رد منطقي"]), content.add_regex_reply_handler),
    (arabic_command(["اضف رد", "أضف رد"]),              content.add_reply_handler),
    (arabic_command(["حذف رد", "مسح رد"]),              content.delete_reply_handler),
    (arabic_command(["الردود", "قائمة الردود"]),        content.list_replies_handler),

    # ─── الفلاتر ───
    (arabic_command(["اضف فلتر", "أضف فلتر"]),          content.add_filter_handler),
    (arabic_command(["حذف فلتر", "مسح فلتر"]),          content.delete_filter_handler),
    (arabic_command(["الفلاتر", "قائمة الفلاتر"]),      content.list_filters_handler),

    # ─── الأوامر المخصصة ───
    (arabic_command(["اضف امر", "أضف أمر", "اضف أمر"]), content.add_command_handler),
    (arabic_command(["حذف امر", "حذف أمر"]),            content.delete_command_handler),
    (arabic_command(["الاوامر", "الأوامر المخصصة"]),   content.list_commands_handler),

    # ─── الترحيب ───
    (arabic_command(["ضع ترحيب", "تعيين ترحيب"]),       welcome.set_welcome_handler),
    (arabic_command(["ضع قوانين", "تعيين قوانين"]),     welcome.set_rules_handler),
    (arabic_command(["القوانين", "قوانين"]),            welcome.show_rules_handler),
    (arabic_command(["ضع مغادرة", "تعيين مغادرة"]),     welcome.set_goodbye_handler),
    (arabic_command(["تفعيل الترحيب", "تعطيل الترحيب"]), welcome.toggle_welcome_handler),
]
