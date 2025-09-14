-- 移除老同步模型的SQLite迁移脚本
-- 执行前请确保数据已迁移到新的优化同步模型

-- 1. 移除accounts表中的permissions字段
-- SQLite不支持直接删除列，需要重建表
BEGIN TRANSACTION;

-- 创建新的accounts表（不包含permissions字段）
CREATE TABLE accounts_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL,
    username VARCHAR(255) NOT NULL,
    host VARCHAR(255),
    database_name VARCHAR(255),
    account_type VARCHAR(50),
    plugin VARCHAR(100),
    password_expired BOOLEAN DEFAULT 0,
    password_last_changed DATETIME,
    is_locked BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    last_login DATETIME,
    is_superuser BOOLEAN DEFAULT 0,
    can_grant BOOLEAN DEFAULT 0,
    user_id INTEGER,
    lock_date DATETIME,
    expiry_date DATETIME,
    default_tablespace VARCHAR(100),
    account_created_at DATETIME,
    last_classified_at DATETIME,
    last_classification_batch_id VARCHAR(36),
    last_sync_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances (id)
);

-- 复制数据（排除permissions字段）
INSERT INTO accounts_new (
    id, instance_id, username, host, database_name, account_type, plugin,
    password_expired, password_last_changed, is_locked, is_active, last_login,
    is_superuser, can_grant, user_id, lock_date, expiry_date, default_tablespace,
    account_created_at, last_classified_at, last_classification_batch_id,
    last_sync_time, created_at, updated_at
)
SELECT
    id, instance_id, username, host, database_name, account_type, plugin,
    password_expired, password_last_changed, is_locked, is_active, last_login,
    is_superuser, can_grant, user_id, lock_date, expiry_date, default_tablespace,
    account_created_at, last_classified_at, last_classification_batch_id,
    last_sync_time, created_at, updated_at
FROM accounts;

-- 删除原表
DROP TABLE accounts;

-- 重命名新表
ALTER TABLE accounts_new RENAME TO accounts;

-- 重新创建索引
CREATE INDEX ix_accounts_instance_id ON accounts (instance_id);
CREATE INDEX ix_accounts_username ON accounts (username);
CREATE INDEX ix_accounts_is_locked ON accounts (is_locked);
CREATE INDEX ix_accounts_is_active ON accounts (is_active);
CREATE INDEX ix_accounts_last_sync_time ON accounts (last_sync_time);

COMMIT;

-- 2. 移除sync_data表（如果存在）
DROP TABLE IF EXISTS sync_data;

-- 3. 验证表结构
-- 检查accounts表结构
PRAGMA table_info(accounts);

-- 检查sync_data表是否已删除
SELECT name FROM sqlite_master WHERE type='table' AND name='sync_data';
