#!/usr/bin/env python3
"""
SQLite 数据库完整初始化脚本
基于 init_postgresql.sql 文档重新初始化 SQLite 数据库
"""

import os
import subprocess
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_script(script_path, description):
    """运行脚本并显示结果"""
    print(f"\n🚀 {description}...")
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True)
        print(f"✅ {description} 完成")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🗄️  泰摸鱼吧 SQLite 数据库完整初始化")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查脚本文件是否存在
    scripts_dir = "scripts"
    structure_script = os.path.join(scripts_dir, "init_sqlite_from_postgresql.py")
    data_script = os.path.join(scripts_dir, "init_sqlite_data.py")

    if not os.path.exists(structure_script):
        print(f"❌ 结构初始化脚本不存在: {structure_script}")
        return False

    if not os.path.exists(data_script):
        print(f"❌ 数据初始化脚本不存在: {data_script}")
        return False

    # 步骤1: 创建数据库结构
    if not run_script(structure_script, "创建数据库表结构"):
        return False

    # 步骤2: 插入初始数据
    if not run_script(data_script, "插入初始数据"):
        return False

    # 步骤3: 验证数据库
    print("\n🔍 验证数据库状态...")
    try:
        import sqlite3

        db_path = "userdata/taifish_dev.db"

        if not os.path.exists(db_path):
            print("❌ 数据库文件不存在")
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 数据库表数量: {len(tables)}")

        # 检查关键表的数据
        key_tables = {
            "users": "用户",
            "database_type_configs": "数据库类型配置",
            "account_classifications": "账户分类",
            "classification_rules": "分类规则",
            "permission_configs": "权限配置",
            "tasks": "任务",
            "global_params": "全局参数",
        }

        print("\n📊 关键表数据统计:")
        for table, description in key_tables.items():
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {description}: {count} 条记录")
            else:
                print(f"  {description}: 表不存在")

        conn.close()
        print("✅ 数据库验证完成")

    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 SQLite 数据库完整初始化成功！")
    print("=" * 60)
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📝 初始化内容:")
    print("  ✅ 数据库表结构创建")
    print("  ✅ 索引创建")
    print("  ✅ 用户数据插入")
    print("  ✅ 数据库类型配置插入")
    print("  ✅ 账户分类数据插入")
    print("  ✅ 分类规则数据插入")
    print("  ✅ 权限配置数据插入 (MySQL, PostgreSQL, SQL Server, Oracle)")
    print("  ✅ 任务数据插入")
    print("  ✅ 全局参数数据插入")
    print("\n🚀 现在可以启动应用程序了！")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
