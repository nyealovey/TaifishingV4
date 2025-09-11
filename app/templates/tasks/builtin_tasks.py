from app.utils.timezone import now

# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 内置任务模板
包含各种数据库类型的同步任务模板
"""

# PostgreSQL 账户同步任务
POSTGRESQL_SYNC_ACCOUNTS = """
def sync_postgresql_accounts(instance, config):
    \"\"\"
    同步PostgreSQL数据库账户信息
    
    Args:
        instance: 数据库实例对象
        config: 任务配置参数
    
    Returns:
        dict: 同步结果
    \"\"\"
    import psycopg
    from app.models.account import Account
    from app import db
    from datetime import datetime
    
    try:
        # 连接数据库
        conn = psycopg.connect(
            host=instance.host,
            port=instance.port,
            database=instance.database_name or 'postgres',
            user=instance.credential.username,
            password=instance.credential.password
        )
        
        cursor = conn.cursor()
        
        # 查询用户信息
        cursor.execute(\"\"\"
            SELECT 
                usename as username,
                'user' as account_type,
                datname as database_name,
                CASE WHEN usesuper THEN 'superuser' ELSE 'user' END as role_type,
                uselock as is_locked,
                usecreatedb as can_create_db,
                usesuper as is_superuser
            FROM pg_user u
            LEFT JOIN pg_database d ON u.usesysid = d.datdba
            WHERE usename NOT LIKE 'pg_%'
            ORDER BY usename
        \"\"\")
        
        accounts = cursor.fetchall()
        synced_count = 0
        
        for account_data in accounts:
            username, account_type, database_name, role_type, is_locked, can_create_db, is_superuser = account_data
            
            # 查找或创建账户记录
            account = Account.query.filter_by(
                instance_id=instance.id,
                username=username
            ).first()
            
            if not account:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    database_name=database_name,
                    account_type=account_type,
                    is_active=not is_locked
                )
                db.session.add(account)
            else:
                account.database_name = database_name
                account.account_type = account_type
                account.is_active = not is_locked
                account.updated_at = now()
            
            synced_count += 1
        
        db.session.commit()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'成功同步 {synced_count} 个PostgreSQL账户',
            'synced_count': synced_count
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'PostgreSQL账户同步失败: {str(e)}',
            'synced_count': 0
        }
"""

# MySQL 账户同步任务
MYSQL_SYNC_ACCOUNTS = """
def sync_mysql_accounts(instance, config):
    \"\"\"
    同步MySQL数据库账户信息
    
    Args:
        instance: 数据库实例对象
        config: 任务配置参数
    
    Returns:
        dict: 同步结果
    \"\"\"
    import pymysql
    from app.models.account import Account
    from app import db
    from datetime import datetime
    
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=instance.host,
            port=instance.port,
            database=instance.database_name or 'mysql',
            user=instance.credential.username,
            password=instance.credential.password
        )
        
        cursor = conn.cursor()
        
        # 查询用户信息
        cursor.execute(\"\"\"
            SELECT 
                User as username,
                'user' as account_type,
                Db as database_name,
                Select_priv as can_select,
                Insert_priv as can_insert,
                Update_priv as can_update,
                Delete_priv as can_delete,
                Create_priv as can_create,
                Drop_priv as can_drop,
                Super_priv as is_superuser
            FROM mysql.user
            WHERE User NOT LIKE 'mysql.%'
            ORDER BY User
        \"\"\")
        
        accounts = cursor.fetchall()
        synced_count = 0
        
        for account_data in accounts:
            username, account_type, database_name, can_select, can_insert, can_update, can_delete, can_create, can_drop, is_superuser = account_data
            
            # 查找或创建账户记录
            account = Account.query.filter_by(
                instance_id=instance.id,
                username=username
            ).first()
            
            if not account:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    database_name=database_name,
                    account_type=account_type,
                    is_active=True
                )
                db.session.add(account)
            else:
                account.database_name = database_name
                account.account_type = account_type
                account.updated_at = now()
            
            synced_count += 1
        
        db.session.commit()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'成功同步 {synced_count} 个MySQL账户',
            'synced_count': synced_count
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'MySQL账户同步失败: {str(e)}',
            'synced_count': 0
        }
