#!/usr/bin/env python3

"""
泰摸鱼吧 - 数据库迁移管理脚本
使用Flask-Migrate管理数据库结构变更，确保数据不丢失
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault("FLASK_APP", "app")

from flask_migrate import current, downgrade, history, init, migrate, stamp, upgrade

from app import create_app, db


def init_migration():
    """初始化迁移环境"""
    print("🔧 初始化数据库迁移环境...")

    # 创建migrations目录
    migrations_dir = project_root / "migrations"
    if not migrations_dir.exists():
        init()
        print("✅ 迁移环境初始化完成")
    else:
        print("✅ 迁移环境已存在")


def create_migration(message):
    """创建新的迁移文件"""
    print(f"📝 创建迁移: {message}")

    try:
        migrate(message=message)
        print("✅ 迁移文件创建成功")
    except Exception as e:
        print(f"❌ 创建迁移失败: {e}")
        return False

    return True


def upgrade_database(revision="head"):
    """升级数据库到指定版本"""
    print(f"⬆️  升级数据库到: {revision}")

    try:
        upgrade(revision)
        print("✅ 数据库升级成功")
    except Exception as e:
        print(f"❌ 数据库升级失败: {e}")
        return False

    return True


def downgrade_database(revision):
    """降级数据库到指定版本"""
    print(f"⬇️  降级数据库到: {revision}")

    try:
        downgrade(revision)
        print("✅ 数据库降级成功")
    except Exception as e:
        print(f"❌ 数据库降级失败: {e}")
        return False

    return True


def show_current():
    """显示当前数据库版本"""
    print("📊 当前数据库版本:")

    try:
        with create_app().app_context():
            current_rev = current()
            print(f"   当前版本: {current_rev}")
    except Exception as e:
        print(f"❌ 获取当前版本失败: {e}")


def show_history():
    """显示迁移历史"""
    print("📚 迁移历史:")

    try:
        with create_app().app_context():
            history_data = history()
            for rev in history_data:
                print(f"   {rev.revision}: {rev.doc}")
    except Exception as e:
        print(f"❌ 获取迁移历史失败: {e}")


def reset_database():
    """重置数据库（危险操作）"""
    print("⚠️  重置数据库（将删除所有数据）")
    confirm = input("确认继续？(yes/no): ")

    if confirm.lower() != "yes":
        print("❌ 操作已取消")
        return False

    try:
        with create_app().app_context():
            # 删除所有表
            db.drop_all()
            print("✅ 所有表已删除")

            # 重新创建表
            db.create_all()
            print("✅ 表结构已重新创建")

            # 标记为最新版本
            stamp("head")
            print("✅ 数据库已重置")
    except Exception as e:
        print(f"❌ 重置数据库失败: {e}")
        return False

    return True


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python scripts/migrate_db.py <命令> [参数]")
        print("")
        print("命令:")
        print("  init                    初始化迁移环境")
        print("  create <message>        创建新的迁移")
        print("  upgrade [revision]      升级数据库（默认到最新）")
        print("  downgrade <revision>    降级数据库")
        print("  current                 显示当前版本")
        print("  history                 显示迁移历史")
        print("  reset                   重置数据库（危险）")
        print("")
        print("示例:")
        print("  python scripts/migrate_db.py init")
        print("  python scripts/migrate_db.py create '添加用户表'")
        print("  python scripts/migrate_db.py upgrade")
        print("  python scripts/migrate_db.py downgrade -1")
        return

    command = sys.argv[1]

    with create_app().app_context():
        if command == "init":
            init_migration()
        elif command == "create":
            if len(sys.argv) < 3:
                print("❌ 请提供迁移描述")
                return
            message = sys.argv[2]
            create_migration(message)
        elif command == "upgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            upgrade_database(revision)
        elif command == "downgrade":
            if len(sys.argv) < 3:
                print("❌ 请指定要降级到的版本")
                return
            revision = sys.argv[2]
            downgrade_database(revision)
        elif command == "current":
            show_current()
        elif command == "history":
            show_history()
        elif command == "reset":
            reset_database()
        else:
            print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
