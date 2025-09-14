-- 移除老同步模型的PostgreSQL迁移脚本
-- 执行前请确保数据已迁移到新的优化同步模型

-- 1. 移除accounts表中的permissions字段
ALTER TABLE accounts DROP COLUMN IF EXISTS permissions;

-- 2. 移除sync_data表（如果存在）
DROP TABLE IF EXISTS sync_data CASCADE;

-- 3. 移除相关的索引（如果存在）
-- 注意：PostgreSQL会自动删除相关的索引，但为了确保清理，可以手动删除

-- 4. 验证表结构
-- 检查accounts表结构
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'accounts'
ORDER BY ordinal_position;

-- 检查sync_data表是否已删除
SELECT table_name
FROM information_schema.tables
WHERE table_name = 'sync_data';

-- 5. 清理相关的序列（如果存在）
-- PostgreSQL会自动清理相关的序列，但可以手动检查
SELECT sequence_name
FROM information_schema.sequences
WHERE sequence_name LIKE '%sync_data%';
