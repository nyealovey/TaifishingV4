-- 泰摸鱼吧 - 添加last_sync_time字段到accounts表 (SQLite版本)
-- 创建时间: 2025-01-14
-- 描述: 为accounts表添加last_sync_time字段以支持最后同步时间显示

-- SQLite版本
-- 添加last_sync_time字段
ALTER TABLE accounts ADD COLUMN last_sync_time DATETIME;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_accounts_last_sync_time ON accounts(last_sync_time);

-- 更新现有记录的last_sync_time为updated_at时间
UPDATE accounts SET last_sync_time = updated_at WHERE last_sync_time IS NULL;
