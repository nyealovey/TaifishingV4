-- 更新 sync_data 表以支持新的同步会话管理
-- 添加 session_id 和 sync_category 字段

-- 添加 session_id 字段
ALTER TABLE sync_data ADD COLUMN session_id VARCHAR(36);

-- 添加 sync_category 字段
ALTER TABLE sync_data ADD COLUMN sync_category VARCHAR(20);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sync_data_session_id ON sync_data(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_data_sync_category ON sync_data(sync_category);

-- 添加注释
COMMENT ON COLUMN sync_data.session_id IS '关联的同步会话ID';
COMMENT ON COLUMN sync_data.sync_category IS '同步分类: account=账户, capacity=容量, config=配置, other=其他';
