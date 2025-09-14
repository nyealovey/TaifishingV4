-- 修复数据库字段缺失和类型不匹配问题
-- 泰摸鱼吧 (TaifishV4) 数据库字段修复脚本

-- ============================================================================
-- 1. 修复 credentials 表 - 添加缺失的 id 字段
-- ============================================================================

-- 检查 credentials 表是否有 id 字段
-- 如果没有，需要重新创建表（因为 SQLite 不支持直接添加主键）

-- 备份现有数据
CREATE TABLE IF NOT EXISTS credentials_backup AS SELECT * FROM credentials;

-- 删除原表
DROP TABLE IF EXISTS credentials;

-- 重新创建 credentials 表（包含 id 字段）
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    credential_type VARCHAR(50) NOT NULL,
    db_type VARCHAR(50),
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    description TEXT,
    instance_ids JSON,
    category_id INTEGER,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME
);

-- 恢复数据（跳过 id 字段，让 SQLite 自动生成）
INSERT INTO credentials (name, credential_type, db_type, username, password, description, instance_ids, category_id, is_active, created_at, updated_at, deleted_at)
SELECT name, credential_type, db_type, username, password, description, instance_ids, category_id, is_active, created_at, updated_at, deleted_at
FROM credentials_backup;

-- 删除备份表
DROP TABLE credentials_backup;

-- ============================================================================
-- 2. 修复 sync_instance_records 表字段长度
-- ============================================================================

-- 重新创建 sync_instance_records 表以修复字段长度
CREATE TABLE IF NOT EXISTS sync_instance_records_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    instance_id INTEGER NOT NULL,
    instance_name VARCHAR(255),
    sync_category VARCHAR(20) NOT NULL DEFAULT 'account',  -- 增加长度
    status VARCHAR(20) NOT NULL DEFAULT 'pending',          -- 增加长度
    started_at DATETIME,
    completed_at DATETIME,
    accounts_synced INTEGER DEFAULT 0,
    accounts_created INTEGER DEFAULT 0,
    accounts_updated INTEGER DEFAULT 0,
    accounts_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    sync_details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sync_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(id) ON DELETE CASCADE
);

-- 复制数据
INSERT INTO sync_instance_records_new
SELECT * FROM sync_instance_records;

-- 删除原表
DROP TABLE sync_instance_records;

-- 重命名新表
ALTER TABLE sync_instance_records_new RENAME TO sync_instance_records;

-- 重新创建索引
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_session_id ON sync_instance_records(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_instance_id ON sync_instance_records(instance_id);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_sync_category ON sync_instance_records(sync_category);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_status ON sync_instance_records(status);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_created_at ON sync_instance_records(created_at);

-- ============================================================================
-- 3. 修复 sync_sessions 表字段长度
-- ============================================================================

-- 重新创建 sync_sessions 表以修复字段长度
CREATE TABLE IF NOT EXISTS sync_sessions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    sync_type VARCHAR(20) NOT NULL,                    -- 增加长度
    sync_category VARCHAR(20) NOT NULL DEFAULT 'account',  -- 增加长度
    status VARCHAR(20) NOT NULL DEFAULT 'running',     -- 增加长度
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    total_instances INTEGER DEFAULT 0,
    successful_instances INTEGER DEFAULT 0,
    failed_instances INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 复制数据
INSERT INTO sync_sessions_new
SELECT * FROM sync_sessions;

-- 删除原表
DROP TABLE sync_sessions;

-- 重命名新表
ALTER TABLE sync_sessions_new RENAME TO sync_sessions;

-- 重新创建索引
CREATE INDEX IF NOT EXISTS idx_sync_sessions_session_id ON sync_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_sync_type ON sync_sessions(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_sync_category ON sync_sessions(sync_category);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_status ON sync_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_created_at ON sync_sessions(created_at);

-- ============================================================================
-- 4. 修复 accounts 表 - 添加 updated_at 触发器
-- ============================================================================

-- 创建触发器自动更新 updated_at 字段
CREATE TRIGGER IF NOT EXISTS update_accounts_updated_at
    AFTER UPDATE ON accounts
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE accounts
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ============================================================================
-- 5. 修复其他表的 updated_at 触发器
-- ============================================================================

-- instances 表触发器
CREATE TRIGGER IF NOT EXISTS update_instances_updated_at
    AFTER UPDATE ON instances
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE instances
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- credentials 表触发器
CREATE TRIGGER IF NOT EXISTS update_credentials_updated_at
    AFTER UPDATE ON credentials
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE credentials
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- account_classifications 表触发器
CREATE TRIGGER IF NOT EXISTS update_account_classifications_updated_at
    AFTER UPDATE ON account_classifications
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE account_classifications
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- classification_rules 表触发器
CREATE TRIGGER IF NOT EXISTS update_classification_rules_updated_at
    AFTER UPDATE ON classification_rules
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE classification_rules
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- account_classification_assignments 表触发器
CREATE TRIGGER IF NOT EXISTS update_account_classification_assignments_updated_at
    AFTER UPDATE ON account_classification_assignments
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE account_classification_assignments
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- sync_sessions 表触发器
CREATE TRIGGER IF NOT EXISTS update_sync_sessions_updated_at
    AFTER UPDATE ON sync_sessions
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE sync_sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ============================================================================
-- 6. 验证修复结果
-- ============================================================================

-- 检查表结构
.schema credentials
.schema sync_instance_records
.schema sync_sessions

-- 检查触发器
SELECT name FROM sqlite_master WHERE type = 'trigger' AND name LIKE '%updated_at%';

PRAGMA table_info(credentials);
PRAGMA table_info(sync_instance_records);
PRAGMA table_info(sync_sessions);
