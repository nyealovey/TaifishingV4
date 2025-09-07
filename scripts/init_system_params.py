#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 初始化系统参数脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.param import Param

def init_system_params():
    """初始化系统参数"""
    print("🔧 初始化系统参数...")
    
    # 创建Flask应用
    app = create_app()
    
    with app.app_context():
        # 系统参数配置
        system_params = [
            # 系统配置
            {
                'name': 'system_name',
                'value': '泰摸鱼吧',
                'param_type': 'string',
                'category': 'system',
                'description': '系统名称',
                'is_system': True
            },
            {
                'name': 'system_version',
                'value': '1.0.0',
                'param_type': 'string',
                'category': 'system',
                'description': '系统版本',
                'is_system': True
            },
            {
                'name': 'debug_mode',
                'value': 'true',
                'param_type': 'bool',
                'category': 'system',
                'description': '调试模式',
                'is_system': True
            },
            
            # 数据库配置
            {
                'name': 'db_pool_size',
                'value': '10',
                'param_type': 'int',
                'category': 'database',
                'description': '数据库连接池大小',
                'is_system': True
            },
            {
                'name': 'db_pool_timeout',
                'value': '30',
                'param_type': 'int',
                'category': 'database',
                'description': '数据库连接超时时间(秒)',
                'is_system': True
            },
            {
                'name': 'db_pool_recycle',
                'value': '3600',
                'param_type': 'int',
                'category': 'database',
                'description': '数据库连接回收时间(秒)',
                'is_system': True
            },
            
            # 同步配置
            {
                'name': 'sync_batch_size',
                'value': '1000',
                'param_type': 'int',
                'category': 'sync',
                'description': '同步批次大小',
                'is_system': True
            },
            {
                'name': 'sync_timeout',
                'value': '300',
                'param_type': 'int',
                'category': 'sync',
                'description': '同步超时时间(秒)',
                'is_system': True
            },
            {
                'name': 'sync_retry_count',
                'value': '3',
                'param_type': 'int',
                'category': 'sync',
                'description': '同步重试次数',
                'is_system': True
            },
            
            # 任务配置
            {
                'name': 'task_max_workers',
                'value': '4',
                'param_type': 'int',
                'category': 'task',
                'description': '最大工作线程数',
                'is_system': True
            },
            {
                'name': 'task_time_limit',
                'value': '1800',
                'param_type': 'int',
                'category': 'task',
                'description': '任务时间限制(秒)',
                'is_system': True
            },
            
            # 安全配置
            {
                'name': 'session_timeout',
                'value': '3600',
                'param_type': 'int',
                'category': 'security',
                'description': '会话超时时间(秒)',
                'is_system': True
            },
            {
                'name': 'password_min_length',
                'value': '8',
                'param_type': 'int',
                'category': 'security',
                'description': '密码最小长度',
                'is_system': True
            },
            {
                'name': 'login_attempts',
                'value': '5',
                'param_type': 'int',
                'category': 'security',
                'description': '最大登录尝试次数',
                'is_system': True
            },
            
            # 日志配置
            {
                'name': 'log_level',
                'value': 'INFO',
                'param_type': 'string',
                'category': 'logging',
                'description': '日志级别',
                'is_system': True
            },
            {
                'name': 'log_retention_days',
                'value': '30',
                'param_type': 'int',
                'category': 'logging',
                'description': '日志保留天数',
                'is_system': True
            },
            {
                'name': 'log_max_size',
                'value': '10485760',
                'param_type': 'int',
                'category': 'logging',
                'description': '日志文件最大大小(字节)',
                'is_system': True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for param_data in system_params:
            existing_param = Param.query.filter_by(name=param_data['name']).first()
            
            if existing_param:
                # 更新现有参数
                existing_param.value = param_data['value']
                existing_param.param_type = param_data['param_type']
                existing_param.category = param_data['category']
                existing_param.description = param_data['description']
                existing_param.is_system = param_data['is_system']
                if not existing_param.default_value:
                    existing_param.default_value = param_data['value']
                updated_count += 1
                print(f"  ✅ 更新参数: {param_data['name']}")
            else:
                # 创建新参数
                param = Param(
                    name=param_data['name'],
                    value=param_data['value'],
                    param_type=param_data['param_type'],
                    category=param_data['category'],
                    description=param_data['description'],
                    is_system=param_data['is_system'],
                    default_value=param_data['value']
                )
                db.session.add(param)
                created_count += 1
                print(f"  ✅ 创建参数: {param_data['name']}")
        
        try:
            db.session.commit()
            print(f"\n🎉 系统参数初始化完成！")
            print(f"   创建: {created_count} 个参数")
            print(f"   更新: {updated_count} 个参数")
            print(f"   总计: {created_count + updated_count} 个参数")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 初始化系统参数失败: {e}")
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("🐟 泰摸鱼吧 - 初始化系统参数")
    print("=" * 50)
    
    success = init_system_params()
    
    if success:
        print("\n🎉 系统参数设置完成！")
        print("现在可以在系统参数管理中查看和配置这些参数")
    else:
        print("\n⚠️  系统参数初始化失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
