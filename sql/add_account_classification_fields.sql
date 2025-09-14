-- 为accounts表添加分类相关字段
-- 用于记录账户的最后分类信息

-- 添加字段
ALTER TABLE accounts ADD COLUMN last_classified_at TIMESTAMP;
ALTER TABLE accounts ADD COLUMN last_classification_batch_id VARCHAR(36);

-- 创建索引
CREATE INDEX idx_accounts_last_classified_at ON accounts(last_classified_at);
CREATE INDEX idx_accounts_last_classification_batch_id ON accounts(last_classification_batch_id);
