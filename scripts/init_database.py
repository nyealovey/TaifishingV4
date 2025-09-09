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
from app.models import User, Instance, Credential, Account, Task, Log, GlobalParam, SyncData, AccountClassification, ClassificationRule, AccountClassificationAssignment, PermissionConfig
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
            
            # 初始化账户分类
            print("🏷️ 初始化账户分类...")
            init_account_classifications()
            
            # 初始化权限配置
            print("🔐 初始化权限配置...")
            init_permission_configs()
            
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

def init_account_classifications():
    """初始化账户分类"""
    classifications = [
        {
            'name': '高风险账户',
            'description': '拥有高权限的数据库账户，需要特别关注',
            'risk_level': 'high',
            'color': '#dc3545',
            'priority': 1,
            'is_active': True,
            'is_system': True
        },
        {
            'name': '特权账户',
            'description': '拥有特殊权限的数据库账户',
            'risk_level': 'medium',
            'color': '#fd7e14',
            'priority': 2,
            'is_active': True,
            'is_system': True
        },
        {
            'name': '普通账户',
            'description': '普通权限的数据库账户',
            'risk_level': 'low',
            'color': '#28a745',
            'priority': 3,
            'is_active': True,
            'is_system': True
        },
        {
            'name': '只读账户',
            'description': '只有读取权限的数据库账户',
            'risk_level': 'low',
            'color': '#17a2b8',
            'priority': 4,
            'is_active': True,
            'is_system': True
        }
    ]
    
    for class_data in classifications:
        existing = AccountClassification.query.filter_by(name=class_data['name']).first()
        if not existing:
            classification = AccountClassification(**class_data)
            db.session.add(classification)
    
    db.session.commit()
    print("✅ 账户分类初始化完成")

def init_permission_configs():
    """初始化权限配置"""
    # MySQL权限配置
    mysql_permissions = [
        # 全局权限
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'SELECT', 'description': '查询权限', 'sort_order': 1},
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'INSERT', 'description': '插入权限', 'sort_order': 2},
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'UPDATE', 'description': '更新权限', 'sort_order': 3},
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'DELETE', 'description': '删除权限', 'sort_order': 4},
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'CREATE', 'description': '创建权限', 'sort_order': 5},
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'DROP', 'description': '删除权限', 'sort_order': 6},
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'SUPER', 'description': '超级权限', 'sort_order': 7},
        {'db_type': 'mysql', 'category': 'global_privileges', 'permission_name': 'GRANT OPTION', 'description': '授权权限', 'sort_order': 8},
        # 数据库权限
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'SELECT', 'description': '查询权限', 'sort_order': 1},
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'INSERT', 'description': '插入权限', 'sort_order': 2},
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'UPDATE', 'description': '更新权限', 'sort_order': 3},
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'DELETE', 'description': '删除权限', 'sort_order': 4},
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'CREATE', 'description': '创建权限', 'sort_order': 5},
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'DROP', 'description': '删除权限', 'sort_order': 6},
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'ALTER', 'description': '修改权限', 'sort_order': 7},
        {'db_type': 'mysql', 'category': 'database_privileges', 'permission_name': 'INDEX', 'description': '索引权限', 'sort_order': 8},
    ]
    
    # SQL Server权限配置
    sqlserver_permissions = [
        # 服务器角色
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'sysadmin', 'description': '系统管理员角色', 'sort_order': 1},
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'serveradmin', 'description': '服务器管理员角色', 'sort_order': 2},
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'securityadmin', 'description': '安全管理员角色', 'sort_order': 3},
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'processadmin', 'description': '进程管理员角色', 'sort_order': 4},
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'setupadmin', 'description': '设置管理员角色', 'sort_order': 5},
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'bulkadmin', 'description': '批量管理员角色', 'sort_order': 6},
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'diskadmin', 'description': '磁盘管理员角色', 'sort_order': 7},
        {'db_type': 'sqlserver', 'category': 'server_roles', 'permission_name': 'dbcreator', 'description': '数据库创建者角色', 'sort_order': 8},
        # 服务器权限
        {'db_type': 'sqlserver', 'category': 'server_permissions', 'permission_name': 'CONTROL SERVER', 'description': '控制服务器权限', 'sort_order': 1},
        {'db_type': 'sqlserver', 'category': 'server_permissions', 'permission_name': 'VIEW SERVER STATE', 'description': '查看服务器状态权限', 'sort_order': 2},
        {'db_type': 'sqlserver', 'category': 'server_permissions', 'permission_name': 'ALTER ANY LOGIN', 'description': '修改任意登录权限', 'sort_order': 3},
        {'db_type': 'sqlserver', 'category': 'server_permissions', 'permission_name': 'CREATE ANY DATABASE', 'description': '创建任意数据库权限', 'sort_order': 4},
        # 数据库角色
        {'db_type': 'sqlserver', 'category': 'database_roles', 'permission_name': 'db_owner', 'description': '数据库所有者角色', 'sort_order': 1},
        {'db_type': 'sqlserver', 'category': 'database_roles', 'permission_name': 'db_accessadmin', 'description': '数据库访问管理员角色', 'sort_order': 2},
        {'db_type': 'sqlserver', 'category': 'database_roles', 'permission_name': 'db_securityadmin', 'description': '数据库安全管理员角色', 'sort_order': 3},
        {'db_type': 'sqlserver', 'category': 'database_roles', 'permission_name': 'db_ddladmin', 'description': '数据库DDL管理员角色', 'sort_order': 4},
        {'db_type': 'sqlserver', 'category': 'database_roles', 'permission_name': 'db_backupoperator', 'description': '数据库备份操作员角色', 'sort_order': 5},
        {'db_type': 'sqlserver', 'category': 'database_roles', 'permission_name': 'db_datareader', 'description': '数据库数据读取者角色', 'sort_order': 6},
        {'db_type': 'sqlserver', 'category': 'database_roles', 'permission_name': 'db_datawriter', 'description': '数据库数据写入者角色', 'sort_order': 7},
        # 数据库权限
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'SELECT', 'description': '查询权限', 'sort_order': 1},
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'INSERT', 'description': '插入权限', 'sort_order': 2},
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'UPDATE', 'description': '更新权限', 'sort_order': 3},
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'DELETE', 'description': '删除权限', 'sort_order': 4},
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'CREATE', 'description': '创建权限', 'sort_order': 5},
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'ALTER', 'description': '修改权限', 'sort_order': 6},
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'EXECUTE', 'description': '执行权限', 'sort_order': 7},
        {'db_type': 'sqlserver', 'category': 'database_privileges', 'permission_name': 'CONTROL', 'description': '控制权限', 'sort_order': 8},
    ]
    
    # 合并所有权限配置
    all_permissions = mysql_permissions + sqlserver_permissions
    
    for perm_data in all_permissions:
        existing = PermissionConfig.query.filter_by(
            db_type=perm_data['db_type'],
            category=perm_data['category'],
            permission_name=perm_data['permission_name']
        ).first()
        
        if not existing:
            permission = PermissionConfig(**perm_data)
            db.session.add(permission)
    
    db.session.commit()
    print("✅ 权限配置初始化完成")

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
