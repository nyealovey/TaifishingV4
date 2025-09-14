-- SQLite 初始化脚本 v2.0 - 修复版本
-- 泰摸鱼吧 (TaifishV4) 数据库初始化脚本
-- 基于修复后的数据库结构，确保字段长度和表结构正确

-- 设置时区和字符集
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- ============================================================================
-- 1. 用户管理模块
-- ============================================================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    last_login DATETIME,
    is_active BOOLEAN NOT NULL
);

-- 用户表索引
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

-- ============================================================================
-- 2. 数据库类型配置模块
-- ============================================================================

-- 数据库类型配置表
CREATE TABLE IF NOT EXISTS database_type_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    driver VARCHAR(50) NOT NULL,
    default_port INTEGER NOT NULL,
    default_schema VARCHAR(50) NOT NULL,
    connection_timeout INTEGER,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(20),
    features TEXT,
    is_active BOOLEAN,
    is_system BOOLEAN,
    sort_order INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================================================
-- 3. 凭据管理模块
-- ============================================================================

-- 凭据表
CREATE TABLE IF NOT EXISTS credentials (
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

-- 凭据表索引
CREATE INDEX IF NOT EXISTS ix_credentials_credential_type ON credentials(credential_type);
CREATE INDEX IF NOT EXISTS ix_credentials_db_type ON credentials(db_type);
CREATE INDEX IF NOT EXISTS ix_credentials_name ON credentials(name);

-- ============================================================================
-- 4. 实例管理模块
-- ============================================================================

-- 实例表
CREATE TABLE IF NOT EXISTS instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    db_type VARCHAR(50) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(255),
    database_version VARCHAR(100),
    environment VARCHAR(20) NOT NULL,
    sync_count INTEGER NOT NULL,
    credential_id INTEGER REFERENCES credentials(id),
    description TEXT,
    tags TEXT, -- SQLite使用TEXT存储JSON
    status VARCHAR(20),
    is_active BOOLEAN NOT NULL,
    last_connected DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME
);

-- 实例表索引
CREATE UNIQUE INDEX IF NOT EXISTS ix_instances_name ON instances(name);
CREATE INDEX IF NOT EXISTS ix_instances_status ON instances(status);
CREATE INDEX IF NOT EXISTS ix_instances_db_type ON instances(db_type);
CREATE INDEX IF NOT EXISTS ix_instances_environment ON instances(environment);

-- ============================================================================
-- 5. 账户管理模块
-- ============================================================================

-- 账户表
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL REFERENCES instances(id),
    username VARCHAR(255) NOT NULL,
    host VARCHAR(255),
    database_name VARCHAR(255),
    account_type VARCHAR(50),
    plugin VARCHAR(100),
    password_expired BOOLEAN DEFAULT FALSE,
    password_last_changed DATETIME,
    is_locked BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    permissions TEXT,
    is_superuser BOOLEAN DEFAULT FALSE,
    can_grant BOOLEAN DEFAULT FALSE,
    -- Oracle特有字段
    user_id INTEGER,
    lock_date DATETIME,
    expiry_date DATETIME,
    default_tablespace VARCHAR(100),
    -- SQL Server特有字段
    account_created_at DATETIME,
    -- 分类相关字段
    last_classified_at DATETIME,
    last_classification_batch_id VARCHAR(36),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 账户表索引
CREATE INDEX IF NOT EXISTS idx_accounts_instance_id ON accounts(instance_id);
CREATE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username);
CREATE INDEX IF NOT EXISTS idx_accounts_is_active ON accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_accounts_is_superuser ON accounts(is_superuser);
CREATE INDEX IF NOT EXISTS idx_accounts_last_classified_at ON accounts(last_classified_at);
CREATE INDEX IF NOT EXISTS idx_accounts_last_classification_batch_id ON accounts(last_classification_batch_id);

-- ============================================================================
-- 6. 账户分类管理模块
-- ============================================================================

