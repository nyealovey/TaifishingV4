-- 泰摸鱼吧 - 优化后的同步数据表结构
-- 创建时间: 2025-01-14
-- 描述: 支持复杂权限结构的统一同步数据模型

-- 1. 创建账户当前状态表
CREATE TABLE IF NOT EXISTS current_account_sync_data (
    id SERIAL PRIMARY KEY,
    instance_id INTEGER NOT NULL REFERENCES instances(id),
    db_type VARCHAR(20) NOT NULL,
    session_id VARCHAR(36),
    sync_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'success',
    message TEXT,
    error_message TEXT,

    -- 账户基本信息
    username VARCHAR(255) NOT NULL,
    is_superuser BOOLEAN DEFAULT FALSE,

    -- MySQL权限字段
    global_privileges JSONB,
    database_privileges JSONB,

    -- PostgreSQL权限字段
    predefined_roles JSONB,
    role_attributes JSONB,
    database_privileges_pg JSONB,
    tablespace_privileges JSONB,

    -- SQL Server权限字段
    server_roles JSONB,
    server_permissions JSONB,
    database_roles JSONB,
    database_permissions JSONB,

    -- Oracle权限字段（移除表空间配额）
    oracle_roles JSONB,
    system_privileges JSONB,
    tablespace_privileges_oracle JSONB,

    -- 通用扩展字段
    type_specific JSONB,

    -- 时间戳和状态字段
    last_sync_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_change_type VARCHAR(20) DEFAULT 'add',
    last_change_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 删除标记（不支持恢复）
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_time TIMESTAMP WITH TIME ZONE,

    -- 约束和索引
    CONSTRAINT uq_current_account_sync UNIQUE (instance_id, db_type, username)
);

-- 2. 创建账户变更日志表
CREATE TABLE IF NOT EXISTS account_change_log (
    id SERIAL PRIMARY KEY,
    instance_id INTEGER NOT NULL REFERENCES instances(id),
    db_type VARCHAR(20) NOT NULL,
    username VARCHAR(255) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    change_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(36),
    status VARCHAR(20) DEFAULT 'success',
    message TEXT,

    -- 变更差异
    privilege_diff JSONB,
    other_diff JSONB
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

-- 4. 添加注释
COMMENT ON TABLE current_account_sync_data IS '账户当前状态同步数据表';
COMMENT ON TABLE account_change_log IS '账户变更日志表';

COMMENT ON COLUMN current_account_sync_data.global_privileges IS 'MySQL全局权限';
COMMENT ON COLUMN current_account_sync_data.database_privileges IS 'MySQL数据库权限';
COMMENT ON COLUMN current_account_sync_data.predefined_roles IS 'PostgreSQL预定义角色';
COMMENT ON COLUMN current_account_sync_data.role_attributes IS 'PostgreSQL角色属性';
COMMENT ON COLUMN current_account_sync_data.database_privileges_pg IS 'PostgreSQL数据库权限';
COMMENT ON COLUMN current_account_sync_data.tablespace_privileges IS 'PostgreSQL表空间权限';
COMMENT ON COLUMN current_account_sync_data.server_roles IS 'SQL Server服务器角色';
COMMENT ON COLUMN current_account_sync_data.server_permissions IS 'SQL Server服务器权限';
COMMENT ON COLUMN current_account_sync_data.database_roles IS 'SQL Server数据库角色';
COMMENT ON COLUMN current_account_sync_data.database_permissions IS 'SQL Server数据库权限';
COMMENT ON COLUMN current_account_sync_data.oracle_roles IS 'Oracle角色';
COMMENT ON COLUMN current_account_sync_data.system_privileges IS 'Oracle系统权限';
COMMENT ON COLUMN current_account_sync_data.tablespace_privileges_oracle IS 'Oracle表空间权限';
COMMENT ON COLUMN current_account_sync_data.type_specific IS '类型特定字段';
COMMENT ON COLUMN current_account_sync_data.is_deleted IS '删除标记（不支持恢复）';

COMMENT ON COLUMN account_change_log.change_type IS '变更类型：add, modify_privilege, modify_other, delete';
COMMENT ON COLUMN account_change_log.privilege_diff IS '权限变更差异';
COMMENT ON COLUMN account_change_log.other_diff IS '其他字段变更差异';
