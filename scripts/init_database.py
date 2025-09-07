#!/usr/bin/env python3
"""
泰摸鱼吧 - 数据库初始化脚本
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Instance, Credential, Account, Task, Log, GlobalParam, SyncData
from app.utils.logger import setup_logger

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建所有表
            print("🔨 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 创建默认管理员用户
            print("👤 创建默认管理员用户...")
            User.create_admin()
            
            # 初始化全局参数
            print("⚙️ 初始化全局参数...")
            init_global_params()
            
            print("✅ 数据库初始化完成")
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            raise

def init_global_params():
    """初始化全局参数"""
    # 数据库类型参数
    db_types = [
        {
            'param_type': 'database_type',
            'name': 'SQL Server',
            'config': {
                'driver': 'pymssql',
                'port': 1433,
                'default_schema': 'dbo',
                'connection_timeout': 30,
                'description': 'Microsoft SQL Server数据库'
            }
        },
        {
            'param_type': 'database_type',
            'name': 'MySQL',
            'config': {
                'driver': 'pymysql',
                'port': 3306,
                'default_schema': 'information_schema',
                'connection_timeout': 30,
                'description': 'MySQL数据库'
            }
        },
        {
            'param_type': 'database_type',
            'name': 'Oracle',
            'config': {
                'driver': 'cx_Oracle',
                'port': 1521,
                'default_schema': 'SYS',
                'connection_timeout': 30,
                'description': 'Oracle数据库'
            }
        }
    ]
    
    # 凭据类型参数
    cred_types = [
        {
            'param_type': 'credential_type',
            'name': '数据库凭据',
            'config': {
                'encryption_method': 'bcrypt',
                'password_strength': 'strong',
                'expiry_days': 90,
                'description': '数据库连接凭据'
            }
        },
        {
            'param_type': 'credential_type',
            'name': 'SSH凭据',
            'config': {
                'encryption_method': 'AES',
                'key_type': 'RSA',
                'expiry_days': 180,
                'description': 'SSH连接凭据'
            }
        },
        {
            'param_type': 'credential_type',
            'name': 'Windows凭据',
            'config': {
                'encryption_method': 'AES',
                'expiry_days': 90,
                'description': 'Windows系统凭据'
            }
        }
    ]
    
    # 同步类型参数
    sync_types = [
        {
            'param_type': 'sync_type',
            'name': '账户信息同步',
            'config': {
                'frequency': '0 */6 * * *',  # 每6小时
                'batch_size': 1000,
                'timeout': 300,
                'description': '同步数据库账户信息'
            }
        },
        {
            'param_type': 'sync_type',
            'name': '权限信息同步',
            'config': {
                'frequency': '0 0 */12 * *',  # 每12小时
                'batch_size': 500,
                'timeout': 600,
                'description': '同步数据库权限信息'
            }
        }
    ]
    
    # 角色类型参数
    role_types = [
        {
            'param_type': 'role_type',
            'name': '管理员',
            'config': {
                'permissions': ['read', 'write', 'delete', 'admin'],
                'description': '系统管理员，拥有所有权限'
            }
        },
        {
            'param_type': 'role_type',
            'name': '普通用户',
            'config': {
                'permissions': ['read'],
                'description': '普通用户，只有查看权限'
            }
        }
    ]
    
    # 合并所有参数
    all_params = db_types + cred_types + sync_types + role_types
    
    # 插入参数
    for param_data in all_params:
        existing = GlobalParam.query.filter_by(
            param_type=param_data['param_type'],
            name=param_data['name']
        ).first()
        
        if not existing:
            param = GlobalParam(
                param_type=param_data['param_type'],
                name=param_data['name'],
                config=param_data['config']
            )
            db.session.add(param)
    
    db.session.commit()
    print("✅ 全局参数初始化完成")

def reset_database():
    """重置数据库"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️ 删除所有表...")
            db.drop_all()
            print("✅ 所有表已删除")
            
            print("🔨 重新创建数据库表...")
            db.create_all()
            print("✅ 数据库表重新创建成功")
            
            # 重新初始化
            init_database()
            
        except Exception as e:
            print(f"❌ 数据库重置失败: {e}")
            raise

def check_database():
    """检查数据库状态"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查表是否存在
            tables = db.engine.table_names()
            print(f"📊 数据库表数量: {len(tables)}")
            print(f"📋 表列表: {', '.join(tables)}")
            
            # 检查用户数量
            user_count = User.query.count()
            print(f"👥 用户数量: {user_count}")
            
            # 检查实例数量
            instance_count = Instance.query.count()
            print(f"🗄️ 实例数量: {instance_count}")
            
            # 检查凭据数量
            credential_count = Credential.query.count()
            print(f"🔑 凭据数量: {credential_count}")
            
            # 检查全局参数数量
            param_count = GlobalParam.query.count()
            print(f"⚙️ 全局参数数量: {param_count}")
            
            print("✅ 数据库状态检查完成")
            
        except Exception as e:
            print(f"❌ 数据库状态检查失败: {e}")
            raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='泰摸鱼吧数据库管理工具')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--reset', action='store_true', help='重置数据库')
    parser.add_argument('--check', action='store_true', help='检查数据库状态')
    
    args = parser.parse_args()
    
    if args.init:
        init_database()
    elif args.reset:
        reset_database()
    elif args.check:
        check_database()
    else:
        print("请指定操作: --init, --reset, 或 --check")
        print("示例: python scripts/init_database.py --init")
