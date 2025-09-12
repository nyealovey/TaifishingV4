#!/usr/bin/env python3

"""
泰摸鱼吧 - 创建测试凭据脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.credential import Credential


def create_test_credential():
    """创建测试凭据"""
    print("🔧 创建测试凭据...")

    # 创建Flask应用
    app = create_app()

    with app.app_context():
        # 检查是否已存在测试凭据
        test_cred = Credential.query.filter_by(name="测试MySQL凭据").first()

        if test_cred:
            print("✅ 测试凭据已存在")
            print(f"   名称: {test_cred.name}")
            print(f"   类型: {test_cred.credential_type}")
            print(f"   状态: {'正常' if test_cred.is_active else '已禁用'}")
            return True

        try:
            # 创建测试凭据
            test_cred = Credential(
                name="测试MySQL凭据",
                credential_type="database",
                username="testuser",
                password="testpass123",
                db_type="mysql",
                description="用于测试的MySQL数据库凭据",
            )
            test_cred.is_active = True

            db.session.add(test_cred)
            db.session.commit()

            print("✅ 测试凭据创建成功")
            print("   名称: 测试MySQL凭据")
            print("   用户名: testuser")
            print("   密码: testpass123")
            print("   类型: database")
            print("   数据库类型: mysql")
            print("   状态: 正常")

            return True

        except Exception as e:
            print(f"❌ 创建测试凭据失败: {e}")
            db.session.rollback()
            return False


def main():
    """主函数"""
    print("=" * 50)
    print("🐟 泰摸鱼吧 - 创建测试凭据")
    print("=" * 50)

    success = create_test_credential()

    if success:
        print("\n🎉 测试凭据设置完成！")
        print("现在可以在实例管理中使用此凭据")
    else:
        print("\n⚠️  测试凭据创建失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