-- 账户分类表
CREATE TABLE IF NOT EXISTS account_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    risk_level VARCHAR(20) NOT NULL,
    color VARCHAR(20),
    priority INTEGER,
    is_system BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME,
    updated_at DATETIME
);

-- 分类规则表
CREATE TABLE IF NOT EXISTS classification_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    classification_id INTEGER NOT NULL REFERENCES account_classifications(id),
    db_type VARCHAR(20) NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    rule_expression TEXT NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME,
    updated_at DATETIME
);

-- 账户分类分配表
CREATE TABLE IF NOT EXISTS account_classification_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    classification_id INTEGER NOT NULL REFERENCES account_classifications(id),
    assigned_by INTEGER REFERENCES users(id),
    assignment_type VARCHAR(20) NOT NULL DEFAULT 'auto',
    confidence_score REAL,
    notes TEXT,
    batch_id VARCHAR(36),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME,
    UNIQUE(account_id, classification_id, batch_id)
);

-- ============================================================================
-- 7. 任务管理模块
-- ============================================================================

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    task_type VARCHAR(50) NOT NULL,
    db_type VARCHAR(50) NOT NULL,
    schedule VARCHAR(100),
    description TEXT,
    python_code TEXT,
    config TEXT, -- SQLite使用TEXT存储JSON
    is_active BOOLEAN NOT NULL,
    is_builtin BOOLEAN NOT NULL,
    last_run DATETIME,
    last_run_at DATETIME,
    last_status VARCHAR(20),
    last_message TEXT,
    run_count INTEGER,
    success_count INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

-- 任务表索引
CREATE INDEX IF NOT EXISTS ix_tasks_db_type ON tasks(db_type);
CREATE INDEX IF NOT EXISTS ix_tasks_task_type ON tasks(task_type);
CREATE UNIQUE INDEX IF NOT EXISTS ix_tasks_name ON tasks(name);

-- ============================================================================
-- 8. 同步数据模块
-- ============================================================================

-- 同步数据表
CREATE TABLE IF NOT EXISTS sync_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type VARCHAR(50) NOT NULL,
    instance_id INTEGER REFERENCES instances(id),
    task_id INTEGER REFERENCES tasks(id),
    session_id VARCHAR(36),
    sync_category VARCHAR(20),
    data TEXT, -- SQLite使用TEXT存储JSON
    sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success',
    message TEXT,
    synced_count INTEGER DEFAULT 0,
    added_count INTEGER DEFAULT 0,
    removed_count INTEGER DEFAULT 0,
    modified_count INTEGER DEFAULT 0,
    error_message TEXT,
    records_count INTEGER DEFAULT 0
);

