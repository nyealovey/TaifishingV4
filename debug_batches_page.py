#!/usr/bin/env python3
"""
调试批次页面脚本
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.account_classification import AccountClassificationAssignment
from app.models.classification_batch import ClassificationBatch


def debug_batches_page():
    app = create_app()
    with app.app_context():
        print("=== 调试批次页面 ===")

        # 检查批次数据
        batches = ClassificationBatch.query.order_by(ClassificationBatch.created_at.desc()).limit(3).all()
        print(f"批次数量: {len(batches)}")

        for batch in batches:
            print(f"\n批次ID: {batch.batch_id}")
            print(f"  状态: {batch.status}")
            print(f"  总账户数: {batch.total_accounts}")
            print(f"  匹配账户数: {batch.matched_accounts}")

            # 检查该批次的匹配记录
            assignments = AccountClassificationAssignment.query.filter_by(batch_id=batch.batch_id, is_active=True).all()

            print(f"  匹配记录数: {len(assignments)}")

            for assignment in assignments:
                print(f"    账户ID: {assignment.account_id}, 分类ID: {assignment.classification_id}")

        # 检查最新的批次
        if batches:
            latest_batch = batches[0]
            print("\n=== 最新批次详情 ===")
            print(f"批次ID: {latest_batch.batch_id}")
            print(f"状态: {latest_batch.status}")
            print(f"创建时间: {latest_batch.created_at}")
            print(f"开始时间: {latest_batch.started_at}")
            print(f"完成时间: {latest_batch.completed_at}")
            print(f"总账户数: {latest_batch.total_accounts}")
            print(f"匹配账户数: {latest_batch.matched_accounts}")
            print(f"失败账户数: {latest_batch.failed_accounts}")


if __name__ == "__main__":
    debug_batches_page()
