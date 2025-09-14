-- 泰摸鱼吧 - 优化后的同步数据表结构 (SQLite版本)
-- 创建时间: 2025-01-14
-- 描述: 支持复杂权限结构的统一同步数据模型

-- 1. 创建账户当前状态表
CREATE TABLE IF NOT EXISTS current_account_sync_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES instances(id),
    db_type VARCHAR(20) NOT NULL,
    session_id VARCHAR(36),
    sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success',
    message TEXT,
    error_message TEXT,
    
    -- 账户基本信息
    username VARCHAR(255) NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE,
    
    -- MySQL权限字段
    global_privileges TEXT,  -- JSON存储
    database_privileges TEXT,  -- JSON存储
    
    -- PostgreSQL权限字段
    predefined_roles TEXT,  -- JSON存储
    role_attributes TEXT,  -- JSON存储
    database_privileges_pg TEXT,  -- JSON存储
    tablespace_privileges TEXT,  -- JSON存储
    
    -- SQL Server权限字段
    server_roles TEXT,  -- JSON存储
    server_permissions TEXT,  -- JSON存储
    database_roles TEXT,  -- JSON存储
    database_permissions TEXT,  -- JSON存储
    
    -- Oracle权限字段（移除表空间配额）
    oracle_roles TEXT,  -- JSON存储
    system_privileges TEXT,  -- JSON存储
    tablespace_privileges_oracle TEXT,  -- JSON存储
    
    -- 通用扩展字段
    type_specific TEXT,  -- JSON存储
    
    -- 时间戳和状态字段
    last_sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_change_type VARCHAR(20) DEFAULT 'add',
    last_change_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 删除标记（不支持恢复）
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_time DATETIME,
    
    -- 唯一约束
    UNIQUE (instance_id, db_type, username)
);

-- 2. 创建账户变更日志表
CREATE TABLE IF NOT EXISTS account_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES instances(id),
    db_type VARCHAR(20) NOT NULL,
    username VARCHAR(255) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    change_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(36),
    status VARCHAR(20) DEFAULT 'success',
    message TEXT,
    
    -- 变更差异
    privilege_diff TEXT,  -- JSON存储
    other_diff TEXT  -- JSON存储
);

-- 3. 创建索引
-- 当前账户状态表索引
CREATE INDEX IF NOT EXISTS idx_current_account_instance_id ON current_account_sync_data(instance_id);
CREATE INDEX IF NOT EXISTS idx_current_account_db_type ON current_account_sync_data(db_type);
CREATE INDEX IF NOT EXISTS idx_current_account_instance_dbtype ON current_account_sync_data(instance_id, db_type);
CREATE INDEX IF NOT EXISTS idx_current_account_deleted ON current_account_sync_data(is_deleted);
CREATE INDEX IF NOT EXISTS idx_current_account_username ON current_account_sync_data(username);
CREATE INDEX IF NOT EXISTS idx_current_account_sync_time ON current_account_sync_data(sync_time);
CREATE INDEX IF NOT EXISTS idx_current_account_last_sync_time ON current_account_sync_data(last_sync_time);
CREATE INDEX IF NOT EXISTS idx_current_account_last_change_time ON current_account_sync_data(last_change_time);

-- 变更日志表索引
CREATE INDEX IF NOT EXISTS idx_change_log_instance_id ON account_change_log(instance_id);
CREATE INDEX IF NOT EXISTS idx_change_log_db_type ON account_change_log(db_type);
CREATE INDEX IF NOT EXISTS idx_change_log_username ON account_change_log(username);
CREATE INDEX IF NOT EXISTS idx_change_log_change_type ON account_change_log(change_type);
CREATE INDEX IF NOT EXISTS idx_change_log_change_time ON account_change_log(change_time);
CREATE INDEX IF NOT EXISTS idx_change_log_instance_dbtype_username_time ON account_change_log(instance_id, db_type, username, change_time);
CREATE INDEX IF NOT EXISTS idx_change_log_username_time ON account_change_log(username, change_time);
