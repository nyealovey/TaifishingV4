-- 同步会话管理优化脚本
-- 解决数据库锁定和死锁问题

-- ============================================================================
-- 1. 优化数据库配置
-- ============================================================================

-- 设置WAL模式（Write-Ahead Logging）提高并发性能
PRAGMA journal_mode = WAL;

-- 设置同步模式为NORMAL（平衡性能和安全性）
PRAGMA synchronous = NORMAL;

-- 增加忙碌超时时间（毫秒）
PRAGMA busy_timeout = 30000;

-- 设置缓存大小（页数）
PRAGMA cache_size = 10000;

-- 设置临时存储为内存
PRAGMA temp_store = MEMORY;

-- ============================================================================
-- 2. 优化表结构
-- ============================================================================

-- 为sync_sessions表添加状态索引
CREATE INDEX IF NOT EXISTS idx_sync_sessions_status_created ON sync_sessions(status, created_at);

-- 为sync_instance_records表添加复合索引
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_session_status ON sync_instance_records(session_id, status);
CREATE INDEX IF NOT EXISTS idx_sync_instance_records_instance_status ON sync_instance_records(instance_id, status);

-- 为accounts表添加实例状态索引
CREATE INDEX IF NOT EXISTS idx_accounts_instance_active ON accounts(instance_id, is_active);

-- ============================================================================
-- 3. 添加并发控制表
-- ============================================================================

-- 创建同步锁表，防止同一实例被多个会话同时同步
CREATE TABLE IF NOT EXISTS sync_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id INTEGER NOT NULL UNIQUE,
    session_id VARCHAR(36) NOT NULL,
    locked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sync_sessions(session_id) ON DELETE CASCADE
);

-- 创建同步锁表索引
CREATE INDEX IF NOT EXISTS idx_sync_locks_instance_id ON sync_locks(instance_id);
CREATE INDEX IF NOT EXISTS idx_sync_locks_session_id ON sync_locks(session_id);
CREATE INDEX IF NOT EXISTS idx_sync_locks_expires_at ON sync_locks(expires_at);

-- ============================================================================
-- 4. 清理过期数据
-- ============================================================================

-- 删除过期的同步锁（超过1小时）
DELETE FROM sync_locks WHERE expires_at < datetime('now', '-1 hour');

-- 清理失败的同步会话（超过24小时）
UPDATE sync_sessions
SET status = 'cancelled', completed_at = datetime('now')
WHERE status = 'running'
AND started_at < datetime('now', '-24 hours');

-- 清理旧的同步数据（超过30天）
DELETE FROM sync_data
WHERE created_at < datetime('now', '-30 days');

-- ============================================================================
-- 5. 优化触发器
-- ============================================================================

-- 删除可能造成性能问题的触发器
DROP TRIGGER IF EXISTS update_sync_sessions_updated_at;

-- 创建轻量级触发器
CREATE TRIGGER IF NOT EXISTS update_sync_sessions_updated_at_light
    AFTER UPDATE ON sync_sessions
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at AND NEW.status != OLD.status
BEGIN
    UPDATE sync_sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ============================================================================
-- 6. 创建性能监控视图
-- ============================================================================

-- 创建同步性能监控视图
CREATE VIEW IF NOT EXISTS sync_performance_view AS
SELECT
    s.session_id,
    s.sync_type,
    s.status,
    s.started_at,
    s.completed_at,
    s.total_instances,
    s.successful_instances,
    s.failed_instances,
    CASE
        WHEN s.completed_at IS NOT NULL
        THEN (julianday(s.completed_at) - julianday(s.started_at)) * 24 * 60 * 60
        ELSE (julianday('now') - julianday(s.started_at)) * 24 * 60 * 60
    END as duration_seconds,
    COUNT(r.id) as total_records,
    COUNT(CASE WHEN r.status = 'completed' THEN 1 END) as completed_records,
    COUNT(CASE WHEN r.status = 'failed' THEN 1 END) as failed_records,
    COUNT(CASE WHEN r.status = 'running' THEN 1 END) as running_records
FROM sync_sessions s
LEFT JOIN sync_instance_records r ON s.session_id = r.session_id
GROUP BY s.id, s.session_id, s.sync_type, s.status, s.started_at, s.completed_at, s.total_instances, s.successful_instances, s.failed_instances;

-- ============================================================================
-- 7. 创建清理存储过程
-- ============================================================================

-- 创建清理过期数据的函数
CREATE TRIGGER IF NOT EXISTS cleanup_expired_locks
    AFTER INSERT ON sync_locks
    FOR EACH ROW
BEGIN
    -- 删除过期的锁
    DELETE FROM sync_locks WHERE expires_at < datetime('now');
END;

-- ============================================================================
-- 8. 验证优化结果
-- ============================================================================

-- 显示优化后的配置
SELECT '数据库优化完成' as message,
       'WAL模式已启用，并发性能已优化' as description,
       datetime('now') as completed_at;

-- 显示当前配置
PRAGMA journal_mode;
PRAGMA synchronous;
PRAGMA busy_timeout;
PRAGMA cache_size;
