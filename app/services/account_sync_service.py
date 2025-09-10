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
    import oracledb
except ImportError:
    oracledb = None
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
                if oracledb is None:
                    raise ImportError("oracledb模块未安装，无法连接Oracle")
                
                # 优先使用Thick模式连接（适用于所有Oracle版本，包括11g）
                try:
                    # 初始化Thick模式（需要Oracle Instant Client）
                    oracledb.init_oracle_client()
                    return oracledb.connect(
                        user=instance.credential.username,
                        password=instance.credential.get_plain_password(),
                        dsn=f"{instance.host}:{instance.port}/{instance.database_name or 'ORCL'}"
                    )
                except oracledb.DatabaseError as e:
                    # 如果Thick模式失败，尝试Thin模式（适用于Oracle 12c+）
                    if "DPI-1047" in str(e) or "Oracle Client library" in str(e):
                        # Thick模式失败，尝试Thin模式
                        try:
                            return oracledb.connect(
                                user=instance.credential.username,
                                password=instance.credential.get_plain_password(),
                                dsn=f"{instance.host}:{instance.port}/{instance.database_name or 'ORCL'}"
                            )
                        except oracledb.DatabaseError as thin_error:
                            # 如果Thin模式也失败，抛出原始错误
                            raise e
                    else:
                        raise
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
        removed_count = 0
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
            
            # 获取完整权限信息
            permissions_info = self._get_mysql_account_permissions(conn, username, host)
            
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
                    is_active=not is_locked,
                    permissions=permissions_info['permissions_json'],
                    is_superuser=permissions_info['is_superuser'],
                    can_grant=permissions_info['can_grant']
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
                
                # 更新权限信息
                if account.permissions != permissions_info['permissions_json']:
                    account.permissions = permissions_info['permissions_json']
                    has_changes = True
                if account.is_superuser != permissions_info['is_superuser']:
                    account.is_superuser = permissions_info['is_superuser']
                    has_changes = True
                if account.can_grant != permissions_info['can_grant']:
                    account.can_grant = permissions_info['can_grant']
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
        
        # 查询角色信息（PostgreSQL中用户和角色是同一个概念）
        cursor.execute("""
            SELECT 
                rolname as username,
                rolsuper as is_superuser,
                rolinherit as can_inherit,
                rolcreaterole as can_create_role,
                rolcreatedb as can_create_db,
                rolcanlogin as can_login,
                rolconnlimit as conn_limit,
                rolvaliduntil as valid_until,
                rolbypassrls as can_bypass_rls,
                rolreplication as can_replicate
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%' 
            AND rolname NOT IN ('rdsadmin', 'rds_superuser')
            ORDER BY rolname
        """)
        
        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        modified_count = 0
        removed_count = 0
        
        # 记录服务器端的账户
        server_accounts = set()
        
        for account_data in accounts:
            (username, is_superuser, can_inherit, can_create_role, can_create_db, 
             can_login, conn_limit, valid_until, can_bypass_rls, can_replicate) = account_data
            
            # 记录服务器端的账户（PostgreSQL没有主机概念）
            server_accounts.add((username, ''))
            
            # 确定账户类型（PostgreSQL中用户和角色是同一个概念）
            if is_superuser:
                account_type = 'role'  # 超级用户角色
            elif can_create_db or can_create_role:
                account_type = 'role'  # 管理员角色
            else:
                account_type = 'user'  # 普通用户
            
            # 检查密码是否过期
            password_expired = valid_until is not None and valid_until < now()
            
            # 检查账户是否被锁定
            is_locked = not can_login
            
            # 检查账户是否活跃
            is_active = can_login and not password_expired
            
            # 查找或创建账户记录
            account = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host=''  # PostgreSQL没有主机概念
            ).first()
            
            if not account:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host='',  # PostgreSQL没有主机概念
                    database_name='postgres',  # PostgreSQL默认数据库
                    account_type=account_type,
                    is_superuser=is_superuser,
                    is_active=is_active,
                    is_locked=is_locked,
                    password_expired=password_expired,
                    created_at=now(),
                    updated_at=now()
                )
                db.session.add(account)
                added_count += 1
            else:
                # 检查是否有变化
                changes = False
                if account.account_type != account_type:
                    account.account_type = account_type
                    changes = True
                if account.is_superuser != is_superuser:
                    account.is_superuser = is_superuser
                    changes = True
                if account.is_active != is_active:
                    account.is_active = is_active
                    changes = True
                if account.is_locked != is_locked:
                    account.is_locked = is_locked
                    changes = True
                if account.password_expired != password_expired:
                    account.password_expired = password_expired
                    changes = True
                
                if changes:
                    account.updated_at = now()
                    modified_count += 1
            
            synced_count += 1
            
            # 获取账户权限
            try:
                permissions = self._get_postgresql_account_permissions(instance, conn, username)
                if permissions:
                    import json
                    account.permissions = json.dumps(permissions)
                    # 更新权限相关字段
                    account.is_superuser = permissions.get('is_superuser', False)
                    account.can_grant = permissions.get('can_grant', False)
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL账户 {username} 权限失败: {e}")
        
        # 删除服务器端不存在的账户
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        for account in local_accounts:
            if (account.username, account.host) not in server_accounts:
                db.session.delete(account)
                removed_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'synced_count': synced_count,
            'added_count': added_count,
            'removed_count': removed_count,
            'modified_count': modified_count
        }
    
    def _get_postgresql_account_permissions(self, instance: Instance, conn, username: str) -> Dict[str, Any]:
        """获取PostgreSQL账户权限 - 根据新的权限配置结构"""
        import json
        cursor = conn.cursor()
        permissions = {
            'predefined_roles': [],
            'role_attributes': [],
            'database_privileges': [],
            'tablespace_privileges': []
        }
        
        try:
            self.logger.info(f"开始获取PostgreSQL用户 {username} 的权限信息")
            
            # 首先检查用户是否存在
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
            if not cursor.fetchone():
                self.logger.warning(f"PostgreSQL用户 {username} 不存在")
                return permissions
            
            self.logger.info(f"PostgreSQL用户 {username} 存在，继续获取权限")
            
            # 获取预定义角色成员身份
            try:
                cursor.execute("""
                    SELECT r.rolname
                    FROM pg_roles r
                    JOIN pg_auth_members m ON r.oid = m.roleid
                    JOIN pg_roles u ON m.member = u.oid
                    WHERE u.rolname = %s
                    AND r.rolname LIKE 'pg_%'
                    ORDER BY r.rolname
                """, (username,))
                
                predefined_roles = cursor.fetchall()
                for role in predefined_roles:
                    permissions['predefined_roles'].append(role[0])
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 预定义角色失败: {e}")
            
            # 获取角色属性
            try:
                cursor.execute("""
                    SELECT 
                        rolsuper, rolcreatedb, rolcreaterole, rolinherit, 
                        rolcanlogin, rolreplication, rolbypassrls
                    FROM pg_roles 
                    WHERE rolname = %s
                """, (username,))
                
                role_attrs = cursor.fetchone()
                if role_attrs:
                    is_super, can_create_db, can_create_role, can_inherit, can_login, can_replicate, can_bypass_rls = role_attrs
                    
                    if is_super:
                        permissions['role_attributes'].append('SUPERUSER')
                    if can_create_db:
                        permissions['role_attributes'].append('CREATEDB')
                    if can_create_role:
                        permissions['role_attributes'].append('CREATEROLE')
                    if can_inherit:
                        permissions['role_attributes'].append('INHERIT')
                    if can_login:
                        permissions['role_attributes'].append('LOGIN')
                    if can_replicate:
                        permissions['role_attributes'].append('REPLICATION')
                    if can_bypass_rls:
                        permissions['role_attributes'].append('BYPASSRLS')
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 角色属性失败: {e}")
            
            # 获取数据库权限（简化版本）
            try:
                # PostgreSQL默认使用'postgres'数据库进行权限查询
                # 因为PostgreSQL实例创建时没有要求填写database_name字段
                current_db = 'postgres'
                self.logger.info(f"PostgreSQL用户 {username} 权限查询使用默认数据库: {current_db}")
                
                cursor.execute("""
                    SELECT 
                        CASE WHEN has_database_privilege(%s, %s, 'CONNECT') THEN 'CONNECT' END,
                        CASE WHEN has_database_privilege(%s, %s, 'CREATE') THEN 'CREATE' END,
                        CASE WHEN has_database_privilege(%s, %s, 'TEMPORARY') THEN 'TEMPORARY' END
                """, (username, current_db, username, current_db, username, current_db))
                
                row = cursor.fetchone()
                if row:
                    connect, create, temp = row
                    if connect:
                        permissions['database_privileges'].append('CONNECT')
                    if create:
                        permissions['database_privileges'].append('CREATE')
                    if temp:
                        permissions['database_privileges'].append('TEMPORARY')
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 数据库权限失败: {e}")
            
            # 获取表空间权限
            try:
                cursor.execute("""
                    SELECT 
                        CASE WHEN has_tablespace_privilege(%s, 'pg_default', 'CREATE') THEN 'CREATE' END
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    create = row[0]
                    if create:
                        permissions['tablespace_privileges'].append('CREATE')
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 表空间权限失败: {e}")
            
            # 确定是否为超级用户和是否可以授权
            is_superuser = 'SUPERUSER' in permissions['role_attributes']
            can_grant = is_superuser or 'CREATEROLE' in permissions['role_attributes']
            
            permissions['is_superuser'] = is_superuser
            permissions['can_grant'] = can_grant
            
            self.logger.info(f"PostgreSQL用户 {username} 权限获取成功: {permissions}")
            
        except Exception as e:
            self.logger.error(f"获取PostgreSQL账户 {username} 权限失败: {e}")
            # 返回基本权限结构而不是空字典
            permissions['is_superuser'] = False
            permissions['can_grant'] = False
        finally:
            cursor.close()
        
        return permissions
    
    def _sync_sqlserver_accounts(self, instance: Instance, conn) -> Dict[str, int]:
        """同步SQL Server账户"""
        cursor = conn.cursor()
        
        # 查询用户信息 - 只同步sa和用户创建的账户，排除内置账户
        cursor.execute("""
            SELECT 
                name as username,
                type_desc as account_type,
                '' as database_name,
                is_disabled as is_disabled,
                create_date as created_date
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G')
            AND name NOT LIKE '##%'
            AND name NOT LIKE 'NT SERVICE\\%'
            AND name NOT LIKE 'NT AUTHORITY\\%'
            AND name NOT LIKE 'BUILTIN\\%'
            AND name NOT IN ('public', 'guest', 'dbo')
            AND (name = 'sa' OR name NOT LIKE 'NT %')
            ORDER BY name
        """)
        
        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        removed_count = 0
        modified_count = 0
        
        for account_data in accounts:
            username, account_type, database_name, is_disabled, created_date = account_data
            
            # 直接使用SQL Server的原始type_desc名称
            account_type = account_type.lower()
            
            # 获取权限信息
            permissions_info = self._get_sqlserver_account_permissions(conn, username)
            
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
                    is_active=not is_disabled,
                    permissions=permissions_info['permissions_json'],
                    is_superuser=permissions_info['is_superuser'],
                    can_grant=permissions_info['can_grant']
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
                if account.is_active != (not is_disabled):
                    account.is_active = not is_disabled
                    has_changes = True
                
                # 更新权限信息
                if account.permissions != permissions_info['permissions_json']:
                    account.permissions = permissions_info['permissions_json']
                    has_changes = True
                if account.is_superuser != permissions_info['is_superuser']:
                    account.is_superuser = permissions_info['is_superuser']
                    has_changes = True
                if account.can_grant != permissions_info['can_grant']:
                    account.can_grant = permissions_info['can_grant']
                    has_changes = True
                
                if has_changes:
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
                expiry_date,
                profile
            FROM dba_users
            WHERE username NOT IN ('OUTLN', 'DIP', 'TSMSYS', 'DBSNMP', 'WMSYS', 'EXFSYS', 'CTXSYS', 'XDB', 'ANONYMOUS', 'ORDPLUGINS', 'ORDSYS', 'SI_INFORMTN_SCHEMA', 'MDSYS', 'OLAPSYS', 'MDDATA', 'SPATIAL_CSW_ADMIN_USR', 'SPATIAL_WFS_ADMIN_USR', 'APEX_PUBLIC_USER', 'APEX_030200', 'FLOWS_FILES', 'HR', 'OE', 'PM', 'IX', 'SH', 'BI', 'SCOTT', 'DEMO', 'ADMIN', 'APPQOSSYS', 'AUDSYS', 'GSMADMIN_INTERNAL', 'GSMCATUSER', 'GSMUSER', 'LBACSYS', 'OJVMSYS', 'ORACLE_OCM', 'ORDDATA', 'ORDPLUGINS', 'ORDS_METADATA', 'ORDS_PUBLIC_USER', 'ORDSYS', 'PDBADMIN', 'RDSADMIN', 'REMOTE_SCHEDULER_AGENT', 'SYSBACKUP', 'SYSDG', 'SYSKM', 'SYSRAC', 'SYS$UMF', 'XDB', 'XS$NULL')
            ORDER BY username
        """)
        
        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        modified_count = 0
        removed_count = 0
        
        # 记录服务器端的账户
        server_accounts = set()
        
        for account_data in accounts:
            username, account_type, database_name, account_status, created, expiry_date, profile = account_data
            
            # 记录服务器端的账户
            server_accounts.add(username)
            
            # 获取权限信息
            permissions_info = self._get_oracle_account_permissions(conn, username)
            
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
                    is_active=account_status == 'OPEN',
                    permissions=permissions_info['permissions_json'],
                    is_superuser=permissions_info['is_superuser'],
                    can_grant=permissions_info['can_grant']
                )
                db.session.add(account)
                added_count += 1
            else:
                # 检查是否有变化
                is_active = account_status == 'OPEN'
                has_changes = False
                
                if account.database_name != database_name:
                    account.database_name = database_name
                    has_changes = True
                if account.account_type != account_type:
                    account.account_type = account_type
                    has_changes = True
                if account.is_active != is_active:
                    account.is_active = is_active
                    has_changes = True
                
                # 更新权限信息
                if account.permissions != permissions_info['permissions_json']:
                    account.permissions = permissions_info['permissions_json']
                    has_changes = True
                if account.is_superuser != permissions_info['is_superuser']:
                    account.is_superuser = permissions_info['is_superuser']
                    has_changes = True
                if account.can_grant != permissions_info['can_grant']:
                    account.can_grant = permissions_info['can_grant']
                    has_changes = True
                
                if has_changes:
                    account.updated_at = now()
                    modified_count += 1
            
            synced_count += 1
        
        # 删除服务器端不存在的本地账户
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
    
    def cleanup_orphaned_accounts(self, instance: Instance) -> Dict[str, Any]:
        """
        清理多余账户（服务器上不存在的本地账户）
        
        Args:
            instance: 数据库实例
            
        Returns:
            Dict: 清理结果
        """
        try:
            # 获取数据库连接
            conn = self._get_connection(instance)
            if not conn:
                return {
                    'success': False,
                    'error': '无法获取数据库连接'
                }
            
            removed_count = 0
            removed_accounts = []
            
            # 根据数据库类型执行清理
            if instance.db_type == 'mysql':
                result = self._cleanup_mysql_orphaned_accounts(instance, conn)
            elif instance.db_type == 'postgresql':
                result = self._cleanup_postgresql_orphaned_accounts(instance, conn)
            elif instance.db_type == 'sqlserver':
                result = self._cleanup_sqlserver_orphaned_accounts(instance, conn)
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {instance.db_type}'
                }
            
            removed_count = result['removed_count']
            removed_accounts = result['removed_accounts']
            
            return {
                'success': True,
                'message': f'清理完成，删除了 {removed_count} 个多余账户',
                'removed_count': removed_count,
                'removed_accounts': removed_accounts
            }
            
        except Exception as e:
            self.logger.error(f"清理多余账户失败: {str(e)}")
            return {
                'success': False,
                'error': f'清理多余账户失败: {str(e)}'
            }
    
    def _cleanup_mysql_orphaned_accounts(self, instance: Instance, conn) -> Dict[str, Any]:
        """清理MySQL多余账户"""
        cursor = conn.cursor()
        
        # 获取服务器端所有账户
        cursor.execute("""
            SELECT User, Host
            FROM mysql.user
            WHERE User NOT LIKE 'mysql.%'
            ORDER BY User, Host
        """)
        
        server_accounts = set()
        for row in cursor.fetchall():
            server_accounts.add((row[0], row[1]))
        
        # 获取本地账户并清理
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []
        removed_count = 0
        
        for local_account in local_accounts:
            if (local_account.username, local_account.host) not in server_accounts:
                removed_accounts.append({
                    'username': local_account.username,
                    'host': local_account.host,
                    'database_name': local_account.database_name,
                    'account_type': local_account.account_type
                })
                db.session.delete(local_account)
                removed_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'removed_count': removed_count,
            'removed_accounts': removed_accounts
        }
    
    def _cleanup_postgresql_orphaned_accounts(self, instance: Instance, conn) -> Dict[str, Any]:
        """清理PostgreSQL多余账户"""
        cursor = conn.cursor()
        
        # 获取服务器端所有账户
        cursor.execute("""
            SELECT usename
            FROM pg_user
            ORDER BY usename
        """)
        
        server_accounts = set()
        for row in cursor.fetchall():
            server_accounts.add(row[0])
        
        # 获取本地账户并清理
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []
        removed_count = 0
        
        for local_account in local_accounts:
            if local_account.username not in server_accounts:
                removed_accounts.append({
                    'username': local_account.username,
                    'host': '',
                    'database_name': local_account.database_name,
                    'account_type': local_account.account_type
                })
                db.session.delete(local_account)
                removed_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'removed_count': removed_count,
            'removed_accounts': removed_accounts
        }
    
    def _cleanup_sqlserver_orphaned_accounts(self, instance: Instance, conn) -> Dict[str, Any]:
        """清理SQL Server多余账户"""
        cursor = conn.cursor()
        
        # 获取服务器端所有账户
        cursor.execute("""
            SELECT name
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G')
            AND name NOT LIKE '##%'
            ORDER BY name
        """)
        
        server_accounts = set()
        for row in cursor.fetchall():
            server_accounts.add(row[0])
        
        # 获取本地账户并清理
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []
        removed_count = 0
        
        for local_account in local_accounts:
            if local_account.username not in server_accounts:
                removed_accounts.append({
                    'username': local_account.username,
                    'host': '',
                    'database_name': local_account.database_name,
                    'account_type': local_account.account_type
                })
                db.session.delete(local_account)
                removed_count += 1
        
        db.session.commit()
        cursor.close()
        
        return {
            'removed_count': removed_count,
            'removed_accounts': removed_accounts
        }
    
    def _get_mysql_account_permissions(self, conn, username: str, host: str) -> Dict[str, Any]:
        """获取MySQL账户权限信息"""
        import json
        
        cursor = conn.cursor()
        
        try:
            # 获取全局权限
            cursor.execute("""
                SELECT PRIVILEGE_TYPE, IS_GRANTABLE
                FROM INFORMATION_SCHEMA.USER_PRIVILEGES
                WHERE GRANTEE = %s
            """, (f"'{username}'@'{host}'",))
            
            global_permissions = []
            can_grant = False
            is_superuser = False
            
            for row in cursor.fetchall():
                privilege, is_grantable = row
                global_permissions.append({
                    'privilege': privilege,
                    'granted': True,
                    'grantable': bool(is_grantable)
                })
                if is_grantable:
                    can_grant = True
                if privilege == 'SUPER':
                    is_superuser = True
            
            # 检查用户是否真正拥有GRANT OPTION权限
            cursor.execute('''
                SELECT Grant_priv FROM mysql.user 
                WHERE User = %s AND Host = %s
            ''', (username, host))
            
            grant_result = cursor.fetchone()
            if grant_result and grant_result[0] == 'Y':
                # 用户真正拥有GRANT OPTION权限
                global_permissions.append({
                    'privilege': 'GRANT OPTION',
                    'granted': True,
                    'grantable': False
                })
            
            # 获取数据库权限
            cursor.execute("""
                SELECT TABLE_SCHEMA, PRIVILEGE_TYPE
                FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES
                WHERE GRANTEE = %s
                ORDER BY TABLE_SCHEMA, PRIVILEGE_TYPE
            """, (f"'{username}'@'{host}'",))
            
            db_permissions = {}
            for row in cursor.fetchall():
                schema, privilege = row
                if schema not in db_permissions:
                    db_permissions[schema] = []
                db_permissions[schema].append(privilege)
            
            # 转换为前端需要的格式
            database_permissions = []
            for schema, privileges in db_permissions.items():
                database_permissions.append({
                    'database': schema,
                    'privileges': privileges
                })
            
            permissions_data = {
                'global': global_permissions,
                'database': database_permissions
            }
            
            return {
                'permissions_json': json.dumps(permissions_data),
                'is_superuser': is_superuser,
                'can_grant': can_grant
            }
            
        except Exception as e:
            self.logger.error(f"获取MySQL权限失败: {e}")
            return {
                'permissions_json': json.dumps({'global': [], 'database': []}),
                'is_superuser': False,
                'can_grant': False
            }
        finally:
            cursor.close()
    
    def _get_sqlserver_account_permissions(self, conn, username: str) -> Dict[str, Any]:
        """获取SQL Server账户权限信息"""
        import json
        
        cursor = conn.cursor()
        
        try:
            # 获取服务器角色
            cursor.execute("""
                SELECT r.name as role_name
                FROM sys.server_role_members rm
                JOIN sys.server_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.server_principals p ON rm.member_principal_id = p.principal_id
                WHERE p.name = %s
            """, (username,))
            
            server_roles = []
            is_sysadmin = False
            for row in cursor.fetchall():
                role_name = row[0]
                server_roles.append({
                    'role': role_name,
                    'granted': True
                })
                if role_name == 'sysadmin':
                    is_sysadmin = True
            
            # 获取服务器权限
            cursor.execute("""
                SELECT p.permission_name, p.state_desc
                FROM sys.server_permissions p
                JOIN sys.server_principals sp ON p.grantee_principal_id = sp.principal_id
                WHERE sp.name = %s
            """, (username,))
            
            server_permissions = []
            for row in cursor.fetchall():
                permission, state = row
                server_permissions.append({
                    'permission': permission,
                    'granted': state == 'GRANT'
                })
            
            # 简化数据库权限获取 - 只获取基本权限
            database_roles = []
            database_permissions = []
            
            # 尝试获取数据库角色（简化版本）
            try:
                cursor.execute("""
                    SELECT 
                        db.name as database_name,
                        r.name as role_name
                    FROM sys.databases db
                    CROSS APPLY (
                        SELECT r.name as role_name
                        FROM sys.database_role_members rm
                        JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
                        JOIN sys.database_principals p ON rm.member_principal_id = p.principal_id
                        WHERE p.name = %s
                    ) roles
                    WHERE roles.role_name IS NOT NULL
                """, (username,))
                
                db_roles = {}
                for row in cursor.fetchall():
                    db_name, role_name = row
                    if db_name not in db_roles:
                        db_roles[db_name] = []
                    db_roles[db_name].append(role_name)
                
                for db_name, roles in db_roles.items():
                    database_roles.append({
                        'database': db_name,
                        'roles': roles
                    })
            except Exception as e:
                self.logger.debug(f"获取数据库角色失败: {e}")
            
            permissions_data = {
                'server_roles': server_roles,
                'server_permissions': server_permissions,
                'database_roles': database_roles,
                'database': database_permissions
            }
            
            return {
                'permissions_json': json.dumps(permissions_data),
                'is_superuser': is_sysadmin,
                'can_grant': is_sysadmin  # sysadmin角色可以授权
            }
            
        except Exception as e:
            self.logger.error(f"获取SQL Server权限失败: {e}")
            return {
                'permissions_json': json.dumps({'server_roles': [], 'server_permissions': [], 'database_roles': [], 'database': []}),
                'is_superuser': False,
                'can_grant': False
            }
        finally:
            cursor.close()
    
    def _get_oracle_account_permissions(self, conn, username: str) -> Dict[str, Any]:
        """获取Oracle账户权限信息 - 根据新的权限配置结构"""
        import json
        
        cursor = conn.cursor()
        permissions = {
            'roles': [],
            'system_privileges': [],
            'tablespace_privileges': [],
            'tablespace_quotas': []
        }
        
        try:
            # 获取角色权限
            cursor.execute("""
                SELECT granted_role, admin_option
                FROM dba_role_privs
                WHERE grantee = :username
                ORDER BY granted_role
            """, {'username': username.upper()})
            
            for row in cursor.fetchall():
                role, admin_option = row
                permissions['roles'].append(role)
            
            # 获取系统权限
            cursor.execute("""
                SELECT privilege, admin_option
                FROM dba_sys_privs
                WHERE grantee = :username
                ORDER BY privilege
            """, {'username': username.upper()})
            
            for row in cursor.fetchall():
                privilege, admin_option = row
                permissions['system_privileges'].append(privilege)
            
            # 获取表空间权限
            cursor.execute("""
                SELECT privilege
                FROM dba_tab_privs
                WHERE grantee = :username
                AND table_name IN (SELECT tablespace_name FROM dba_tablespaces)
                ORDER BY privilege
            """, {'username': username.upper()})
            
            for row in cursor.fetchall():
                privilege = row[0]
                permissions['tablespace_privileges'].append(privilege)
            
            # 获取表空间配额
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN max_bytes = -1 THEN 'UNLIMITED'
                        WHEN max_bytes = 0 THEN 'NO QUOTA'
                        ELSE 'QUOTA'
                    END as quota_type
                FROM dba_ts_quotas
                WHERE username = :username
                ORDER BY tablespace_name
            """, {'username': username.upper()})
            
            for row in cursor.fetchall():
                quota_type = row[0]
                permissions['tablespace_quotas'].append(quota_type)
            
            # 确定是否为超级用户和是否可以授权
            is_superuser = any(role in ['DBA', 'SYSDBA', 'SYSOPER'] for role in permissions['roles'])
            can_grant = is_superuser or any(priv in ['GRANT ANY PRIVILEGE', 'GRANT ANY ROLE'] for priv in permissions['system_privileges'])
            
            permissions['is_superuser'] = is_superuser
            permissions['can_grant'] = can_grant
            
            return {
                'permissions_json': json.dumps(permissions),
                'is_superuser': is_superuser,
                'can_grant': can_grant
            }
            
        except Exception as e:
            self.logger.error(f"获取Oracle权限失败: {e}")
            return {
                'permissions_json': json.dumps({'roles': [], 'system_privileges': [], 'tablespace_privileges': [], 'tablespace_quotas': []}),
                'is_superuser': False,
                'can_grant': False
            }
        finally:
            cursor.close()

# 全局实例
account_sync_service = AccountSyncService()