"""

# PostgreSQL 版本同步任务
POSTGRESQL_SYNC_VERSION = """
def sync_postgresql_version(instance, config):
    \"\"\"
    同步PostgreSQL数据库版本信息
    
    Args:
        instance: 数据库实例对象
        config: 任务配置参数
    
    Returns:
        dict: 同步结果
    \"\"\"
    import psycopg
    from app.models.instance import Instance
    from app import db
    from datetime import datetime
    
    try:
        # 连接数据库
        conn = psycopg.connect(
            host=instance.host,
            port=instance.port,
            database=instance.database_name or 'postgres',
            user=instance.credential.username,
            password=instance.credential.password
        )
        
        cursor = conn.cursor()
        
        # 查询版本信息
        cursor.execute(\"SELECT version()\")
        version_info = cursor.fetchone()[0]
        
        # 解析版本号
        version_parts = version_info.split()
        version = version_parts[1] if len(version_parts) > 1 else 'Unknown'
        
        # 更新实例信息
        instance.tags = instance.tags or {}
        instance.tags['version'] = version
        instance.tags['version_info'] = version_info
        instance.tags['last_version_sync'] = now().isoformat()
        instance.updated_at = now()
        
        db.session.commit()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'成功同步PostgreSQL版本: {version}',
            'version': version
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'PostgreSQL版本同步失败: {str(e)}'
        }
"""

# MySQL 版本同步任务
MYSQL_SYNC_VERSION = """
def sync_mysql_version(instance, config):
    \"\"\"
    同步MySQL数据库版本信息
    
    Args:
        instance: 数据库实例对象
        config: 任务配置参数
    
    Returns:
        dict: 同步结果
    \"\"\"
    import pymysql
    from app.models.instance import Instance
    from app import db
    from datetime import datetime
    
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=instance.host,
            port=instance.port,
            database=instance.database_name or 'mysql',
            user=instance.credential.username,
            password=instance.credential.password
        )
        
        cursor = conn.cursor()
        
        # 查询版本信息
        cursor.execute(\"SELECT VERSION()\")
        version_info = cursor.fetchone()[0]
        
        # 解析版本号
        version_parts = version_info.split('-')
        version = version_parts[0] if version_parts else 'Unknown'
        
        # 更新实例信息
        instance.tags = instance.tags or {}
        instance.tags['version'] = version
        instance.tags['version_info'] = version_info
        instance.tags['last_version_sync'] = now().isoformat()
        instance.updated_at = now()
        
        db.session.commit()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'成功同步MySQL版本: {version}',
            'version': version
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'MySQL版本同步失败: {str(e)}'
        }
"""

# PostgreSQL 数据库大小同步任务
POSTGRESQL_SYNC_SIZE = """
def sync_postgresql_size(instance, config):
    \"\"\"
    同步PostgreSQL数据库大小信息
    
    Args:
        instance: 数据库实例对象
        config: 任务配置参数
    
    Returns:
        dict: 同步结果
    \"\"\"
    import psycopg
    from app.models.instance import Instance
    from app import db
    from datetime import datetime
    
    try:
        # 连接数据库
        conn = psycopg.connect(
            host=instance.host,
            port=instance.port,
            database=instance.database_name or 'postgres',
            user=instance.credential.username,
            password=instance.credential.password
        )
        
        cursor = conn.cursor()
        
        # 查询数据库大小
        cursor.execute(\"\"\"
            SELECT 
                pg_database.datname,
                pg_size_pretty(pg_database_size(pg_database.datname)) as size_pretty,
                pg_database_size(pg_database.datname) as size_bytes
            FROM pg_database
            WHERE datname = current_database()
        \"\"\")
        
        size_info = cursor.fetchone()
        if size_info:
            db_name, size_pretty, size_bytes = size_info
            
            # 更新实例信息
            instance.tags = instance.tags or {}
            instance.tags['database_size'] = size_pretty
            instance.tags['database_size_bytes'] = size_bytes
            instance.tags['last_size_sync'] = now().isoformat()
            instance.updated_at = now()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功同步PostgreSQL数据库大小: {size_pretty}',
                'size': size_pretty,
                'size_bytes': size_bytes
            }
        else:
            return {
                'success': False,
                'error': '无法获取数据库大小信息'
            }
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        return {
            'success': False,
            'error': f'PostgreSQL数据库大小同步失败: {str(e)}'
        }
