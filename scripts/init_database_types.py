#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 初始化数据库类型配置
创建默认的数据库类型配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.services.database_type_service import DatabaseTypeService

def init_database_types():
    """初始化数据库类型配置"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 开始初始化数据库类型配置...")
            
            # 初始化默认类型
            DatabaseTypeService.init_default_types()
            
            print("✅ 数据库类型配置初始化完成")
            
            # 显示已创建的数据库类型
            types = DatabaseTypeService.get_all_types()
            print(f"\n📊 已创建 {len(types)} 个数据库类型:")
            for config in types:
                status = "✅ 启用" if config.is_active else "❌ 禁用"
                system = "🔒 系统" if config.is_system else "🔓 自定义"
                print(f"  - {config.display_name} ({config.name}) - {status} - {system}")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            raise

if __name__ == '__main__':
    init_database_types()
