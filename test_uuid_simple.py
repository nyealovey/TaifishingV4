#!/usr/bin/env python3
"""
简单的UUID测试脚本
验证UUID生成是否正常工作
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uuid

from app import create_app, db
from app.services.classification_batch_service import ClassificationBatchService


def test_uuid_generation():
    """测试UUID生成"""
    print("=== UUID生成测试 ===")

    # 测试基本UUID生成
    test_uuid = str(uuid.uuid4())
    print(f"生成的UUID: {test_uuid}")
    print(f"UUID长度: {len(test_uuid)}")
    print(f"UUID格式正确: {len(test_uuid) == 36 and test_uuid.count('-') == 4}")

    # 测试批次服务
    app = create_app()
    with app.app_context():
        try:
            print("\n=== 批次服务测试 ===")

            # 确保数据库表存在
            db.create_all()

            # 创建批次
            batch_id = ClassificationBatchService.create_batch(
                batch_type="test", created_by=1, total_rules=5, active_rules=5
            )

            print(f"创建的批次ID: {batch_id}")
            print(f"批次ID长度: {len(batch_id)}")
            print(f"批次ID格式正确: {len(batch_id) == 36 and batch_id.count('-') == 4}")

            # 检查批次是否保存到数据库
            from app.models.classification_batch import ClassificationBatch

            batch = ClassificationBatch.query.filter_by(batch_id=batch_id).first()
            if batch:
                print("✅ 批次成功保存到数据库")
                print(f"批次状态: {batch.status}")
                print(f"批次类型: {batch.batch_type}")
            else:
                print("❌ 批次未保存到数据库")

        except Exception as e:
            print(f"❌ 批次服务测试失败: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    test_uuid_generation()
