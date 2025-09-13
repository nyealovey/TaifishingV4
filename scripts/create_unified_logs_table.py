#!/usr/bin/env python3
"""
创建unified_logs表的脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.unified_log import UnifiedLog

def create_unified_logs_table():
    """创建unified_logs表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建表
            db.create_all()
            print("✅ unified_logs表创建成功")
            
            # 验证表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'unified_logs' in tables:
                print("✅ 表验证成功")
                
                # 显示表结构
                columns = inspector.get_columns('unified_logs')
                print("\n📋 表结构:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            else:
                print("❌ 表创建失败")
                
        except Exception as e:
            print(f"❌ 创建表时出错: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 开始创建unified_logs表...")
    success = create_unified_logs_table()
    
    if success:
        print("\n🎉 表创建完成!")
    else:
        print("\n💥 表创建失败!")
        sys.exit(1)
