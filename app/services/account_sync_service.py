"""
泰摸鱼吧 - 账户同步服务
统一处理手动同步和定时任务的账户同步逻辑
"""

import pymysql
import logging

# 可选导入数据库驱动
try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import cx_Oracle
except ImportError:
    cx_Oracle = None
from typing import Dict, Any, Optional, List, Tuple
from app.models import Instance, Credential
from app.models.account import Account
from app import db
from datetime import datetime
from app.utils.timezone import now

class AccountSyncService:
    """账户同步服务 - 统一处理所有账户同步逻辑"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def sync_accounts(self, instance: Instance, sync_type: str = 'batch') -> Dict[str, Any]:
        """
        同步账户信息 - 统一入口
        
        Args:
            instance: 数据库实例
            sync_type: 同步类型 ('batch' 或 'task')
            
        Returns:
            Dict: 同步结果
        """
        try:
            # 获取数据库连接
            conn = self._get_connection(instance)
            if not conn:
                return {
                    'success': False,
                    'error': '无法获取数据库连接'
                }
            
            # 记录同步前的账户数量
            before_count = Account.query.filter_by(instance_id=instance.id).count()
            
            # 获取同步前的账户快照
            before_accounts = self._get_account_snapshot(instance)
            
            synced_count = 0
            added_count = 0
            removed_count = 0
            modified_count = 0
            
            # 根据数据库类型执行同步
            if instance.db_type == 'mysql':
                result = self._sync_mysql_accounts(instance, conn)
            elif instance.db_type == 'postgresql':
                result = self._sync_postgresql_accounts(instance, conn)
            elif instance.db_type == 'sqlserver':
                result = self._sync_sqlserver_accounts(instance, conn)
            elif instance.db_type == 'oracle':
                result = self._sync_oracle_accounts(instance, conn)
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {instance.db_type}'
                }
            
            synced_count = result['synced_count']
            added_count = result['added_count']
            removed_count = result['removed_count']
            modified_count = result['modified_count']
            
            # 计算变化
            after_count = Account.query.filter_by(instance_id=instance.id).count()
            net_change = after_count - before_count
            
            return {
                'success': True,
                'message': f'成功同步 {synced_count} 个{instance.db_type.upper()}账户',
                'synced_count': synced_count,
                'added_count': added_count,
                'removed_count': removed_count,
                'modified_count': modified_count,
                'net_change': net_change
            }
            
        except Exception as e:
            self.logger.error(f"账户同步失败: {str(e)}")
            return {
                'success': False,
                'error': f'{instance.db_type.upper()}账户同步失败: {str(e)}',
                'synced_count': 0
            }
    
    def _get_connection(self, instance: Instance):
        """获取数据库连接"""
        try:
            if instance.db_type == 'mysql':
                return pymysql.connect(
                    host=instance.host,
                    port=instance.port,
                    database=instance.database_name or 'mysql',
                    user=instance.credential.username,
                    password=instance.credential.get_plain_password()
                )
            elif instance.db_type == 'postgresql':
                if psycopg2 is None:
                    raise ImportError("psycopg2模块未安装，无法连接PostgreSQL")
                return psycopg2.connect(
                    host=instance.host,
                    port=instance.port,
                    database=instance.database_name or 'postgres',
                    user=instance.credential.username,
                    password=instance.credential.get_plain_password()
                )
            elif instance.db_type == 'sqlserver':
                # 优先使用pymssql连接SQL Server
                try:
                    import pymssql
                    return pymssql.connect(
                        server=instance.host,
                        port=instance.port,
                        database=instance.database_name or 'master',
                        user=instance.credential.username,
                        password=instance.credential.get_plain_password()
                    )
                except ImportError:
                    # 如果pymssql不可用，尝试pyodbc
                    if pyodbc is None:
                        raise ImportError("SQL Server驱动未安装，请安装pymssql或pyodbc")
                    
                    # 尝试pyodbc连接
                    conn_str = self._get_sqlserver_pyodbc_connection(instance)
                    if conn_str:
                        return pyodbc.connect(conn_str)
                    else:
                        raise ImportError("SQL Server驱动配置错误")
                
            elif instance.db_type == 'oracle':
                if cx_Oracle is None:
                    raise ImportError("cx_Oracle模块未安装，无法连接Oracle")
                return cx_Oracle.connect(
                    instance.credential.username,
                    instance.credential.get_plain_password(),
                    f"{instance.host}:{instance.port}/{instance.database_name or 'xe'}"
                )
            else:
                return None
        except Exception as e:
            self.logger.error(f"数据库连接失败: {str(e)}")
            return None
    
    def _get_sqlserver_pyodbc_connection(self, instance: Instance):
        """获取SQL Server pyodbc连接字符串"""
        if pyodbc is None:
            return None
        
        # 尝试不同的ODBC驱动
        drivers = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server", 
            "SQL Server",
            "SQL Server Native Client 11.0"
        ]
        
        for driver in drivers:
            try:
                # 检查驱动是否可用
                if driver in pyodbc.drivers():
                    return (
                        f"DRIVER={{{driver}}};"
                        f"SERVER={instance.host},{instance.port};"
                        f"DATABASE={instance.database_name or 'master'};"
                        f"UID={instance.credential.username};"
                        f"PWD={instance.credential.get_plain_password()}"
                    )
            except:
                continue
        
        return None
    
    def _get_sqlserver_pymssql_connection(self, instance: Instance):
        """获取SQL Server pymssql连接参数"""
        try:
            import pymssql
            return {
                'server': instance.host,
                'port': instance.port,
                'database': instance.database_name or 'master',
                'user': instance.credential.username,
                'password': instance.credential.get_plain_password()
            }
        except ImportError:
            return None
    
    def _get_account_snapshot(self, instance: Instance) -> Dict[str, Dict]:
        """获取同步前的账户快照"""
        before_accounts = {}
        existing_accounts = Account.query.filter_by(instance_id=instance.id).all()
        for account in existing_accounts:
            key = f"{account.username}@{account.host}"
            before_accounts[key] = {
                'id': account.id,
                'username': account.username,
                'host': account.host,
                'database_name': account.database_name,
                'account_type': account.account_type,
                'plugin': account.plugin,
                'password_expired': account.password_expired,
                'password_last_changed': account.password_last_changed.isoformat() if account.password_last_changed else None,
                'is_locked': account.is_locked,
                'is_active': account.is_active,
                'last_login': account.last_login.isoformat() if account.last_login else None
            }
        return before_accounts
    
    def _sync_mysql_accounts(self, instance: Instance, conn) -> Dict[str, int]:
        """同步MySQL账户"""
        cursor = conn.cursor()
        
        # 查询用户信息 - 包含完整的账户信息
        cursor.execute("""
            SELECT 
                User as username,
                Host as host,
                'user' as account_type,
                '' as database_name,
                plugin as plugin,
                password_expired as password_expired,
                password_last_changed as password_last_changed,
                account_locked as account_locked,
                password_lifetime as password_lifetime,
                Select_priv as can_select,
                Insert_priv as can_insert,
                Update_priv as can_update,
                Delete_priv as can_delete,
                Create_priv as can_create,
                Drop_priv as can_drop,
                Super_priv as is_superuser
            FROM mysql.user
            WHERE User NOT LIKE 'mysql.%'
            ORDER BY User, Host
        """)
        
        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        modified_count = 0
        
        for account_data in accounts:
            (username, host, account_type, database_name, plugin, password_expired, 
             password_last_changed, account_locked, password_lifetime, can_select, 
             can_insert, can_update, can_delete, can_create, can_drop, is_superuser) = account_data
            
            # 查找或创建账户记录
            account = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host=host
            ).first()
            
            # 处理插件信息
            plugin_name = plugin if plugin else 'mysql_native_password'
            
            # 处理密码过期状态
            is_password_expired = password_expired == 'Y' if password_expired else False
            
            # 处理锁定状态
            is_locked = account_locked == 'Y' if account_locked else False
            
            # 处理密码最后修改时间
            password_changed = None
            if password_last_changed:
                try:
                    password_changed = password_last_changed
                except:
                    password_changed = None
            
            if not account:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host=host,
                    database_name=database_name,
                    account_type=account_type,
                    plugin=plugin_name,
                    password_expired=is_password_expired,
                    password_last_changed=password_changed,
                    is_locked=is_locked,
                    is_active=not is_locked
                )
                db.session.add(account)
                added_count += 1
            else:
                # 检查是否有变化
                has_changes = False
                if account.database_name != database_name:
                    account.database_name = database_name
                    has_changes = True
                if account.account_type != account_type:
                    account.account_type = account_type
                    has_changes = True
                if account.plugin != plugin_name:
                    account.plugin = plugin_name
                    has_changes = True
                if account.password_expired != is_password_expired:
                    account.password_expired = is_password_expired
                    has_changes = True
                if account.password_last_changed != password_changed:
                    account.password_last_changed = password_changed
                    has_changes = True
                if account.is_locked != is_locked:
                    account.is_locked = is_locked
                    has_changes = True
                if account.is_active != (not is_locked):
                    account.is_active = not is_locked
                    has_changes = True
                
                if has_changes:
                    account.updated_at = now()
                    modified_count += 1
            
            synced_count += 1
        
        # 删除服务器端不存在的本地账户
        server_accounts = set()
        for account_data in accounts:
            username, host, account_type, database_name, plugin_name, password_expired, password_last_changed, account_locked, password_lifetime, can_select, can_insert, can_update, can_delete, can_create, can_drop, is_superuser = account_data
            server_accounts.add((username, host))
        
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []
        
        for local_account in local_accounts:
            if (local_account.username, local_account.host) not in server_accounts:
                removed_accounts.append({
                    'username': local_account.username,
                    'host': local_account.host,
                    'database_name': local_account.database_name,
                    'account_type': local_account.account_type,
                    'plugin': local_account.plugin,
                    'password_expired': local_account.password_expired,
                    'password_last_changed': local_account.password_last_changed.isoformat() if local_account.password_last_changed else None,
                    'is_locked': local_account.is_locked,
                    'is_active': local_account.is_active
                })
                db.session.delete(local_account)
                removed_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'synced_count': synced_count,
            'added_count': added_count,
            'removed_count': removed_count,
            'modified_count': modified_count,
            'removed_accounts': removed_accounts
        }
    
    def _sync_postgresql_accounts(self, instance: Instance, conn) -> Dict[str, int]:
        """同步PostgreSQL账户"""
        cursor = conn.cursor()
        
        # 查询用户信息
        cursor.execute("""
            SELECT 
                usename as username,
                'user' as account_type,
                '' as database_name,
                usesuper as is_superuser,
                usecreatedb as can_create_db,
                usebypassrls as can_bypass_rls
            FROM pg_user
            ORDER BY usename
        """)
        
        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        modified_count = 0
        
        for account_data in accounts:
            username, account_type, database_name, is_superuser, can_create_db, can_bypass_rls = account_data
            
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
                added_count += 1
            else:
                # 检查是否有变化
                if (account.database_name != database_name or 
                    account.account_type != account_type):
                    account.database_name = database_name
                    account.account_type = account_type
                    account.updated_at = now()
                    modified_count += 1
            
            synced_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'synced_count': synced_count,
            'added_count': added_count,
            'removed_count': 0,
            'modified_count': modified_count
        }
    
    def _sync_sqlserver_accounts(self, instance: Instance, conn) -> Dict[str, int]:
        """同步SQL Server账户"""
        cursor = conn.cursor()
        
        # 查询用户信息
        cursor.execute("""
            SELECT 
                name as username,
                'user' as account_type,
                '' as database_name,
                is_disabled as is_disabled,
                create_date as created_date
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G')
            AND name NOT LIKE '##%'
            ORDER BY name
        """)
        
        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        removed_count = 0
        modified_count = 0
        
        for account_data in accounts:
            username, account_type, database_name, is_disabled, created_date = account_data
            
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
                    is_active=not is_disabled
                )
                db.session.add(account)
                added_count += 1
            else:
                # 检查是否有变化
                if (account.database_name != database_name or 
                    account.account_type != account_type or
                    account.is_active != (not is_disabled)):
                    account.database_name = database_name
                    account.account_type = account_type
                    account.is_active = not is_disabled
                    account.updated_at = now()
                    modified_count += 1
            
            synced_count += 1
        
        # 删除服务器端不存在的本地账户
        server_accounts = set()
        for account_data in accounts:
            username, account_type, database_name, is_disabled, created_date = account_data
            server_accounts.add(username)
        
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []
        
        for local_account in local_accounts:
            if local_account.username not in server_accounts:
                removed_accounts.append({
                    'username': local_account.username,
                    'host': local_account.host,
                    'database_name': local_account.database_name,
                    'account_type': local_account.account_type,
                    'plugin': local_account.plugin,
                    'password_expired': local_account.password_expired,
                    'password_last_changed': local_account.password_last_changed.isoformat() if local_account.password_last_changed else None,
                    'is_locked': local_account.is_locked,
                    'is_active': local_account.is_active
                })
                db.session.delete(local_account)
                removed_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'synced_count': synced_count,
            'added_count': added_count,
            'removed_count': removed_count,
            'modified_count': modified_count,
            'removed_accounts': removed_accounts
        }
    
    def _sync_oracle_accounts(self, instance: Instance, conn) -> Dict[str, int]:
        """同步Oracle账户"""
        cursor = conn.cursor()
        
        # 查询用户信息
        cursor.execute("""
            SELECT 
                username,
                'user' as account_type,
                '' as database_name,
                account_status,
                created,
                expiry_date
            FROM dba_users
            WHERE username NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DIP', 'TSMSYS', 'DBSNMP', 'WMSYS', 'EXFSYS', 'CTXSYS', 'XDB', 'ANONYMOUS', 'ORDPLUGINS', 'ORDSYS', 'SI_INFORMTN_SCHEMA', 'MDSYS', 'OLAPSYS', 'MDDATA', 'SPATIAL_CSW_ADMIN_USR', 'SPATIAL_WFS_ADMIN_USR')
            ORDER BY username
        """)
        
        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        modified_count = 0
        
        for account_data in accounts:
            username, account_type, database_name, account_status, created, expiry_date = account_data
            
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
                    is_active=account_status == 'OPEN'
                )
                db.session.add(account)
                added_count += 1
            else:
                # 检查是否有变化
                is_active = account_status == 'OPEN'
                if (account.database_name != database_name or 
                    account.account_type != account_type or
                    account.is_active != is_active):
                    account.database_name = database_name
                    account.account_type = account_type
                    account.is_active = is_active
                    account.updated_at = now()
                    modified_count += 1
            
            synced_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'synced_count': synced_count,
            'added_count': added_count,
            'removed_count': 0,
            'modified_count': modified_count
        }

# 全局实例
account_sync_service = AccountSyncService()
