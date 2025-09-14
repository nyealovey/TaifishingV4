-- 更新账户分类分配表的唯一约束
-- 从 (account_id, classification_id) 改为 (account_id, classification_id, batch_id)

-- 删除旧的唯一约束
DROP INDEX IF EXISTS unique_account_classification;

-- 添加新的唯一约束
CREATE UNIQUE INDEX unique_account_classification_batch
ON account_classification_assignments (account_id, classification_id, batch_id);
