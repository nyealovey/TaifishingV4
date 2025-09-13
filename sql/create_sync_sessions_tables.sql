-- 创建同步会话管理表
-- 用于管理批量同步会话和实例记录

-- 创建同步会话表
CREATE TABLE IF NOT EXISTS sync_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    sync_type ENUM('scheduled', 'manual_batch') NOT NULL,
    sync_category ENUM('account', 'capacity', 'config', 'other') NOT NULL DEFAULT 'account',
    status ENUM('running', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'running',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    total_instances INTEGER DEFAULT 0,
    successful_instances INTEGER DEFAULT 0,
    failed_instances INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建同步实例记录表
CREATE TABLE IF NOT EXISTS sync_instance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    instance_id INTEGER NOT NULL,
    instance_name VARCHAR(255),
    sync_category ENUM('account', 'capacity', 'config', 'other') NOT NULL DEFAULT 'account',
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    started_at DATETIME,
    completed_at DATETIME,
    -- 账户同步统计字段
    accounts_synced INTEGER DEFAULT 0,
    accounts_created INTEGER DEFAULT 0,
    accounts_updated INTEGER DEFAULT 0,
    accounts_deleted INTEGER DEFAULT 0,
    -- 通用字段
    error_message TEXT,
    sync_details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sync_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sync_sessions_session_id ON sync_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_sync_type ON sync_sessions(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_sync_category ON sync_sessions(sync_category);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_status ON sync_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sync_sessions_created_at ON sync_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_sync_instance_records_session_id ON sync_instance_records(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_instance_id ON sync_instance_records(instance_id);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_sync_category ON sync_instance_records(sync_category);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_status ON sync_instance_records(status);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_created_at ON sync_instance_records(created_at);

-- 添加注释
COMMENT ON TABLE sync_sessions IS '同步会话表 - 管理批量同步会话';
COMMENT ON TABLE sync_instance_records IS '同步实例记录表 - 记录每个实例的同步详情';

COMMENT ON COLUMN sync_sessions.session_id IS '会话唯一标识符 (UUID)';
COMMENT ON COLUMN sync_sessions.sync_type IS '同步类型: scheduled=定时任务, manual_batch=手动批量';
COMMENT ON COLUMN sync_sessions.sync_category IS '同步分类: account=账户, capacity=容量, config=配置, other=其他';
COMMENT ON COLUMN sync_sessions.status IS '会话状态: running=运行中, completed=已完成, failed=失败, cancelled=已取消';

COMMENT ON COLUMN sync_instance_records.session_id IS '关联的同步会话ID';
COMMENT ON COLUMN sync_instance_records.instance_id IS '数据库实例ID';
COMMENT ON COLUMN sync_instance_records.sync_category IS '同步分类: account=账户, capacity=容量, config=配置, other=其他';
COMMENT ON COLUMN sync_instance_records.status IS '实例同步状态: pending=等待中, running=运行中, completed=已完成, failed=失败';
COMMENT ON COLUMN sync_instance_records.accounts_synced IS '同步的账户总数';
COMMENT ON COLUMN sync_instance_records.accounts_created IS '新增的账户数量';
COMMENT ON COLUMN sync_instance_records.accounts_updated IS '更新的账户数量';
COMMENT ON COLUMN sync_instance_records.accounts_deleted IS '删除的账户数量';
COMMENT ON COLUMN sync_instance_records.sync_details IS '同步详情 (JSON格式)';