-- 同步数据表索引
CREATE INDEX IF NOT EXISTS idx_sync_data_sync_type ON sync_data(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_data_instance_id ON sync_data(instance_id);
CREATE INDEX IF NOT EXISTS idx_sync_data_task_id ON sync_data(task_id);
CREATE INDEX IF NOT EXISTS idx_sync_data_sync_time ON sync_data(sync_time);
CREATE INDEX IF NOT EXISTS idx_sync_data_status ON sync_data(status);
CREATE INDEX IF NOT EXISTS idx_sync_data_session_id ON sync_data(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_data_sync_category ON sync_data(sync_category);

-- ============================================================================
-- 9. 同步会话管理模块
-- ============================================================================

-- 同步会话表
CREATE TABLE IF NOT EXISTS sync_sessions (
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

-- 同步实例记录表
CREATE TABLE IF NOT EXISTS sync_instance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    instance_id INTEGER NOT NULL,
    instance_name VARCHAR(255),
    sync_category VARCHAR(20) NOT NULL DEFAULT 'account' CHECK (sync_category IN ('account', 'capacity', 'config', 'other')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at DATETIME,
    completed_at DATETIME,
    -- 账户同步统计字段
    accounts_synced INTEGER DEFAULT 0,
    accounts_created INTEGER DEFAULT 0,
    accounts_updated INTEGER DEFAULT 0,
    accounts_deleted INTEGER DEFAULT 0,
    -- 通用字段
    error_message TEXT,
    sync_details TEXT, -- SQLite使用TEXT存储JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sync_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(id) ON DELETE CASCADE
);

-- 同步会话表索引
CREATE INDEX IF NOT EXISTS idx_sync_sessions_session_id ON sync_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_sync_type ON sync_sessions(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_sync_category ON sync_sessions(sync_category);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_status ON sync_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_created_at ON sync_sessions(created_at);

-- 同步实例记录表索引
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_session_id ON sync_instance_records(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_instance_id ON sync_instance_records(instance_id);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_sync_category ON sync_instance_records(sync_category);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_status ON sync_instance_records(status);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_created_at ON sync_instance_records(created_at);

-- ============================================================================
-- 10. 自动分类批次管理模块
-- ============================================================================

-- 自动分类批次表
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

-- 自动分类批次表索引
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_id ON classification_batches(batch_id);
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_type ON classification_batches(batch_type);
CREATE INDEX IF NOT EXISTS idx_classification_batches_status ON classification_batches(status);
CREATE INDEX IF NOT EXISTS idx_classification_batches_started_at ON classification_batches(started_at);
CREATE INDEX IF NOT EXISTS idx_classification_batches_created_by ON classification_batches(created_by);

-- ============================================================================
-- 11. 账户变化跟踪模块
-- ============================================================================

-- 账户变化表
CREATE TABLE IF NOT EXISTS account_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_data_id INTEGER NOT NULL REFERENCES sync_data(id),
    instance_id INTEGER NOT NULL REFERENCES instances(id),
    change_type VARCHAR(20) NOT NULL,
    account_data TEXT NOT NULL, -- SQLite使用TEXT存储JSON
    change_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 账户变化表索引
CREATE INDEX IF NOT EXISTS idx_account_changes_sync_data_id ON account_changes(sync_data_id);
CREATE INDEX IF NOT EXISTS idx_account_changes_instance_id ON account_changes(instance_id);
CREATE INDEX IF NOT EXISTS idx_account_changes_change_type ON account_changes(change_type);
CREATE INDEX IF NOT EXISTS idx_account_changes_change_time ON account_changes(change_time);

-- ============================================================================
-- 12. 日志管理模块
-- ============================================================================

-- 日志表
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level VARCHAR(20) NOT NULL,
    log_type VARCHAR(50) NOT NULL,
    module VARCHAR(100),
    message TEXT NOT NULL,
    details TEXT,
    user_id INTEGER REFERENCES users(id),
    ip_address VARCHAR(45),
    user_agent TEXT,
    source VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 统一日志表
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

-- 日志表索引
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_log_type ON logs(log_type);
CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module);
CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);

-- 统一日志表索引
CREATE INDEX IF NOT EXISTS idx_unified_logs_timestamp ON unified_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_unified_logs_level ON unified_logs(level);
CREATE INDEX IF NOT EXISTS idx_unified_logs_module ON unified_logs(module);
CREATE INDEX IF NOT EXISTS idx_unified_logs_created_at ON unified_logs(created_at);

-- ============================================================================
-- 13. 全局参数模块
-- ============================================================================

-- 全局参数表
CREATE TABLE IF NOT EXISTS global_params (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    param_type VARCHAR(50) DEFAULT 'string',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 权限配置表
CREATE TABLE IF NOT EXISTS permission_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    db_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    permission_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN,
    sort_order INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

-- ============================================================================
-- 14. 创建触发器
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
-- 15. 脚本执行完成提示
-- ============================================================================

-- 显示表创建统计
SELECT 'SQLite 初始化脚本执行完成！' as message,
       '泰摸鱼吧 (TaifishV4) 数据库已准备就绪' as description,
       datetime('now') as completed_at;
