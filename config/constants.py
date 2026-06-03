config/constants.py
═══════════════════════════════════════════════════════════════
الثوابت المستخدمة في كل أنحاء المشروع.
وضعها في مكان واحد يمنع "الأرقام السحرية" (Magic Numbers)
ويسهّل التعديل المركزي.
═══════════════════════════════════════════════════════════════
"""

from enum import IntEnum, Enum


# ═══════════════════════════════════════════════════════════════
# مستويات الرتب (رقمية تصاعدية)
# الأعلى رقماً = صلاحيات أكبر
# ═══════════════════════════════════════════════════════════════
class RankLevel(IntEnum):
    """مستويات الرتب في النظام."""
    MEMBER = 0           # عضو
    VIP = 1              # مميز
    ADMIN = 2            # أدمن
    MANAGER = 3          # مدير
    OWNER = 4            # مالك
    MAIN_OWNER = 5       # مالك أساسي
    DEVELOPER = 6        # مطور
    MAIN_DEVELOPER = 7   # المطور الأساسي


# ═══════════════════════════════════════════════════════════════
# الأسماء العربية للرتب (للعرض)
# ═══════════════════════════════════════════════════════════════
RANK_NAMES_AR = {
    RankLevel.MEMBER: "عضو",
    RankLevel.VIP: "مميز",
    RankLevel.ADMIN: "أدمن",
    RankLevel.MANAGER: "مدير",
    RankLevel.OWNER: "مالك",
    RankLevel.MAIN_OWNER: "مالك أساسي",
    RankLevel.DEVELOPER: "مطور",
    RankLevel.MAIN_DEVELOPER: "المطور الأساسي",
}


# ═══════════════════════════════════════════════════════════════
# أنواع العقوبات في نظام الحماية
# ═══════════════════════════════════════════════════════════════
class PunishmentType(str, Enum):
    """أنواع العقوبات."""
    WARN = "warn"          # إنذار
    MUTE = "mute"          # كتم
    RESTRICT = "restrict"  # تقييد
    KICK = "kick"          # طرد
    BAN = "ban"            # حظر


PUNISHMENT_NAMES_AR = {
    PunishmentType.WARN: "إنذار",
    PunishmentType.MUTE: "كتم",
    PunishmentType.RESTRICT: "تقييد",
    PunishmentType.KICK: "طرد",
    PunishmentType.BAN: "حظر",
}


# ═══════════════════════════════════════════════════════════════
# أنواع إجراءات الإدارة (Moderation)
# ═══════════════════════════════════════════════════════════════
class ModerationAction(str, Enum):
    BAN = "ban"
    UNBAN = "unban"
    MUTE = "mute"
    UNMUTE = "unmute"
    RESTRICT = "restrict"
    UNRESTRICT = "unrestrict"
    KICK = "kick"
    GBAN = "gban"          # حظر عام
    UNGBAN = "ungban"      # فك حظر عام


# ═══════════════════════════════════════════════════════════════
# أنواع أحداث السجلات (Event Logs)
# ═══════════════════════════════════════════════════════════════
class EventType(str, Enum):
    MESSAGE_DELETED = "msg_deleted"
    MESSAGE_EDITED = "msg_edited"
    NAME_CHANGED = "name_changed"
    PHOTO_CHANGED = "photo_changed"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    RANK_PROMOTED = "rank_promoted"
    RANK_DEMOTED = "rank_demoted"
    USER_BANNED = "user_banned"
    USER_MUTED = "user_muted"
    PROTECTION_TRIGGERED = "protection_triggered"
    SETTINGS_CHANGED = "settings_changed"


# ═══════════════════════════════════════════════════════════════
# أنواع الحماية
# ═══════════════════════════════════════════════════════════════
class ProtectionType(str, Enum):
    LINKS = "anti_links"
    USERNAME = "anti_username"
    FORWARD = "anti_forward"
    PHOTO = "anti_photo"
    VIDEO = "anti_video"
    FILES = "anti_files"
    AUDIO = "anti_audio"
    STICKERS = "anti_stickers"
    GIF = "anti_gif"
    BOTS = "anti_bots"
    SPAM = "anti_spam"
    FLOOD = "anti_flood"
    NEW_ACCOUNTS = "anti_new_accounts"
    INVITE_LINKS = "anti_invite_links"


PROTECTION_NAMES_AR = {
    ProtectionType.LINKS: "حماية الروابط",
    ProtectionType.USERNAME: "حماية اليوزر",
    ProtectionType.FORWARD: "حماية التوجيه",
    ProtectionType.PHOTO: "حماية الصور",
    ProtectionType.VIDEO: "حماية الفيديو",
    ProtectionType.FILES: "حماية الملفات",
    ProtectionType.AUDIO: "حماية الصوتيات",
    ProtectionType.STICKERS: "حماية الملصقات",
    ProtectionType.GIF: "حماية المتحركات",
    ProtectionType.BOTS: "حماية البوتات",
    ProtectionType.SPAM: "حماية السبام",
    ProtectionType.FLOOD: "حماية التكرار",
    ProtectionType.NEW_ACCOUNTS: "حماية الحسابات الجديدة",
    ProtectionType.INVITE_LINKS: "حماية الدعوات",
}


# ═══════════════════════════════════════════════════════════════
# أنواع الردود
# ═══════════════════════════════════════════════════════════════
class ReplyType(str, Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    GIF = "gif"


class MatchType(str, Enum):
    EXACT = "exact"        # تطابق كامل
    CONTAINS = "contains"  # يحتوي
    REGEX = "regex"        # تعبير نمطي
    KEYWORD = "keyword"    # كلمة مفتاحية


# ═══════════════════════════════════════════════════════════════
# مفاتيح Redis (Namespacing) - دوال بناء المفاتيح
# توحيد بناء المفاتيح يمنع الأخطاء الإملائية
# ═══════════════════════════════════════════════════════════════
class RedisKeys:
    """دوال موحّدة لبناء مفاتيح Redis."""

    @staticmethod
    def rate_limit(user_id: int, action: str) -> str:
        return f"ratelimit:{user_id}:{action}"

    @staticmethod
    def flood(chat_id: int, user_id: int) -> str:
        return f"flood:{chat_id}:{user_id}"

    @staticmethod
    def cache_protection(chat_id: int) -> str:
        return f"cache:protection:{chat_id}"

    @staticmethod
    def cache_welcome(chat_id: int) -> str:
        return f"cache:welcome:{chat_id}"

    @staticmethod
    def cache_rank(chat_id: int, user_id: int) -> str:
        return f"cache:rank:{chat_id}:{user_id}"

    @staticmethod
    def fsm_state(user_id: int) -> str:
        return f"fsm:{user_id}:state"

    @staticmethod
    def fsm_data(user_id: int) -> str:
        return f"fsm:{user_id}:data"

    @staticmethod
    def whisper(whisper_id: str) -> str:
        return f"whisper:{whisper_id}"

    @staticmethod
    def last_message(chat_id: int, user_id: int) -> str:
        return f"lastmsg:{chat_id}:{user_id}"

    @staticmethod
    def global_ban(user_id: int) -> str:
        return f"gban:{user_id}"

    MAINTENANCE = "bot:maintenance"
    BROADCAST_LOCK = "broadcast:lock"


# ═══════════════════════════════════════════════════════════════
# حدود عامة
# ═══════════════════════════════════════════════════════════════
class Limits:
    MAX_WARNS_DEFAULT = 3
    FLOOD_LIMIT_DEFAULT = 5
    FLOOD_SECONDS_DEFAULT = 5
    NEW_ACCOUNT_DAYS_DEFAULT = 7
    CLEANUP_DEFAULT_SECONDS = 60
    BROADCAST_BATCH_SIZE = 25        # عدد الرسائل في الدفعة الواحدة
    BROADCAST_SLEEP = 1              # ثواني بين الدفعات (تجنب FloodWait)
    MAX_MESSAGE_LENGTH = 4096
