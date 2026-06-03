handlers/admin/commands_map.py
═══════════════════════════════════════════════════════════════
خريطة الأوامر العربية الطبيعية لمعالجاتها.
نستخدم filters.regex لمطابقة الكلمات العربية في بداية الرسالة.
═══════════════════════════════════════════════════════════════
"""

import re

from pyrogram import filters

from handlers.admin import ranks, moderation


def arabic_command(words: list[str]):
    """
    إنشاء فلتر يطابق كلمة عربية في بداية الرسالة.
    مثال: arabic_command(["حظر", "بان"]) يطابق "حظر @user".
    """
    # نبني نمطاً يطابق أي من الكلمات في البداية
    escaped = "|".join(re.escape(w) for w in words)
    pattern = rf"^({escaped})(\s|$)"
    return filters.text & filters.regex(pattern)


# ═══════════════════════════════════════════════════════════════
# خريطة الأوامر: (الفلتر, المعالج)
# ═══════════════════════════════════════════════════════════════
ADMIN_COMMANDS = [
    # ─── الرتب: رفع ───
    (arabic_command(["رفع مميز", "تمييز"]),        ranks.promote_vip_handler),
    (arabic_command(["رفع ادمن", "رفع أدمن"]),      ranks.promote_admin_handler),
    (arabic_command(["رفع مدير"]),                  ranks.promote_manager_handler),
    (arabic_command(["رفع مالك اساسي", "رفع مالك أساسي"]), ranks.promote_main_owner_handler),
    (arabic_command(["رفع مالك"]),                  ranks.promote_owner_handler),

    # ─── الرتب: تنزيل ───
    (arabic_command(["تنزيل مميز"]),                ranks.demote_vip_handler),
    (arabic_command(["تنزيل ادمن", "تنزيل أدمن"]),  ranks.demote_admin_handler),
    (arabic_command(["تنزيل مدير"]),                ranks.demote_manager_handler),
    (arabic_command(["تنزيل مالك اساسي", "تنزيل مالك أساسي"]), ranks.demote_main_owner_handler),
    (arabic_command(["تنزيل مالك"]),                ranks.demote_owner_handler),

    # ─── الإدارة ───
    (arabic_command(["حظر", "بان"]),                moderation.ban_handler),
    (arabic_command(["فك حظر", "الغاء حظر"]),       moderation.unban_handler),
    (arabic_command(["كتم"]),                       moderation.mute_handler),
    (arabic_command(["فك كتم", "الغاء كتم"]),       moderation.unmute_handler),
    (arabic_command(["تقييد"]),                     moderation.restrict_handler),
    (arabic_command(["فك تقييد", "الغاء تقييد"]),   moderation.unrestrict_handler),
    (arabic_command(["طرد"]),                       moderation.kick_handler),
    (arabic_command(["تثبيت"]),                     moderation.pin_handler),
    (arabic_command(["الغاء تثبيت", "إلغاء تثبيت"]), moderation.unpin_handler),
    (arabic_command(["مسح", "حذف"]),                moderation.purge_handler),
]
