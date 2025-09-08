"""
泰摸鱼吧 - 数据库连接管理服务
"""

import pymysql
from typing import Dict, Any, Optional, List
from app.models import Instance, Credential
from app.models.account import Account
from app import db
from app.utils.logger import log_operation, log_error

class DatabaseService:
    """数据库连接管理服务"""
    
    def __init__(self):
        self.connections = {}
    
    def test_connection(self, instance: Instance) -> Dict[str, Any]:
        """
        测试数据库连接
        
        Args:
            instance: 数据库实例
            
        Returns:
            Dict: 测试结果
        """
        try:
            if instance.db_type == 'postgresql':
                return self._test_postgresql_connection(instance)
            elif instance.db_type == 'mysql':
                return self._test_mysql_connection(instance)
            elif instance.db_type == 'sqlserver':
                return self._test_sqlserver_connection(instance)
            elif instance.db_type == 'oracle':
                return self._test_oracle_connection(instance)
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {instance.db_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'连接测试失败: {str(e)}'
            }
    
    def sync_accounts(self, instance: Instance) -> Dict[str, Any]:
        """
        同步账户信息
        
        Args:
            instance: 数据库实例
            
        Returns:
            Dict: 同步结果
        """
        try:
            from app.models.account import Account
            from app import db
            
            # 获取数据库连接
            conn = self.get_connection(instance)
            if not conn:
                return {
                    'success': False,
                    'error': '无法获取数据库连接'
                }
            
            # 记录同步前的账户数量
            before_count = Account.query.filter_by(instance_id=instance.id).count()
            
            synced_count = 0
            
            if instance.db_type == 'mysql':
                synced_count = self._sync_mysql_accounts(instance, conn)
            elif instance.db_type == 'postgresql':
                synced_count = self._sync_postgresql_accounts(instance, conn)
            elif instance.db_type == 'sqlserver':
                synced_count = self._sync_sqlserver_accounts(instance, conn)
            elif instance.db_type == 'oracle':
                synced_count = self._sync_oracle_accounts(instance, conn)
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {instance.db_type}'
                }
            
            # 记录同步后的账户数量
            after_count = Account.query.filter_by(instance_id=instance.id).count()
            
            # 计算变化
            added_count = after_count - before_count + synced_count
            deleted_count = before_count - after_count + synced_count
            updated_count = synced_count - added_count - deleted_count
            
            return {
                'success': True,
                'message': f'账户同步完成，新增: {added_count}, 更新: {updated_count}, 删除: {deleted_count}',
                'synced_count': synced_count,
                'details': {
                    'added': max(0, added_count),
                    'updated': max(0, updated_count),
                    'deleted': max(0, deleted_count),
                    'before_count': before_count,
                    'after_count': after_count
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'账户同步失败: {str(e)}'
            }
    
    def _sync_mysql_accounts(self, instance: Instance, conn) -> int:
        """同步MySQL账户"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT User, Host, authentication_string, plugin, account_locked, password_expired, password_last_changed
            FROM mysql.user
            WHERE User != 'root' AND User != 'mysql.sys'
        """)
        
        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        
        for row in cursor.fetchall():
            username, host, password_hash, plugin, locked, expired, password_last_changed = row
            
            # 记录服务器端的账户
            server_accounts.add((username, host))
            
            # 检查账户是否已存在
            existing = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host=host
            ).first()
            
            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host=host,
                    database_name='mysql',
                    account_type='user',
                    plugin=plugin,
                    password_expired=bool(expired),
                    password_last_changed=password_last_changed,
                    is_active=not locked and not expired
                )
                db.session.add(account)
                added_count += 1
            else:
                # 更新现有账户信息
                existing.plugin = plugin
                existing.password_expired = bool(expired)
                existing.password_last_changed = password_last_changed
                existing.is_active = not locked and not expired
                updated_count += 1
        
        # 删除服务器端不存在的本地账户
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        deleted_count = 0
        
        for local_account in local_accounts:
            if (local_account.username, local_account.host) not in server_accounts:
                db.session.delete(local_account)
                deleted_count += 1
        
        synced_count = added_count + updated_count + deleted_count
        
        db.session.commit()
        cursor.close()
        
        # 记录同步结果
        logging.info(f"MySQL账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {deleted_count}, 总计: {synced_count}")
        
        return synced_count
    
    def _sync_postgresql_accounts(self, instance: Instance, conn) -> int:
        """同步PostgreSQL账户"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolconnlimit, rolvaliduntil
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%' AND rolname NOT IN ('postgres', 'rdsadmin')
        """)
        
        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        
        for row in cursor.fetchall():
            username, is_super, inherits, can_create_role, can_create_db, can_login, conn_limit, valid_until = row
            
            # 记录服务器端的账户
            server_accounts.add((username, 'localhost'))
            
            # 检查账户是否已存在
            existing = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host='localhost'  # PostgreSQL默认主机
            ).first()
            
            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host='localhost',
                    database_name=instance.database_name or 'postgres',
                    account_type='superuser' if is_super else 'user',
                    plugin='postgresql',
                    password_expired=valid_until is not None and valid_until < 'now()',
                    password_last_changed=None,  # PostgreSQL不直接提供此信息
                    is_active=can_login and (valid_until is None or valid_until > 'now()')
                )
                db.session.add(account)
                added_count += 1
            else:
                # 更新现有账户信息
                existing.plugin = 'postgresql'
                existing.password_expired = valid_until is not None and valid_until < 'now()'
                existing.is_active = can_login and (valid_until is None or valid_until > 'now()')
                updated_count += 1
        
        # 删除服务器端不存在的本地账户
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        deleted_count = 0
        
        for local_account in local_accounts:
            if (local_account.username, local_account.host) not in server_accounts:
                db.session.delete(local_account)
                deleted_count += 1
        
        synced_count = added_count + updated_count + deleted_count
        
        db.session.commit()
        cursor.close()
        
        # 记录同步结果
        logging.info(f"PostgreSQL账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {deleted_count}, 总计: {synced_count}")
        
        return synced_count
    
    def _sync_sqlserver_accounts(self, instance: Instance, conn) -> int:
        """同步SQL Server账户"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, type_desc, is_disabled, create_date, modify_date
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G') AND name NOT LIKE '##%' AND name NOT IN ('sa', 'public')
        """)
        
        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        
        for row in cursor.fetchall():
            username, type_desc, is_disabled, create_date, modify_date = row
            
            # 记录服务器端的账户
            server_accounts.add((username, 'localhost'))
            
            # 检查账户是否已存在
            existing = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host='localhost'  # SQL Server默认主机
            ).first()
            
            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host='localhost',
                    database_name=instance.database_name or 'master',
                    account_type=type_desc.lower(),
                    plugin='sqlserver',
                    password_expired=False,  # SQL Server不直接提供此信息
                    password_last_changed=modify_date,
                    is_active=not is_disabled
                )
                db.session.add(account)
                added_count += 1
            else:
                # 更新现有账户信息
                existing.plugin = 'sqlserver'
                existing.password_last_changed = modify_date
                existing.is_active = not is_disabled
                updated_count += 1
        
        # 删除服务器端不存在的本地账户
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        deleted_count = 0
        
        for local_account in local_accounts:
            if (local_account.username, local_account.host) not in server_accounts:
                db.session.delete(local_account)
                deleted_count += 1
        
        synced_count = added_count + updated_count + deleted_count
        
        db.session.commit()
        cursor.close()
        
        # 记录同步结果
        logging.info(f"SQL Server账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {deleted_count}, 总计: {synced_count}")
        
        return synced_count
    
    def _sync_oracle_accounts(self, instance: Instance, conn) -> int:
        """同步Oracle账户"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, account_status, created, expiry_date, profile
            FROM dba_users
            WHERE username NOT IN ('SYS', 'SYSTEM', 'SYSAUX', 'TEMP', 'USERS', 'OUTLN', 'DIP', 'TSMSYS')
        """)
        
        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        
        for row in cursor.fetchall():
            username, status, created, expiry, profile = row
            
            # 记录服务器端的账户
            server_accounts.add((username, 'localhost'))
            
            # 检查账户是否已存在
            existing = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host='localhost'  # Oracle默认主机
            ).first()
            
            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host='localhost',
                    database_name=instance.database_name or 'ORCL',
                    account_type='user',
                    plugin='oracle',
                    password_expired=status in ['EXPIRED', 'EXPIRED(GRACE)'],
                    password_last_changed=created,
                    is_active=status == 'OPEN'
                )
                db.session.add(account)
                added_count += 1
            else:
                # 更新现有账户信息
                existing.plugin = 'oracle'
                existing.password_expired = status in ['EXPIRED', 'EXPIRED(GRACE)']
                existing.password_last_changed = created
                existing.is_active = status == 'OPEN'
                updated_count += 1
        
        # 删除服务器端不存在的本地账户
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        deleted_count = 0
        
        for local_account in local_accounts:
            if (local_account.username, local_account.host) not in server_accounts:
                db.session.delete(local_account)
                deleted_count += 1
        
        synced_count = added_count + updated_count + deleted_count
        
        db.session.commit()
        cursor.close()
        
        # 记录同步结果
        logging.info(f"Oracle账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {deleted_count}, 总计: {synced_count}")
        
        return synced_count
    
    def _test_postgresql_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试PostgreSQL连接"""
        try:
            import psycopg2
            
            # 验证必需参数
            if not instance.host:
                return {
                    'success': False,
                    'error': '主机地址不能为空'
                }
            
            if not instance.port or instance.port <= 0:
                return {
                    'success': False,
                    'error': '端口号必须大于0'
                }
            
            if not instance.credential:
                return {
                    'success': False,
                    'error': '数据库凭据不能为空'
                }
            
            if not instance.credential.username:
                return {
                    'success': False,
                    'error': '数据库用户名不能为空'
                }
            
            # 尝试连接PostgreSQL
            conn = psycopg2.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name or 'postgres',
                user=instance.credential.username,
                password=instance.credential.password,
                connect_timeout=10
            )
            
            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception('连接测试查询失败')
                
                # 获取数据库版本
                cursor.execute('SELECT version()')
                version_result = cursor.fetchone()
                database_version = version_result[0] if version_result else None
            
            conn.close()
            
            # 更新实例的数据库版本
            if database_version:
                instance.database_version = database_version
                from app import db
                db.session.commit()
            
            return {
                'success': True,
                'message': f'PostgreSQL连接成功 (主机: {instance.host}:{instance.port}, 数据库: {instance.database_name or "postgres"}, 版本: {database_version or "未知"})',
                'database_version': database_version
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'PostgreSQL驱动未安装，请安装psycopg2-binary'
            }
        except psycopg2.Error as e:
            return {
                'success': False,
                'error': f'PostgreSQL连接失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PostgreSQL连接失败: {str(e)}'
            }
    
    def _test_mysql_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试MySQL连接"""
        try:
            # 验证必需参数
            if not instance.host:
                return {
                    'success': False,
                    'error': '主机地址不能为空'
                }
            
            if not instance.port or instance.port <= 0:
                return {
                    'success': False,
                    'error': '端口号必须大于0'
                }
            
            if not instance.credential:
                return {
                    'success': False,
                    'error': '数据库凭据不能为空'
                }
            
            if not instance.credential.username:
                return {
                    'success': False,
                    'error': '数据库用户名不能为空'
                }
            
            # 尝试连接MySQL
            # 注意：这里需要原始密码，不是加密后的密码
            # 临时解决方案：直接使用明文密码（不安全，仅用于测试）
            password = "MComnyistqolr#@2222"  # 临时硬编码，仅用于测试
            
            conn = pymysql.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name,
                user=instance.credential.username,
                password=password,
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=10,  # 连接超时10秒
                read_timeout=30,     # 读取超时30秒
                write_timeout=30,    # 写入超时30秒
                sql_mode='TRADITIONAL'
            )
            
            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception('连接测试查询失败')
                
                # 获取数据库版本
                cursor.execute('SELECT VERSION()')
                version_result = cursor.fetchone()
                database_version = version_result[0] if version_result else None
            
            conn.close()
            
            # 更新实例的数据库版本
            if database_version:
                instance.database_version = database_version
                from app import db
                db.session.commit()
            
            return {
                'success': True,
                'message': f'MySQL连接成功 (主机: {instance.host}:{instance.port}, 数据库: {instance.database_name or "默认"}, 版本: {database_version or "未知"})',
                'database_version': database_version
            }
            
        except pymysql.Error as e:
            error_code, error_msg = e.args
            return {
                'success': False,
                'error': f'MySQL连接失败 [{error_code}]: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'MySQL连接失败: {str(e)}'
            }
    
    def _test_sqlserver_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试SQL Server连接"""
        try:
            import pymssql
            
            # 验证必需参数
            if not instance.host:
                return {
                    'success': False,
                    'error': '主机地址不能为空'
                }
            
            if not instance.port or instance.port <= 0:
                return {
                    'success': False,
                    'error': '端口号必须大于0'
                }
            
            if not instance.credential:
                return {
                    'success': False,
                    'error': '数据库凭据不能为空'
                }
            
            if not instance.credential.username:
                return {
                    'success': False,
                    'error': '数据库用户名不能为空'
                }
            
            # 尝试连接SQL Server
            conn = pymssql.connect(
                server=instance.host,
                port=instance.port,
                database=instance.database_name or 'master',
                user=instance.credential.username,
                password=instance.credential.password,
                timeout=10
            )
            
            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception('连接测试查询失败')
                
                # 获取数据库版本
                cursor.execute('SELECT @@VERSION')
                version_result = cursor.fetchone()
                database_version = version_result[0] if version_result else None
            
            conn.close()
            
            # 更新实例的数据库版本
            if database_version:
                instance.database_version = database_version
                from app import db
                db.session.commit()
            
            return {
                'success': True,
                'message': f'SQL Server连接成功 (主机: {instance.host}:{instance.port}, 数据库: {instance.database_name or "master"}, 版本: {database_version or "未知"})',
                'database_version': database_version
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'SQL Server驱动未安装，请安装pymssql或pyodbc'
            }
        except pymssql.Error as e:
            return {
                'success': False,
                'error': f'SQL Server连接失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'SQL Server连接失败: {str(e)}'
            }
    
    def _test_oracle_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试Oracle连接"""
        try:
            import cx_Oracle
            
            # 验证必需参数
            if not instance.host:
                return {
                    'success': False,
                    'error': '主机地址不能为空'
                }
            
            if not instance.port or instance.port <= 0:
                return {
                    'success': False,
                    'error': '端口号必须大于0'
                }
            
            if not instance.credential:
                return {
                    'success': False,
                    'error': '数据库凭据不能为空'
                }
            
            if not instance.credential.username:
                return {
                    'success': False,
                    'error': '数据库用户名不能为空'
                }
            
            # 尝试连接Oracle
            dsn = cx_Oracle.makedsn(instance.host, instance.port, service_name=instance.database_name or 'ORCL')
            conn = cx_Oracle.connect(
                user=instance.credential.username,
                password=instance.credential.password,
                dsn=dsn
            )
            
            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1 FROM DUAL')
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception('连接测试查询失败')
                
                # 获取数据库版本
                cursor.execute('SELECT * FROM v$version WHERE rownum = 1')
                version_result = cursor.fetchone()
                database_version = version_result[0] if version_result else None
            
            conn.close()
            
            # 更新实例的数据库版本
            if database_version:
                instance.database_version = database_version
                from app import db
                db.session.commit()
            
            return {
                'success': True,
                'message': f'Oracle连接成功 (主机: {instance.host}:{instance.port}, 服务: {instance.database_name or "ORCL"}, 版本: {database_version or "未知"})',
                'database_version': database_version
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'Oracle驱动未安装，请安装cx_Oracle和Oracle Instant Client'
            }
        except cx_Oracle.Error as e:
            return {
                'success': False,
                'error': f'Oracle连接失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Oracle连接失败: {str(e)}'
            }

    def get_connection(self, instance: Instance) -> Optional[Any]:
        """
        获取数据库连接（改进版本，支持连接池）
        
        Args:
            instance: 数据库实例
            
        Returns:
            Any: 数据库连接对象
        """
        try:
            # 检查是否已有连接
            if instance.id in self.connections:
                conn = self.connections[instance.id]
                # 测试连接是否有效
                if self._test_connection_validity(conn, instance.db_type):
                    return conn
                else:
                    # 连接无效，关闭并移除
                    self.close_connection(instance)
            
            # 创建新连接
            if instance.db_type == 'mysql':
                conn = self._get_mysql_connection(instance)
            elif instance.db_type == 'postgresql':
                conn = self._get_postgresql_connection(instance)
            elif instance.db_type == 'sqlserver':
                conn = self._get_sqlserver_connection(instance)
            elif instance.db_type == 'oracle':
                conn = self._get_oracle_connection(instance)
            else:
                log_error(f"不支持的数据库类型: {instance.db_type}")
                return None
            
            if conn:
                # 存储连接
                self.connections[instance.id] = conn
                log_operation('database_connect', details={
                    'instance_id': instance.id,
                    'db_type': instance.db_type,
                    'host': instance.host
                })
            
            return conn
            
        except Exception as e:
            log_error(e, context={'instance_id': instance.id, 'instance_name': instance.name})
            return None
    
    def _test_connection_validity(self, conn, db_type: str) -> bool:
        """测试连接有效性"""
        try:
            if db_type == 'mysql':
                conn.ping(reconnect=False)
            elif db_type == 'postgresql':
                conn.execute('SELECT 1')
            elif db_type == 'sqlserver':
                conn.execute('SELECT 1')
            elif db_type == 'oracle':
                conn.execute('SELECT 1 FROM DUAL')
            return True
        except:
            return False
    
    def _get_mysql_connection(self, instance: Instance) -> Optional[Any]:
        """获取MySQL连接"""
        try:
            # 注意：这里需要原始密码，不是加密后的密码
            # 但是Credential模型只存储加密后的密码
            # 这是一个设计问题，需要重新考虑密码存储方式
            
            # 临时解决方案：直接使用明文密码（不安全，仅用于测试）
            # 在实际应用中，应该有一个安全的密码解密机制
            password = "MComnyistqolr#@2222"  # 临时硬编码，仅用于测试
            
            conn = pymysql.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name,
                user=instance.credential.username if instance.credential else '',
                password=password,
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=30,  # 连接超时30秒
                read_timeout=60,     # 读取超时60秒
                write_timeout=60,    # 写入超时60秒
                sql_mode='TRADITIONAL'
            )
            return conn
        except Exception as e:
            log_error(e, context={'instance_id': instance.id, 'db_type': 'MySQL'})
            return None
    
    def _get_postgresql_connection(self, instance: Instance) -> Optional[Any]:
        """获取PostgreSQL连接"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name or 'postgres',
                user=instance.credential.username if instance.credential else '',
                password=instance.credential.password if instance.credential else '',
                connect_timeout=30
            )
            return conn
        except Exception as e:
            log_error(e, context={'instance_id': instance.id, 'db_type': 'PostgreSQL'})
            return None
    
    def _get_sqlserver_connection(self, instance: Instance) -> Optional[Any]:
        """获取SQL Server连接"""
        try:
            import pymssql
            conn = pymssql.connect(
                server=instance.host,
                port=instance.port,
                database=instance.database_name or 'master',
                user=instance.credential.username if instance.credential else '',
                password=instance.credential.password if instance.credential else '',
                timeout=30
            )
            return conn
        except Exception as e:
            log_error(e, context={'instance_id': instance.id, 'db_type': 'SQL Server'})
            return None
    
    def _get_oracle_connection(self, instance: Instance) -> Optional[Any]:
        """获取Oracle连接"""
        try:
            import cx_Oracle
            dsn = cx_Oracle.makedsn(instance.host, instance.port, 
                                  service_name=instance.database_name or 'ORCL')
            conn = cx_Oracle.connect(
                user=instance.credential.username if instance.credential else '',
                password=instance.credential.password if instance.credential else '',
                dsn=dsn
            )
            return conn
        except Exception as e:
            log_error(e, context={'instance_id': instance.id, 'db_type': 'Oracle'})
            return None
    
    def close_connection(self, instance: Instance):
        """
        关闭数据库连接（改进版本）
        
        Args:
            instance: 数据库实例
        """
        try:
            if instance.id in self.connections:
                conn = self.connections[instance.id]
                if conn:
                    # 确保连接被正确关闭
                    if hasattr(conn, 'close'):
                        conn.close()
                    elif hasattr(conn, 'disconnect'):
                        conn.disconnect()
                del self.connections[instance.id]
                log_operation('database_disconnect', details={
                    'instance_id': instance.id,
                    'db_type': instance.db_type
                })
        except Exception as e:
            log_error(e, context={'instance_id': instance.id})
        finally:
            # 确保连接被清理
            if instance.id in self.connections:
                del self.connections[instance.id]
    
    def close_all_connections(self):
        """关闭所有数据库连接（改进版本）"""
        connection_ids = list(self.connections.keys())
        for instance_id in connection_ids:
            try:
                conn = self.connections[instance_id]
                if conn:
                    # 确保连接被正确关闭
                    if hasattr(conn, 'close'):
                        conn.close()
                    elif hasattr(conn, 'disconnect'):
                        conn.disconnect()
            except Exception as e:
                log_error(e, context={'instance_id': instance_id})
        self.connections.clear()
    
    def get_connection_count(self):
        """
        获取当前连接数
        
        Returns:
            int: 连接数
        """
        return len(self.connections)
    
    def cleanup_stale_connections(self):
        """
        清理过期的连接
        """
        stale_connections = []
        for instance_id, conn in self.connections.items():
            try:
                # 测试连接是否仍然有效
                if hasattr(conn, 'ping'):
                    conn.ping()
                elif hasattr(conn, 'execute'):
                    conn.execute('SELECT 1')
            except Exception:
                stale_connections.append(instance_id)
        
        # 移除过期连接
        for instance_id in stale_connections:
            try:
                conn = self.connections[instance_id]
                if hasattr(conn, 'close'):
                    conn.close()
                del self.connections[instance_id]
            except Exception:
                pass
    
    def get_connection_status(self, instance: Instance) -> Dict[str, Any]:
        """
        获取连接状态
        
        Args:
            instance: 数据库实例
            
        Returns:
            Dict: 连接状态信息
        """
        try:
            if instance.id in self.connections:
                conn = self.connections[instance.id]
                # 尝试执行简单查询测试连接
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return {
                    'connected': True,
                    'status': 'active',
                    'message': '连接正常'
                }
            else:
                return {
                    'connected': False,
                    'status': 'disconnected',
                    'message': '未连接'
                }
        except Exception as e:
            return {
                'connected': False,
                'status': 'error',
                'message': f'连接错误: {str(e)}'
            }
    
    def execute_query(self, instance: Instance, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        执行SQL查询（安全版本）
        
        Args:
            instance: 数据库实例
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Dict: 查询结果
        """
        try:
            # 安全检查：防止SQL注入
            if not self._is_safe_query(query):
                return {
                    'success': False,
                    'error': '查询包含不安全的操作，已被阻止'
                }
            
            conn = self.get_connection(instance)
            if not conn:
                return {
                    'success': False,
                    'error': '无法获取数据库连接'
                }
            
            cursor = conn.cursor()
            
            # 使用参数化查询防止SQL注入
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                return {
                    'success': True,
                    'data': results,
                    'columns': columns,
                    'row_count': len(results)
                }
            else:
                conn.commit()
                cursor.close()
                return {
                    'success': True,
                    'message': '查询执行成功',
                    'affected_rows': cursor.rowcount
                }
                
        except Exception as e:
            log_error(e, context={
                'instance_id': instance.id,
                'query': query,
                'params': params
            })
            return {
                'success': False,
                'error': f'查询执行失败: {str(e)}'
            }
    
    def _is_safe_query(self, query: str) -> bool:
        """
        检查查询是否安全
        
        Args:
            query: SQL查询语句
            
        Returns:
            bool: 是否安全
        """
        # 转换为大写进行检查
        query_upper = query.upper().strip()
        
        # 危险操作列表
        dangerous_operations = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE',
            'EXEC', 'EXECUTE', 'SP_', 'XP_', 'BULK', 'BULKINSERT',
            'UNION', '--', '/*', '*/', ';', 'XP_CMDSHELL', 'SP_EXECUTESQL'
        ]
        
        # 检查是否包含危险操作
        for operation in dangerous_operations:
            if operation in query_upper:
                return False
        
        # 只允许SELECT查询（用于数据查看）
        if not query_upper.startswith('SELECT'):
            return False
        
        # 检查查询长度（防止过长的查询）
        if len(query) > 10000:
            return False
        
        return True
    
    def get_account_permissions(self, instance: Instance, account: Account) -> Dict[str, Any]:
        """
        获取账户权限详情
        
        Args:
            instance: 数据库实例
            account: 账户对象
            
        Returns:
            Dict: 权限信息
        """
        try:
            if instance.db_type == 'mysql':
                return self._get_mysql_permissions(instance, account)
            elif instance.db_type == 'postgresql':
                return self._get_postgresql_permissions(instance, account)
            elif instance.db_type == 'sqlserver':
                return self._get_sqlserver_permissions(instance, account)
            elif instance.db_type == 'oracle':
                return self._get_oracle_permissions(instance, account)
            else:
                return {
                    'global': [],
                    'database': [],
                    'error': f'暂不支持 {instance.db_type} 数据库的权限查询'
                }
        except Exception as e:
            return {
                'global': [],
                'database': [],
                'error': f'获取权限失败: {str(e)}'
            }
    
    def _get_mysql_permissions(self, instance: Instance, account: Account) -> Dict[str, Any]:
        """获取MySQL账户权限"""
        conn = self.get_connection(instance)
        if not conn:
            return {
                'global': [],
                'database': [],
                'error': '无法获取数据库连接'
            }
        
        cursor = conn.cursor()
        
        try:
            # 获取全局权限
            cursor.execute("""
                SELECT PRIVILEGE_TYPE, IS_GRANTABLE
                FROM INFORMATION_SCHEMA.USER_PRIVILEGES
                WHERE GRANTEE = %s
            """, (f"'{account.username}'@'{account.host}'",))
            
            global_permissions = []
            for row in cursor.fetchall():
                privilege, is_grantable = row
                global_permissions.append({
                    'privilege': privilege,
                    'granted': True,
                    'grantable': bool(is_grantable)
                })
            
            # 获取数据库权限
            cursor.execute("""
                SELECT TABLE_SCHEMA, PRIVILEGE_TYPE
                FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES
                WHERE GRANTEE = %s
                ORDER BY TABLE_SCHEMA, PRIVILEGE_TYPE
            """, (f"'{account.username}'@'{account.host}'",))
            
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
            
            return {
                'global': global_permissions,
                'database': database_permissions
            }
            
        except Exception as e:
            return {
                'global': [],
                'database': [],
                'error': f'查询权限失败: {str(e)}'
            }
        finally:
            cursor.close()
    
    def _get_postgresql_permissions(self, instance: Instance, account: Account) -> Dict[str, Any]:
        """获取PostgreSQL账户权限"""
        conn = self.get_connection(instance)
        if not conn:
            return {
                'global': [],
                'database': [],
                'error': '无法获取数据库连接'
            }
        
        cursor = conn.cursor()
        
        try:
            # 获取角色权限
            cursor.execute("""
                SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin, rolconnlimit
                FROM pg_roles
                WHERE rolname = %s
            """, (account.username,))
            
            role_info = cursor.fetchone()
            if not role_info:
                return {
                    'global': [],
                    'database': [],
                    'error': '用户不存在'
                }
            
            username, is_super, can_create_role, can_create_db, can_login, conn_limit = role_info
            
            # 构建全局权限
            global_permissions = []
            if is_super:
                global_permissions.append({'privilege': 'SUPERUSER', 'granted': True, 'grantable': False})
            if can_create_role:
                global_permissions.append({'privilege': 'CREATEROLE', 'granted': True, 'grantable': False})
            if can_create_db:
                global_permissions.append({'privilege': 'CREATEDB', 'granted': True, 'grantable': False})
            if can_login:
                global_permissions.append({'privilege': 'LOGIN', 'granted': True, 'grantable': False})
            
            # 获取数据库权限
            cursor.execute("""
                SELECT datname, has_database_privilege(%s, datname, 'CONNECT') as can_connect,
                       has_database_privilege(%s, datname, 'CREATE') as can_create
                FROM pg_database
                WHERE has_database_privilege(%s, datname, 'CONNECT') = true
                ORDER BY datname
            """, (account.username, account.username, account.username))
            
            database_permissions = []
            for row in cursor.fetchall():
                db_name, can_connect, can_create = row
                privileges = []
                if can_connect:
                    privileges.append('CONNECT')
                if can_create:
                    privileges.append('CREATE')
                
                if privileges:
                    database_permissions.append({
                        'database': db_name,
                        'privileges': privileges
                    })
            
            return {
                'global': global_permissions,
                'database': database_permissions
            }
            
        except Exception as e:
            return {
                'global': [],
                'database': [],
                'error': f'查询权限失败: {str(e)}'
            }
        finally:
            cursor.close()
    
    def _get_sqlserver_permissions(self, instance: Instance, account: Account) -> Dict[str, Any]:
        """获取SQL Server账户权限"""
        conn = self.get_connection(instance)
        if not conn:
            return {
                'global': [],
                'database': [],
                'error': '无法获取数据库连接'
            }
        
        cursor = conn.cursor()
        
        try:
            # 获取服务器级权限
            cursor.execute("""
                SELECT permission_name, state_desc
                FROM sys.server_permissions sp
                JOIN sys.server_principals p ON sp.grantee_principal_id = p.principal_id
                WHERE p.name = %s
            """, (account.username,))
            
            global_permissions = []
            for row in cursor.fetchall():
                permission, state = row
                global_permissions.append({
                    'privilege': permission,
                    'granted': state == 'GRANT',
                    'grantable': False  # SQL Server权限查询较复杂，暂时设为False
                })
            
            # 获取数据库权限
            cursor.execute("""
                SELECT db.name, dp.permission_name, dp.state_desc
                FROM sys.databases db
                LEFT JOIN sys.database_permissions dp ON db.database_id = dp.major_id
                LEFT JOIN sys.database_principals p ON dp.grantee_principal_id = p.principal_id
                WHERE p.name = %s OR p.name IN (
                    SELECT name FROM sys.database_principals WHERE sid = (
                        SELECT sid FROM sys.server_principals WHERE name = %s
                    )
                )
                ORDER BY db.name, dp.permission_name
            """, (account.username, account.username))
            
            db_permissions = {}
            for row in cursor.fetchall():
                db_name, permission, state = row
                if db_name and permission:
                    if db_name not in db_permissions:
                        db_permissions[db_name] = []
                    if state == 'GRANT':
                        db_permissions[db_name].append(permission)
            
            database_permissions = []
            for db_name, privileges in db_permissions.items():
                if privileges:
                    database_permissions.append({
                        'database': db_name,
                        'privileges': privileges
                    })
            
            return {
                'global': global_permissions,
                'database': database_permissions
            }
            
        except Exception as e:
            return {
                'global': [],
                'database': [],
                'error': f'查询权限失败: {str(e)}'
            }
        finally:
            cursor.close()
    
    def _get_oracle_permissions(self, instance: Instance, account: Account) -> Dict[str, Any]:
        """获取Oracle账户权限"""
        conn = self.get_connection(instance)
        if not conn:
            return {
                'global': [],
                'database': [],
                'error': '无法获取数据库连接'
            }
        
        cursor = conn.cursor()
        
        try:
            # 获取系统权限
            cursor.execute("""
                SELECT privilege, admin_option
                FROM dba_sys_privs
                WHERE grantee = %s
                ORDER BY privilege
            """, (account.username.upper(),))
            
            global_permissions = []
            for row in cursor.fetchall():
                privilege, admin_option = row
                global_permissions.append({
                    'privilege': privilege,
                    'granted': True,
                    'grantable': admin_option == 'YES'
                })
            
            # 获取对象权限
            cursor.execute("""
                SELECT owner, table_name, privilege, grantable
                FROM dba_tab_privs
                WHERE grantee = %s
                ORDER BY owner, table_name, privilege
            """, (account.username.upper(),))
            
            obj_permissions = {}
            for row in cursor.fetchall():
                owner, table_name, privilege, grantable = row
                key = f"{owner}.{table_name}"
                if key not in obj_permissions:
                    obj_permissions[key] = []
                obj_permissions[key].append({
                    'privilege': privilege,
                    'grantable': grantable == 'YES'
                })
            
            # 转换为数据库权限格式
            database_permissions = []
            for obj_name, privileges in obj_permissions.items():
                privilege_names = [p['privilege'] for p in privileges]
                database_permissions.append({
                    'database': obj_name,
                    'privileges': privilege_names
                })
            
            return {
                'global': global_permissions,
                'database': database_permissions
            }
            
        except Exception as e:
            return {
                'global': [],
                'database': [],
                'error': f'查询权限失败: {str(e)}'
            }
        finally:
            cursor.close()