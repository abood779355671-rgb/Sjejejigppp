keyboards/protection_kb.py
═══════════════════════════════════════════════════════════════
لوحة تحكم الحماية التفاعلية.
تعرض كل أنواع الحماية مع حالتها (✅ مفعّل / ❌ معطّل).
═══════════════════════════════════════════════════════════════
"""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config.constants import ProtectionType, PROTECTION_NAMES_AR, PunishmentType, PUNISHMENT_NAMES_AR


class ProtectionKeyboards:
    """لوحات الحماية."""

    @staticmethod
    def main_panel(settings_data: dict) -> InlineKeyboardMarkup:
        """
        اللوحة الرئيسية للحماية.
        كل زر يعرض اسم الحماية وحالتها.
        """
        rows = []
        # ترتيب أنواع الحماية في أزرار (زرّان بكل صف)
        types = [
            (ProtectionType.LINKS, "anti_links"),
            (ProtectionType.INVITE_LINKS, "anti_invite_links"),
            (ProtectionType.USERNAME, "anti_username"),
            (ProtectionType.FORWARD, "anti_forward"),
            (ProtectionType.PHOTO, "anti_photo"),
            (ProtectionType.VIDEO, "anti_video"),
            (ProtectionType.FILES, "anti_files"),
            (ProtectionType.AUDIO, "anti_audio"),
            (ProtectionType.STICKERS, "anti_stickers"),
            (ProtectionType.GIF, "anti_gif"),
            (ProtectionType.BOTS, "anti_bots"),
            (ProtectionType.SPAM, "anti_spam"),
            (ProtectionType.FLOOD, "anti_flood"),
            (ProtectionType.NEW_ACCOUNTS, "anti_new_accounts"),
        ]

        row = []
        for prot_type, field in types:
            enabled = settings_data.get(field, False)
            icon = "✅" if enabled else "❌"
            name = PROTECTION_NAMES_AR[prot_type]
            row.append(
                InlineKeyboardButton(
                    f"{icon} {name}",
                    callback_data=f"prot:toggle:{field}",
                )
            )
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)

        # زر العقوبة الحالية
        current_punishment = settings_data.get("punishment", "warn")
        punishment_name = PUNISHMENT_NAMES_AR.get(
            PunishmentType(current_punishment), "إنذار"
        )
        rows.append([
            InlineKeyboardButton(
                f"⚖️ العقوبة: {punishment_name}",
                callback_data="prot:punishment:menu",
            )
        ])
        rows.append([
            InlineKeyboardButton("❌ إغلاق", callback_data="prot:close")
        ])

        return InlineKeyboardMarkup(rows)

    @staticmethod
    def punishment_menu() -> InlineKeyboardMarkup:
        """قائمة اختيار العقوبة."""
        rows = []
        for p_type in PunishmentType:
            name = PUNISHMENT_NAMES_AR[p_type]
            rows.append([
                InlineKeyboardButton(
                    f"⚖️ {name}",
                    callback_data=f"prot:setpunish:{p_type.value}",
                )
            ])
        rows.append([
            InlineKeyboardButton("🔙 رجوع", callback_data="prot:main")
        ])
        return InlineKeyboardMarkup(rows)


protection_kb = ProtectionKeyboards()
