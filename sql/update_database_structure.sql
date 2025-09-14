-- 数据库结构更新脚本 v2.0
-- 泰摸鱼吧 (TaifishV4) 数据库结构修复和更新
-- 适用于SQLite数据库，确保与修复后的结构一致

-- 设置外键约束
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 1. 检查并修复credentials表
-- ============================================================================

-- 检查credentials表是否有id字段
-- 如果没有，需要重新创建表
CREATE TABLE IF NOT EXISTS credentials_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    credential_type VARCHAR(50) NOT NULL,
    db_type VARCHAR(50),
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    description TEXT,
    instance_ids TEXT, -- SQLite使用TEXT存储JSON
    category_id INTEGER,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME
);

-- 如果原表存在，复制数据到新表
INSERT OR IGNORE INTO credentials_new
SELECT * FROM credentials WHERE 1=0; -- 只复制结构，不复制数据

-- 检查原表是否有id字段
-- 如果没有，重新创建表
DROP TABLE IF EXISTS credentials_backup;
CREATE TABLE credentials_backup AS SELECT * FROM credentials;

DROP TABLE IF EXISTS credentials;
ALTER TABLE credentials_new RENAME TO credentials;

-- 恢复数据（跳过id字段，让SQLite自动生成）
INSERT INTO credentials (name, credential_type, db_type, username, password, description, instance_ids, category_id, is_active, created_at, updated_at, deleted_at)
SELECT name, credential_type, db_type, username, password, description, instance_ids, category_id, is_active, created_at, updated_at, deleted_at
FROM credentials_backup;

DROP TABLE credentials_backup;

-- ============================================================================
-- 2. 检查并修复sync_sessions表字段长度
-- ============================================================================

-- 重新创建sync_sessions表以修复字段长度
CREATE TABLE IF NOT EXISTS sync_sessions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    sync_type VARCHAR(20) NOT NULL CHECK (sync_type IN ('scheduled', 'manual_batch')),
    sync_category VARCHAR(20) NOT NULL DEFAULT 'account' CHECK (sync_category IN ('account', 'capacity', 'config', 'other')),
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
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
-- 3. 检查并修复sync_instance_records表字段长度
-- ============================================================================

-- 重新创建sync_instance_records表以修复字段长度
CREATE TABLE IF NOT EXISTS sync_instance_records_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    instance_id INTEGER NOT NULL,
    instance_name VARCHAR(255),
    sync_category VARCHAR(20) NOT NULL DEFAULT 'account' CHECK (sync_category IN ('account', 'capacity', 'config', 'other')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at DATETIME,
    completed_at DATETIME,
    accounts_synced INTEGER DEFAULT 0,
    accounts_created INTEGER DEFAULT 0,
    accounts_updated INTEGER DEFAULT 0,
    accounts_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    sync_details TEXT, -- SQLite使用TEXT存储JSON
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
-- 4. 为accounts表添加分类相关字段
-- ============================================================================

-- 添加分类相关字段（如果不存在）
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS last_classified_at DATETIME;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS last_classification_batch_id VARCHAR(36);

-- 创建新字段的索引
CREATE INDEX IF NOT EXISTS idx_accounts_last_classified_at ON accounts(last_classified_at);
CREATE INDEX IF NOT EXISTS idx_accounts_last_classification_batch_id ON accounts(last_classification_batch_id);

-- ============================================================================
-- 5. 为sync_data表添加新字段
-- ============================================================================

-- 添加新字段（如果不存在）
ALTER TABLE sync_data ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);
ALTER TABLE sync_data ADD COLUMN IF NOT EXISTS sync_category VARCHAR(20);

-- 创建新字段的索引
CREATE INDEX IF NOT EXISTS idx_sync_data_session_id ON sync_data(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_data_sync_category ON sync_data(sync_category);

-- ============================================================================
-- 6. 创建缺失的表
-- ============================================================================

-- 创建classification_batches表（如果不存在）
CREATE TABLE IF NOT EXISTS classification_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id VARCHAR(36) UNIQUE NOT NULL,
    batch_type VARCHAR(20) NOT NULL CHECK (batch_type IN ('manual', 'scheduled', 'api')),
    status VARCHAR(20) NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    total_accounts INTEGER DEFAULT 0,
    matched_accounts INTEGER DEFAULT 0,
    failed_accounts INTEGER DEFAULT 0,
    total_rules INTEGER DEFAULT 0,
    active_rules INTEGER DEFAULT 0,
    error_message TEXT,
    batch_details TEXT, -- SQLite使用TEXT存储JSON
    created_by INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建classification_batches表索引
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_id ON classification_batches(batch_id);
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_type ON classification_batches(batch_type);
CREATE INDEX IF NOT EXISTS idx_classification_batches_status ON classification_batches(status);
CREATE INDEX IF NOT EXISTS idx_classification_batches_started_at ON classification_batches(started_at);
CREATE INDEX IF NOT EXISTS idx_classification_batches_created_by ON classification_batches(created_by);

-- 创建unified_logs表（如果不存在）
CREATE TABLE IF NOT EXISTS unified_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    level VARCHAR(8) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    traceback TEXT,
    context TEXT, -- SQLite使用TEXT存储JSON
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建unified_logs表索引
CREATE INDEX IF NOT EXISTS idx_unified_logs_timestamp ON unified_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_unified_logs_level ON unified_logs(level);
CREATE INDEX IF NOT EXISTS idx_unified_logs_module ON unified_logs(module);
CREATE INDEX IF NOT EXISTS idx_unified_logs_created_at ON unified_logs(created_at);

-- ============================================================================
-- 7. 创建updated_at触发器
-- ============================================================================

-- 创建updated_at字段自动更新触发器
CREATE TRIGGER IF NOT EXISTS update_instances_updated_at
    AFTER UPDATE ON instances
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE instances
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_credentials_updated_at
    AFTER UPDATE ON credentials
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE credentials
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_accounts_updated_at
    AFTER UPDATE ON accounts
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE accounts
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_account_classifications_updated_at
    AFTER UPDATE ON account_classifications
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE account_classifications
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_classification_rules_updated_at
    AFTER UPDATE ON classification_rules
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE classification_rules
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_account_classification_assignments_updated_at
    AFTER UPDATE ON account_classification_assignments
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE account_classification_assignments
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_sync_sessions_updated_at
    AFTER UPDATE ON sync_sessions
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE sync_sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_classification_batches_updated_at
    AFTER UPDATE ON classification_batches
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE classification_batches
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ============================================================================
-- 8. 验证修复结果
-- ============================================================================

-- 显示表结构验证
SELECT '数据库结构更新完成！' as message,
       '所有表结构已修复并更新' as description,
       datetime('now') as completed_at;

-- 显示表列表
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- 显示触发器列表
SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%updated_at%';
