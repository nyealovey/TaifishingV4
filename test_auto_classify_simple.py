#!/usr/bin/env python3
"""
简单的自动分类测试脚本
直接调用服务层方法
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.services.account_classification_service import AccountClassificationService


def test_auto_classify():
    """测试自动分类功能"""
    app = create_app()

    with app.app_context():
        try:
            print("开始测试自动分类功能...")

            # 确保数据库表存在
            print("检查数据库表...")
            db.create_all()

            # 创建服务实例
            service = AccountClassificationService()

            # 执行自动分类
            print("执行自动分类...")
            result = service.auto_classify_accounts(instance_id=None, batch_type="test", created_by=1)

            print(f"自动分类结果: {result}")

            if result.get("success"):
                batch_id = result.get("batch_id")
                print(f"✅ 自动分类成功，批次ID: {batch_id}")

                # 检查账户的last_classified_at字段
                print("\n检查账户分类记录...")
                from app.models.account import Account

                accounts_with_classification = Account.query.filter(Account.last_classified_at.isnot(None)).all()

                print(f"有分类记录的账户数: {len(accounts_with_classification)}")
                for account in accounts_with_classification:
                    print(
                        f"  账户: {account.username} | 最后分类时间: {account.last_classified_at} | 批次ID: {account.last_classification_batch_id}"
                    )

                # 检查批次记录
                print("\n检查批次记录...")
                from app.models.classification_batch import ClassificationBatch

                batch = ClassificationBatch.query.filter_by(batch_id=batch_id).first()
                if batch:
                    print(f"批次状态: {batch.status}")
                    print(f"匹配账户数: {batch.matched_accounts}")
                    print(f"总账户数: {batch.total_accounts}")
                else:
                    print("❌ 未找到批次记录")

                # 检查分类分配记录
                print("\n检查分类分配记录...")
                from app.models.account_classification import AccountClassificationAssignment

                assignments = AccountClassificationAssignment.query.filter_by(batch_id=batch_id, is_active=True).all()
                print(f"活跃的分类分配记录数: {len(assignments)}")

                # 检查UUID格式
                print("\n检查UUID格式...")
                print(f"批次ID长度: {len(batch_id)}")
                print(f"批次ID格式: {batch_id}")
                print(f"是否为有效UUID: {len(batch_id) == 36 and batch_id.count('-') == 4}")

            else:
                print(f"❌ 自动分类失败: {result.get('error')}")

        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_auto_classify()
