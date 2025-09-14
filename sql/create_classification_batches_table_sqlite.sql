-- 创建自动分类批次表 (SQLite版本)
-- 用于管理自动分类操作的批次信息，便于日志聚合和查询

CREATE TABLE IF NOT EXISTS classification_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id VARCHAR(36) UNIQUE NOT NULL,
    batch_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    total_accounts INTEGER DEFAULT 0,
    matched_accounts INTEGER DEFAULT 0,
    failed_accounts INTEGER DEFAULT 0,
    total_rules INTEGER DEFAULT 0,
    active_rules INTEGER DEFAULT 0,
    error_message TEXT NULL,
    batch_details TEXT NULL,
    created_by INTEGER NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_id ON classification_batches(batch_id);
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_type ON classification_batches(batch_type);
CREATE INDEX IF NOT EXISTS idx_classification_batches_status ON classification_batches(status);
CREATE INDEX IF NOT EXISTS idx_classification_batches_started_at ON classification_batches(started_at);
CREATE INDEX IF NOT EXISTS idx_classification_batches_created_by ON classification_batches(created_by);
