#!/usr/bin/env python3

"""
泰摸鱼吧 - 创建管理员用户脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


from app import create_app, db
from app.models.user import User


def create_admin_user():
    """创建管理员用户"""
    print("🔧 创建管理员用户...")

    # 创建Flask应用
    app = create_app()

    with app.app_context():
        # 检查是否已存在管理员用户
        admin_user = User.query.filter_by(username='admin').first()

        if admin_user:
            print("✅ 管理员用户已存在")
            print(f"   用户名: {admin_user.username}")
            print(f"   角色: {admin_user.role}")
            print(f"   状态: {'正常' if admin_user.is_active else '已禁用'}")
            return True

        try:
            # 创建管理员用户
            admin_user = User(
                username='admin',
                password='Admin123',
                role='admin'
            )
            admin_user.email = 'admin@taifish.local'
            admin_user.is_active = True

            db.session.add(admin_user)
            db.session.commit()

            print("✅ 管理员用户创建成功")
            print("   用户名: admin")
            print("   密码: Admin123")
            print("   角色: admin")
            print("   状态: 正常")

            return True

        except Exception as e:
            print(f"❌ 创建管理员用户失败: {e}")
            db.session.rollback()
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("🐟 泰摸鱼吧 - 创建管理员用户")
    print("=" * 50)

    success = create_admin_user()

    if success:
        print("\n🎉 管理员用户设置完成！")
        print("现在可以使用 admin/Admin123 登录系统")
    else:
        print("\n⚠️  管理员用户创建失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
