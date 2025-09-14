-- 创建自动分类批次表
-- 用于管理自动分类操作的批次信息，便于日志聚合和查询

-- PostgreSQL版本
CREATE TABLE IF NOT EXISTS classification_batches (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(36) UNIQUE NOT NULL,
    batch_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    total_accounts INTEGER DEFAULT 0,
    matched_accounts INTEGER DEFAULT 0,
    failed_accounts INTEGER DEFAULT 0,
    total_rules INTEGER DEFAULT 0,
    active_rules INTEGER DEFAULT 0,
    error_message TEXT NULL,
    batch_details TEXT NULL,
    created_by INTEGER NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_id ON classification_batches(batch_id);
CREATE INDEX IF NOT EXISTS idx_classification_batches_batch_type ON classification_batches(batch_type);
CREATE INDEX IF NOT EXISTS idx_classification_batches_status ON classification_batches(status);
CREATE INDEX IF NOT EXISTS idx_classification_batches_started_at ON classification_batches(started_at);
CREATE INDEX IF NOT EXISTS idx_classification_batches_created_by ON classification_batches(created_by);

-- 添加注释
COMMENT ON TABLE classification_batches IS '自动分类批次表';
COMMENT ON COLUMN classification_batches.batch_id IS '批次唯一标识';
COMMENT ON COLUMN classification_batches.batch_type IS '批次类型: manual(手动), scheduled(定时), api(API)';
COMMENT ON COLUMN classification_batches.status IS '批次状态: running(运行中), completed(完成), failed(失败)';
COMMENT ON COLUMN classification_batches.started_at IS '批次开始时间';
COMMENT ON COLUMN classification_batches.completed_at IS '批次完成时间';
COMMENT ON COLUMN classification_batches.total_accounts IS '总账户数';
COMMENT ON COLUMN classification_batches.matched_accounts IS '匹配账户数';
COMMENT ON COLUMN classification_batches.failed_accounts IS '失败账户数';
COMMENT ON COLUMN classification_batches.total_rules IS '总规则数';
COMMENT ON COLUMN classification_batches.active_rules IS '活跃规则数';
COMMENT ON COLUMN classification_batches.error_message IS '错误信息';
COMMENT ON COLUMN classification_batches.batch_details IS '批次详细信息(JSON)';
COMMENT ON COLUMN classification_batches.created_by IS '创建者用户ID';
COMMENT ON COLUMN classification_batches.created_at IS '创建时间';
COMMENT ON COLUMN classification_batches.updated_at IS '更新时间';
