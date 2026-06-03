keyboards/developer_kb.py
═══════════════════════════════════════════════════════════════
لوحات الأزرار التفاعلية (Inline) للوحة المطور.
نستخدم callback_data منظمة بصيغة: dev:section:action
═══════════════════════════════════════════════════════════════
"""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from locales.ar import buttons


class DeveloperKeyboards:
    """لوحات أزرار المطور."""

    @staticmethod
    def main_panel() -> InlineKeyboardMarkup:
        """اللوحة الرئيسية للمطور."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(buttons.BROADCAST, callback_data="dev:broadcast:menu"),
                InlineKeyboardButton(buttons.STATISTICS, callback_data="dev:stats:show"),
            ],
            [
                InlineKeyboardButton(buttons.DEVELOPERS, callback_data="dev:developers:menu"),
                InlineKeyboardButton(buttons.ERRORS, callback_data="dev:errors:show"),
            ],
            [
                InlineKeyboardButton(buttons.LOGS, callback_data="dev:logs:show"),
                InlineKeyboardButton(buttons.BACKUP, callback_data="dev:backup:menu"),
            ],
            [
                InlineKeyboardButton(buttons.MAINTENANCE, callback_data="dev:maintenance:menu"),
                InlineKeyboardButton(buttons.RESTART, callback_data="dev:restart:confirm"),
            ],
            [
                InlineKeyboardButton(buttons.CLOSE, callback_data="dev:close"),
            ],
        ])

    @staticmethod
    def broadcast_menu() -> InlineKeyboardMarkup:
        """قائمة الإذاعة."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(buttons.BROADCAST_ALL, callback_data="dev:broadcast:all")],
            [InlineKeyboardButton(buttons.BROADCAST_USERS, callback_data="dev:broadcast:users")],
            [InlineKeyboardButton(buttons.BROADCAST_GROUPS, callback_data="dev:broadcast:groups")],
            [InlineKeyboardButton(buttons.BACK, callback_data="dev:main")],
        ])

    @staticmethod
    def developers_menu() -> InlineKeyboardMarkup:
        """قائمة إدارة المطورين."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(buttons.ADD_DEVELOPER, callback_data="dev:developers:add")],
            [InlineKeyboardButton(buttons.REMOVE_DEVELOPER, callback_data="dev:developers:remove")],
            [InlineKeyboardButton(buttons.LIST_DEVELOPERS, callback_data="dev:developers:list")],
            [InlineKeyboardButton(buttons.BACK, callback_data="dev:main")],
        ])

    @staticmethod
    def maintenance_menu(is_on: bool) -> InlineKeyboardMarkup:
        """قائمة الصيانة (تعرض الزر المناسب حسب الحالة)."""
        toggle_btn = (
            InlineKeyboardButton(buttons.MAINTENANCE_OFF, callback_data="dev:maintenance:off")
            if is_on
            else InlineKeyboardButton(buttons.MAINTENANCE_ON, callback_data="dev:maintenance:on")
        )
        return InlineKeyboardMarkup([
            [toggle_btn],
            [InlineKeyboardButton(buttons.BACK, callback_data="dev:main")],
        ])

    @staticmethod
    def backup_menu() -> InlineKeyboardMarkup:
        """قائمة النسخ الاحتياطي."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💾 إنشاء نسخة", callback_data="dev:backup:create")],
            [InlineKeyboardButton("♻️ استعادة نسخة", callback_data="dev:backup:restore")],
            [InlineKeyboardButton(buttons.BACK, callback_data="dev:main")],
        ])

    @staticmethod
    def restart_confirm() -> InlineKeyboardMarkup:
        """تأكيد إعادة التشغيل."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ نعم", callback_data="dev:restart:yes"),
                InlineKeyboardButton("❌ لا", callback_data="dev:main"),
            ],
        ])

    @staticmethod
    def back_button() -> InlineKeyboardMarkup:
        """زر رجوع فقط."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(buttons.BACK, callback_data="dev:main")],
        ])


developer_kb = DeveloperKeyboards()
