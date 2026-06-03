-- ═══════════════════════════════════════════
-- جدول المستخدمين العام (عبر كل البوت)
-- ═══════════════════════════════════════════
CREATE TABLE users (
    user_id         BIGINT PRIMARY KEY,           -- معرف تيليجرام
    first_name      VARCHAR(255),
    last_name       VARCHAR(255),
    username        VARCHAR(255),
    language_code   VARCHAR(10) DEFAULT 'ar',
    is_developer    BOOLEAN DEFAULT FALSE,         -- مطور
    is_main_dev     BOOLEAN DEFAULT FALSE,         -- المطور الأساسي
    is_globally_banned BOOLEAN DEFAULT FALSE,      -- حظر عام
    global_ban_reason TEXT,
    account_created TIMESTAMP,                     -- تاريخ إنشاء حساب تيليجرام (تقديري)
    first_seen      TIMESTAMP DEFAULT NOW(),
    last_activity   TIMESTAMP DEFAULT NOW(),
    is_bot          BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_global_ban ON users(is_globally_banned);


-- ═══════════════════════════════════════════
-- جدول المجموعات
-- ═══════════════════════════════════════════
CREATE TABLE groups (
    chat_id         BIGINT PRIMARY KEY,
    title           VARCHAR(255),
    username        VARCHAR(255),
    chat_type       VARCHAR(20),                  -- group / supergroup
    members_count   INTEGER DEFAULT 0,
    added_by        BIGINT REFERENCES users(user_id),
    is_active       BOOLEAN DEFAULT TRUE,          -- هل البوت لا يزال داخلها
    is_banned       BOOLEAN DEFAULT FALSE,         -- مجموعة محظورة من البوت
    joined_at       TIMESTAMP DEFAULT NOW(),
    left_at         TIMESTAMP,
    settings        JSONB DEFAULT '{}'             -- إعدادات مرنة قابلة للتوسع
);
CREATE INDEX idx_groups_active ON groups(is_active);


-- ═══════════════════════════════════════════
-- جدول الرتب (داخل كل مجموعة)
-- ═══════════════════════════════════════════
CREATE TABLE user_ranks (
    id              BIGSERIAL PRIMARY KEY,
    chat_id         BIGINT REFERENCES groups(chat_id) ON DELETE CASCADE,
    user_id         BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    rank_level      SMALLINT NOT NULL,            -- رقمي: 7=مطور أساسي ... 0=عضو
    promoted_by     BIGINT REFERENCES users(user_id),
    promoted_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(chat_id, user_id)
);
CREATE INDEX idx_ranks_chat_user ON user_ranks(chat_id, user_id);
CREATE INDEX idx_ranks_level ON user_ranks(rank_level);


-- ═══════════════════════════════════════════
-- جدول إجراءات الإدارة (حظر/كتم/تقييد) لكل مجموعة
-- ═══════════════════════════════════════════
CREATE TABLE moderation_actions (
    id              BIGSERIAL PRIMARY KEY,
    chat_id         BIGINT REFERENCES groups(chat_id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL,
    action_type     VARCHAR(20) NOT NULL,         -- ban / mute / restrict
    reason          TEXT,
    issued_by       BIGINT REFERENCES users(user_id),
    expires_at      TIMESTAMP,                     -- NULL = دائم
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_mod_chat_user_active ON moderation_actions(chat_id, user_id, is_active);


-- ═══════════════════════════════════════════
-- جدول إعدادات الحماية لكل مجموعة
-- ═══════════════════════════════════════════
CREATE TABLE protection_settings (
    chat_id             BIGINT PRIMARY KEY REFERENCES groups(chat_id) ON DELETE CASCADE,
    anti_links          BOOLEAN DEFAULT FALSE,
    anti_username       BOOLEAN DEFAULT FALSE,
    anti_forward        BOOLEAN DEFAULT FALSE,
    anti_photo          BOOLEAN DEFAULT FALSE,
    anti_video          BOOLEAN DEFAULT FALSE,
    anti_files          BOOLEAN DEFAULT FALSE,
    anti_audio          BOOLEAN DEFAULT FALSE,
    anti_stickers       BOOLEAN DEFAULT FALSE,
    anti_gif            BOOLEAN DEFAULT FALSE,
    anti_bots           BOOLEAN DEFAULT FALSE,
    anti_spam           BOOLEAN DEFAULT FALSE,
    anti_flood          BOOLEAN DEFAULT FALSE,
    anti_new_accounts   BOOLEAN DEFAULT FALSE,
    anti_invite_links   BOOLEAN DEFAULT FALSE,
    -- العقوبة لكل نوع: warn/mute/restrict/kick/ban
    punishment          VARCHAR(20) DEFAULT 'warn',
    flood_limit         SMALLINT DEFAULT 5,        -- رسائل
    flood_seconds       SMALLINT DEFAULT 5,        -- خلال ثواني
    max_warns           SMALLINT DEFAULT 3,
    new_account_days    SMALLINT DEFAULT 7,
    updated_at          TIMESTAMP DEFAULT NOW()
);


-- ═══════════════════════════════════════════
-- جدول الإنذارات
-- ═══════════════════════════════════════════
CREATE TABLE warns (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     BIGINT REFERENCES groups(chat_id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL,
    count       SMALLINT DEFAULT 0,
    reason      TEXT,
    warned_by   BIGINT,
    updated_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(chat_id, user_id)
);


-- ═══════════════════════════════════════════
-- جدول الترحيب
-- ═══════════════════════════════════════════
CREATE TABLE welcome_settings (
    chat_id         BIGINT PRIMARY KEY REFERENCES groups(chat_id) ON DELETE CASCADE,
    is_enabled      BOOLEAN DEFAULT TRUE,
    welcome_text    TEXT,
    media_type      VARCHAR(20),                  -- photo/video/none
    media_file_id   VARCHAR(255),
    rules_text      TEXT,
    goodbye_text    TEXT,
    goodbye_enabled BOOLEAN DEFAULT FALSE,
    buttons         JSONB DEFAULT '[]',           -- أزرار انلاين
    updated_at      TIMESTAMP DEFAULT NOW()
);


-- ═══════════════════════════════════════════
-- جدول الردود (نصية/وسائط/Regex)
-- ═══════════════════════════════════════════
CREATE TABLE replies (
    id              BIGSERIAL PRIMARY KEY,
    chat_id         BIGINT,                        -- NULL = رد عام لكل البوت
    trigger_text    TEXT NOT NULL,
    match_type      VARCHAR(20) DEFAULT 'exact',  -- exact/contains/regex/keyword
    reply_type      VARCHAR(20) DEFAULT 'text',   -- text/photo/video/audio/gif
    reply_content   TEXT,
    media_file_id   VARCHAR(255),
    is_random       BOOLEAN DEFAULT FALSE,
    created_by      BIGINT,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_replies_chat ON replies(chat_id);


-- ═══════════════════════════════════════════
-- الأوامر المخصصة
-- ═══════════════════════════════════════════
CREATE TABLE custom_commands (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     BIGINT,                            -- NULL = عام
    command     VARCHAR(64) NOT NULL,
    response    TEXT,
    media_file_id VARCHAR(255),
    created_by  BIGINT,
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(chat_id, command)
);


-- ═══════════════════════════════════════════
-- الفلاتر (كلمات/روابط ممنوعة)
-- ═══════════════════════════════════════════
CREATE TABLE filters (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     BIGINT,                            -- NULL = عام
    filter_word TEXT NOT NULL,
    filter_type VARCHAR(20) DEFAULT 'word',        -- word/link/regex
    action      VARCHAR(20) DEFAULT 'delete',
    created_at  TIMESTAMP DEFAULT NOW()
);


-- ═══════════════════════════════════════════
-- التنظيف التلقائي
-- ═══════════════════════════════════════════
CREATE TABLE auto_cleanup (
    chat_id         BIGINT PRIMARY KEY REFERENCES groups(chat_id) ON DELETE CASCADE,
    clean_photos    BOOLEAN DEFAULT FALSE,
    clean_videos    BOOLEAN DEFAULT FALSE,
    clean_files     BOOLEAN DEFAULT FALSE,
    clean_albums    BOOLEAN DEFAULT FALSE,
    delete_after    INTEGER DEFAULT 60,            -- ثواني
    updated_at      TIMESTAMP DEFAULT NOW()
);


-- ═══════════════════════════════════════════
-- السجلات (Audit / Event Logs)
-- ═══════════════════════════════════════════
CREATE TABLE event_logs (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     BIGINT,
    user_id     BIGINT,
    event_type  VARCHAR(50) NOT NULL,    -- msg_deleted/msg_edited/name_changed/join/leave/promote/demote/ban/mute
    actor_id    BIGINT,                  -- منفذ الإجراء
    target_id   BIGINT,                  -- المستهدف
    details     JSONB DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_logs_chat_type ON event_logs(chat_id, event_type);
CREATE INDEX idx_logs_created ON event_logs(created_at);


-- ═══════════════════════════════════════════
-- إحصائيات الرسائل اليومية
-- ═══════════════════════════════════════════
CREATE TABLE daily_stats (
    id              BIGSERIAL PRIMARY KEY,
    stat_date       DATE NOT NULL,
    chat_id         BIGINT,
    messages_count  INTEGER DEFAULT 0,
    new_users       INTEGER DEFAULT 0,
    UNIQUE(stat_date, chat_id)
);


-- ═══════════════════════════════════════════
-- مراقبة الأخطاء
-- ═══════════════════════════════════════════
CREATE TABLE error_logs (
    id          BIGSERIAL PRIMARY KEY,
    error_type  VARCHAR(255),
    message     TEXT,
    traceback   TEXT,
    chat_id     BIGINT,
    user_id     BIGINT,
    created_at  TIMESTAMP DEFAULT NOW()
);


-- ═══════════════════════════════════════════
-- الصراحة (Sarahah)
-- ═══════════════════════════════════════════
CREATE TABLE sarahah_links (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(user_id),
    link_code   VARCHAR(32) UNIQUE NOT NULL,        -- كود فريد للرابط
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sarahah_messages (
    id          BIGSERIAL PRIMARY KEY,
    link_id     BIGINT REFERENCES sarahah_links(id),
    receiver_id BIGINT,
    content     TEXT,
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW()
);


-- ═══════════════════════════════════════════
-- إعدادات البوت العامة (Singleton)
-- ═══════════════════════════════════════════
CREATE TABLE bot_settings (
    key         VARCHAR(64) PRIMARY KEY,
    value       JSONB,
    updated_at  TIMESTAMP DEFAULT NOW()
);
-- مثال: maintenance_mode, force_subscribe_channel


-- ═══════════════════════════════════════════════════════════════
-- 001_initial_schema.sql
-- المخطط الأولي الكامل لقاعدة البيانات
-- ═══════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────
-- المستخدمون
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id            BIGINT PRIMARY KEY,
    first_name         VARCHAR(255),
    last_name          VARCHAR(255),
    username           VARCHAR(255),
    language_code      VARCHAR(10) DEFAULT 'ar',
    is_developer       BOOLEAN DEFAULT FALSE,
    is_main_dev        BOOLEAN DEFAULT FALSE,
    is_globally_banned BOOLEAN DEFAULT FALSE,
    global_ban_reason  TEXT,
    account_created    TIMESTAMP,
    first_seen         TIMESTAMP DEFAULT NOW(),
    last_activity      TIMESTAMP DEFAULT NOW(),
    is_bot             BOOLEAN DEFAULT FALSE,
    created_at         TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_global_ban ON users(is_globally_banned);
CREATE INDEX IF NOT EXISTS idx_users_developer ON users(is_developer);

-- ───────────────────────────────────────────────
-- المجموعات
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS groups (
    chat_id        BIGINT PRIMARY KEY,
    title          VARCHAR(255),
    username       VARCHAR(255),
    chat_type      VARCHAR(20),
    members_count  INTEGER DEFAULT 0,
    added_by       BIGINT,
    is_active      BOOLEAN DEFAULT TRUE,
    is_banned      BOOLEAN DEFAULT FALSE,
    joined_at      TIMESTAMP DEFAULT NOW(),
    left_at        TIMESTAMP,
    settings       JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_groups_active ON groups(is_active);

-- ───────────────────────────────────────────────
-- الرتب
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_ranks (
    id           BIGSERIAL PRIMARY KEY,
    chat_id      BIGINT NOT NULL REFERENCES groups(chat_id) ON DELETE CASCADE,
    user_id      BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    rank_level   SMALLINT NOT NULL DEFAULT 0,
    promoted_by  BIGINT,
    promoted_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(chat_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_ranks_chat_user ON user_ranks(chat_id, user_id);
CREATE INDEX IF NOT EXISTS idx_ranks_level ON user_ranks(rank_level);

-- ───────────────────────────────────────────────
-- إجراءات الإدارة
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS moderation_actions (
    id           BIGSERIAL PRIMARY KEY,
    chat_id      BIGINT NOT NULL REFERENCES groups(chat_id) ON DELETE CASCADE,
    user_id      BIGINT NOT NULL,
    action_type  VARCHAR(20) NOT NULL,
    reason       TEXT,
    issued_by    BIGINT,
    expires_at   TIMESTAMP,
    is_active    BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mod_chat_user_active
    ON moderation_actions(chat_id, user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_mod_expires ON moderation_actions(expires_at)
    WHERE is_active = TRUE;

-- ───────────────────────────────────────────────
-- إعدادات الحماية
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS protection_settings (
    chat_id            BIGINT PRIMARY KEY REFERENCES groups(chat_id) ON DELETE CASCADE,
    anti_links         BOOLEAN DEFAULT FALSE,
    anti_username      BOOLEAN DEFAULT FALSE,
    anti_forward       BOOLEAN DEFAULT FALSE,
    anti_photo         BOOLEAN DEFAULT FALSE,
    anti_video         BOOLEAN DEFAULT FALSE,
    anti_files         BOOLEAN DEFAULT FALSE,
    anti_audio         BOOLEAN DEFAULT FALSE,
    anti_stickers      BOOLEAN DEFAULT FALSE,
    anti_gif           BOOLEAN DEFAULT FALSE,
    anti_bots          BOOLEAN DEFAULT FALSE,
    anti_spam          BOOLEAN DEFAULT FALSE,
    anti_flood         BOOLEAN DEFAULT FALSE,
    anti_new_accounts  BOOLEAN DEFAULT FALSE,
    anti_invite_links  BOOLEAN DEFAULT FALSE,
    punishment         VARCHAR(20) DEFAULT 'warn',
    flood_limit        SMALLINT DEFAULT 5,
    flood_seconds      SMALLINT DEFAULT 5,
    max_warns          SMALLINT DEFAULT 3,
    new_account_days   SMALLINT DEFAULT 7,
    updated_at         TIMESTAMP DEFAULT NOW()
);

-- ───────────────────────────────────────────────
-- الإنذارات
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS warns (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     BIGINT NOT NULL REFERENCES groups(chat_id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL,
    count       SMALLINT DEFAULT 0,
    reason      TEXT,
    warned_by   BIGINT,
    updated_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(chat_id, user_id)
);

-- ───────────────────────────────────────────────
-- الترحيب
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS welcome_settings (
    chat_id          BIGINT PRIMARY KEY REFERENCES groups(chat_id) ON DELETE CASCADE,
    is_enabled       BOOLEAN DEFAULT TRUE,
    welcome_text     TEXT,
    media_type       VARCHAR(20),
    media_file_id    VARCHAR(255),
    rules_text       TEXT,
    goodbye_text     TEXT,
    goodbye_enabled  BOOLEAN DEFAULT FALSE,
    buttons          JSONB DEFAULT '[]'::jsonb,
    updated_at       TIMESTAMP DEFAULT NOW()
);

-- ───────────────────────────────────────────────
-- الردود
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS replies (
    id             BIGSERIAL PRIMARY KEY,
    chat_id        BIGINT,
    trigger_text   TEXT NOT NULL,
    match_type     VARCHAR(20) DEFAULT 'exact',
    reply_type     VARCHAR(20) DEFAULT 'text',
    reply_content  TEXT,
    media_file_id  VARCHAR(255),
    is_random      BOOLEAN DEFAULT FALSE,
    created_by     BIGINT,
    created_at     TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_replies_chat ON replies(chat_id);
CREATE INDEX IF NOT EXISTS idx_replies_trigger ON replies(trigger_text);

-- ───────────────────────────────────────────────
-- الأوامر المخصصة
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS custom_commands (
    id             BIGSERIAL PRIMARY KEY,
    chat_id        BIGINT,
    command        VARCHAR(64) NOT NULL,
    response       TEXT,
    media_file_id  VARCHAR(255),
    created_by     BIGINT,
    created_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(chat_id, command)
);

-- ───────────────────────────────────────────────
-- الفلاتر
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS filters (
    id           BIGSERIAL PRIMARY KEY,
    chat_id      BIGINT,
    filter_word  TEXT NOT NULL,
    filter_type  VARCHAR(20) DEFAULT 'word',
    action       VARCHAR(20) DEFAULT 'delete',
    created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_filters_chat ON filters(chat_id);

-- ───────────────────────────────────────────────
-- التنظيف التلقائي
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auto_cleanup (
    chat_id       BIGINT PRIMARY KEY REFERENCES groups(chat_id) ON DELETE CASCADE,
    clean_photos  BOOLEAN DEFAULT FALSE,
    clean_videos  BOOLEAN DEFAULT FALSE,
    clean_files   BOOLEAN DEFAULT FALSE,
    clean_albums  BOOLEAN DEFAULT FALSE,
    delete_after  INTEGER DEFAULT 60,
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- ───────────────────────────────────────────────
-- السجلات
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS event_logs (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     BIGINT,
    user_id     BIGINT,
    event_type  VARCHAR(50) NOT NULL,
    actor_id    BIGINT,
    target_id   BIGINT,
    details     JSONB DEFAULT '{}'::jsonb,
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_logs_chat_type ON event_logs(chat_id, event_type);
CREATE INDEX IF NOT EXISTS idx_logs_created ON event_logs(created_at);

-- ───────────────────────────────────────────────
-- الإحصائيات اليومية
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_stats (
    id              BIGSERIAL PRIMARY KEY,
    stat_date       DATE NOT NULL,
    chat_id         BIGINT,
    messages_count  INTEGER DEFAULT 0,
    new_users       INTEGER DEFAULT 0,
    UNIQUE(stat_date, chat_id)
);
CREATE INDEX IF NOT EXISTS idx_stats_date ON daily_stats(stat_date);

-- ───────────────────────────────────────────────
-- سجل الأخطاء
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS error_logs (
    id          BIGSERIAL PRIMARY KEY,
    error_type  VARCHAR(255),
    message     TEXT,
    traceback   TEXT,
    chat_id     BIGINT,
    user_id     BIGINT,
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_errors_created ON error_logs(created_at);

-- ───────────────────────────────────────────────
-- الصراحة
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sarahah_links (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    link_code   VARCHAR(32) UNIQUE NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sarahah_code ON sarahah_links(link_code);

CREATE TABLE IF NOT EXISTS sarahah_messages (
    id           BIGSERIAL PRIMARY KEY,
    link_id      BIGINT NOT NULL REFERENCES sarahah_links(id) ON DELETE CASCADE,
    receiver_id  BIGINT NOT NULL,
    content      TEXT,
    is_read      BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sarahah_msg_receiver ON sarahah_messages(receiver_id);

-- ───────────────────────────────────────────────
-- إعدادات البوت العامة
-- ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bot_settings (
    key         VARCHAR(64) PRIMARY KEY,
    value       JSONB,
    updated_at  TIMESTAMP DEFAULT NOW()
);
