#!/usr/bin/env python3
"""
泰摸鱼吧 - 数据初始化脚本
根据data_requirements.md规范生成真实数据
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Account, Credential, GlobalParam, Instance, Log, SyncData, Task, User


def init_all_data():
    """初始化所有数据"""
    app = create_app()

    with app.app_context():
        try:
            print("🚀 开始初始化泰摸鱼吧数据...")

            # 1. 初始化数据库
            print("\n1️⃣ 初始化数据库...")
            init_database()

            # 2. 初始化全局参数
            print("\n2️⃣ 初始化全局参数...")
            init_global_params()

            # 3. 初始化示例实例（需要真实连接信息）
            print("\n3️⃣ 初始化示例实例...")
            init_sample_instances()

            # 4. 初始化示例凭据
            print("\n4️⃣ 初始化示例凭据...")
            init_sample_credentials()

            # 5. 初始化管理员用户
            print("\n5️⃣ 初始化管理员用户...")
            init_admin_user()

            print("\n✅ 所有数据初始化完成！")
            print("\n📋 初始化摘要:")
            print(f"   - 用户数量: {User.query.count()}")
            print(f"   - 实例数量: {Instance.query.count()}")
            print(f"   - 凭据数量: {Credential.query.count()}")
            print(f"   - 全局参数数量: {GlobalParam.query.count()}")

        except Exception as e:
            print(f"❌ 数据初始化失败: {e}")
            raise

def init_database():
    """初始化数据库"""
    try:
        db.create_all()
        print("✅ 数据库表创建成功")
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
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
        }
    ]

    # 同步类型参数
    sync_types = [
        {
            'param_type': 'sync_type',
            'name': '账户信息同步',
            'config': {
                'frequency': '0 */6 * * *',
                'batch_size': 1000,
                'timeout': 300,
                'description': '同步数据库账户信息'
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

    all_params = db_types + cred_types + sync_types + role_types

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

def init_sample_instances():
    """初始化示例实例（需要真实连接信息）"""
    # 从环境变量或配置文件读取实例信息
    instances_config = [
        {
            'name': '开发SQL Server',
            'db_type': 'SQL Server',
            'host': os.getenv('SQL_SERVER_HOST', 'localhost'),
            'port': int(os.getenv('SQL_SERVER_PORT', 1433)),
            'description': '开发环境SQL Server数据库',
            'tags': ['开发', 'SQL Server']
        },
        {
            'name': '开发MySQL',
            'db_type': 'MySQL',
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'description': '开发环境MySQL数据库',
            'tags': ['开发', 'MySQL']
        },
        {
            'name': '开发Oracle',
            'db_type': 'Oracle',
            'host': os.getenv('ORACLE_HOST', 'localhost'),
            'port': int(os.getenv('ORACLE_PORT', 1521)),
            'description': '开发环境Oracle数据库',
            'tags': ['开发', 'Oracle']
        }
    ]

    for instance_data in instances_config:
        existing = Instance.query.filter_by(name=instance_data['name']).first()
        if not existing:
            instance = Instance(
                name=instance_data['name'],
                db_type=instance_data['db_type'],
                host=instance_data['host'],
                port=instance_data['port'],
                description=instance_data['description'],
                tags=instance_data['tags']
            )
            db.session.add(instance)

    db.session.commit()
    print("✅ 示例实例初始化完成")

def init_sample_credentials():
    """初始化示例凭据"""
    credentials_config = [
        {
            'name': 'SQL Server管理员凭据',
            'credential_type': '数据库凭据',
            'db_type': 'SQL Server',
            'username': os.getenv('SQL_SERVER_USERNAME', 'sa'),
            'password': os.getenv('SQL_SERVER_PASSWORD', 'your_password'),
            'description': 'SQL Server管理员凭据'
        },
        {
            'name': 'MySQL管理员凭据',
            'credential_type': '数据库凭据',
            'db_type': 'MySQL',
            'username': os.getenv('MYSQL_USERNAME', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', 'your_password'),
            'description': 'MySQL管理员凭据'
        },
        {
            'name': 'Oracle管理员凭据',
            'credential_type': '数据库凭据',
            'db_type': 'Oracle',
            'username': os.getenv('ORACLE_USERNAME', 'system'),
            'password': os.getenv('ORACLE_PASSWORD', 'your_password'),
            'description': 'Oracle管理员凭据'
        }
    ]

    for cred_data in credentials_config:
        existing = Credential.query.filter_by(name=cred_data['name']).first()
        if not existing:
            credential = Credential(
                name=cred_data['name'],
                credential_type=cred_data['credential_type'],
                db_type=cred_data['db_type'],
                username=cred_data['username'],
                password=cred_data['password']
            )
            db.session.add(credential)

    db.session.commit()
    print("✅ 示例凭据初始化完成")

def init_admin_user():
    """初始化管理员用户"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password='Admin123',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ 管理员用户创建成功: admin/Admin123")
    else:
        print("✅ 管理员用户已存在")

def validate_connections():
    """验证数据库连接"""
    print("🔍 验证数据库连接...")

    instances = Instance.query.all()
    for instance in instances:
        print(f"   - 测试实例: {instance.name} ({instance.db_type})")
        result = instance.test_connection()
        if result['status'] == 'success':
            print(f"     ✅ 连接成功: {result['message']}")
        else:
            print(f"     ❌ 连接失败: {result['message']}")

def clean_all_data():
    """清理所有数据"""
    app = create_app()

    with app.app_context():
        try:
            print("🗑️ 清理所有数据...")

            # 删除所有数据（按依赖关系顺序）
            SyncData.query.delete()
            Task.query.delete()
            Account.query.delete()
            Log.query.delete()
            Instance.query.delete()
            Credential.query.delete()
            User.query.delete()
            GlobalParam.query.delete()

            db.session.commit()
            print("✅ 所有数据已清理")

        except Exception as e:
            print(f"❌ 数据清理失败: {e}")
            raise

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='泰摸鱼吧数据初始化工具')
    parser.add_argument('--init-all', action='store_true', help='初始化所有数据')
    parser.add_argument('--init-global-params', action='store_true', help='初始化全局参数')
    parser.add_argument('--init-instances', action='store_true', help='初始化实例')
    parser.add_argument('--init-credentials', action='store_true', help='初始化凭据')
    parser.add_argument('--init-accounts', action='store_true', help='初始化账户数据')
    parser.add_argument('--validate-all', action='store_true', help='验证所有连接')
    parser.add_argument('--clean-all', action='store_true', help='清理所有数据')

    args = parser.parse_args()

    if args.init_all:
        init_all_data()
    elif args.init_global_params:
        app = create_app()
        with app.app_context():
            init_global_params()
    elif args.init_instances:
        app = create_app()
        with app.app_context():
            init_sample_instances()
    elif args.init_credentials:
        app = create_app()
        with app.app_context():
            init_sample_credentials()
    elif args.init_accounts:
        print("⚠️ 账户数据需要从真实数据库同步，请先配置实例连接")
    elif args.validate_all:
        app = create_app()
        with app.app_context():
            validate_connections()
    elif args.clean_all:
        clean_all_data()
    else:
        print("请指定操作参数")
        print("示例: python scripts/init_data.py --init-all")