"""

# MySQL 数据库大小同步任务
MYSQL_SYNC_SIZE = """
def sync_mysql_size(instance, config):
    \"\"\"
    同步MySQL数据库大小信息
    
    Args:
        instance: 数据库实例对象
        config: 任务配置参数
    
    Returns:
        dict: 同步结果
    \"\"\"
    import pymysql
    from app.models.instance import Instance
    from app import db
    from datetime import datetime
    
    try:
        # 连接数据库
        conn = pymysql.connect(
            host=instance.host,
            port=instance.port,
            database=instance.database_name or 'mysql',
            user=instance.credential.username,
            password=instance.credential.password
        )
        
        cursor = conn.cursor()
        
        # 查询数据库大小
        cursor.execute(\"\"\"
            SELECT 
                table_schema as database_name,
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb,
                ROUND(SUM(data_length + index_length) / 1024 / 1024 / 1024, 2) as size_gb
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            GROUP BY table_schema
        \"\"\")
        
        size_info = cursor.fetchone()
        if size_info:
            db_name, size_mb, size_gb = size_info
            size_pretty = f\"{size_gb} GB\" if size_gb >= 1 else f\"{size_mb} MB\"
            
            # 更新实例信息
            instance.tags = instance.tags or {}
            instance.tags['database_size'] = size_pretty
            instance.tags['database_size_mb'] = size_mb
            instance.tags['database_size_gb'] = size_gb
            instance.tags['last_size_sync'] = now().isoformat()
            instance.updated_at = now()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'成功同步MySQL数据库大小: {size_pretty}',
                'size': size_pretty,
                'size_mb': size_mb,
                'size_gb': size_gb
            }
        else:
            return {
                'success': False,
                'error': '无法获取数据库大小信息'
            }
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        return {
            'success': False,
            'error': f'MySQL数据库大小同步失败: {str(e)}'
        }
"""

# 内置任务配置
BUILTIN_TASKS = [
    {
        "name": "PostgreSQL账户同步",
        "task_type": "sync_accounts",
        "db_type": "postgresql",
        "description": "同步PostgreSQL数据库用户账户信息",
        "python_code": POSTGRESQL_SYNC_ACCOUNTS,
        "config": {"enabled": True, "sync_roles": True, "sync_permissions": True},
        "schedule": "0 */6 * * *",  # 每6小时执行一次
    },
    {
        "name": "MySQL账户同步",
        "task_type": "sync_accounts",
        "db_type": "mysql",
        "description": "同步MySQL数据库用户账户信息",
        "python_code": MYSQL_SYNC_ACCOUNTS,
        "config": {"enabled": True, "sync_privileges": True},
        "schedule": "0 */6 * * *",  # 每6小时执行一次
    },
    {
        "name": "PostgreSQL版本同步",
        "task_type": "sync_version",
        "db_type": "postgresql",
        "description": "同步PostgreSQL数据库版本信息",
        "python_code": POSTGRESQL_SYNC_VERSION,
        "config": {"enabled": True},
        "schedule": "0 0 * * *",  # 每天执行一次
    },
    {
        "name": "MySQL版本同步",
        "task_type": "sync_version",
        "db_type": "mysql",
        "description": "同步MySQL数据库版本信息",
        "python_code": MYSQL_SYNC_VERSION,
        "config": {"enabled": True},
        "schedule": "0 0 * * *",  # 每天执行一次
    },
    {
        "name": "PostgreSQL数据库大小同步",
        "task_type": "sync_size",
        "db_type": "postgresql",
        "description": "同步PostgreSQL数据库大小信息",
        "python_code": POSTGRESQL_SYNC_SIZE,
        "config": {"enabled": True},
        "schedule": "0 2 * * *",  # 每天凌晨2点执行
    },
    {
        "name": "MySQL数据库大小同步",
        "task_type": "sync_size",
        "db_type": "mysql",
        "description": "同步MySQL数据库大小信息",
        "python_code": MYSQL_SYNC_SIZE,
        "config": {"enabled": True},
        "schedule": "0 2 * * *",  # 每天凌晨2点执行
    },
]
