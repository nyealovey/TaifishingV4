#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
初始化权限配置数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.permission_config import PermissionConfig

def init_permission_configs():
    """初始化权限配置数据"""
    app = create_app()
    
    with app.app_context():
        # 检查是否已经初始化过
        if PermissionConfig.query.first():
            print("权限配置已经初始化过了")
            return
        
        print("开始初始化权限配置...")
        
        # 初始化默认权限配置
        PermissionConfig.init_default_permissions()
        
        print("权限配置初始化完成！")
        
        # 显示统计信息
        mysql_count = PermissionConfig.query.filter_by(db_type='mysql').count()
        sqlserver_count = PermissionConfig.query.filter_by(db_type='sqlserver').count()
        
        print(f"MySQL权限配置: {mysql_count} 个")
        print(f"SQL Server权限配置: {sqlserver_count} 个")

if __name__ == '__main__':
    init_permission_configs()
