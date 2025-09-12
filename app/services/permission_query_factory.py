#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限查询工厂
提供统一的数据库权限查询功能
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from app.models.instance import Instance
from app.models.account import Account
from app.services.connection_factory import ConnectionFactory
from app.utils.enhanced_logger import log_error, log_operation


class PermissionQuery(ABC):
    """权限查询抽象基类"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
        self.connection = None
    
    @abstractmethod
    def get_account_permissions(self, account: Account) -> Dict[str, Any]:
        """获取账户权限"""
        pass
    
    @abstractmethod
    def get_global_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取全局权限"""
        pass
    
    @abstractmethod
    def get_database_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取数据库权限"""
        pass
    
    @abstractmethod
    def get_table_permissions(self, account: Account, database: str) -> List[Dict[str, Any]]:
        """获取表权限"""
        pass
    
    def _get_connection(self):
        """获取数据库连接"""
        if not self.connection:
            self.connection = ConnectionFactory.create_connection(self.instance)
        return self.connection


class MySQLPermissionQuery(PermissionQuery):
    """MySQL权限查询"""
    
    def get_account_permissions(self, account: Account) -> Dict[str, Any]:
        """获取MySQL账户权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return {"success": False, "error": "无法建立数据库连接"}
            
            global_perms = self.get_global_permissions(account)
            database_perms = self.get_database_permissions(account)
            
            return {
                "success": True,
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "host": account.host,
                    "plugin": account.plugin
                },
                "permissions": {
                    "global": global_perms,
                    "database": database_perms
                }
            }
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return {"success": False, "error": str(e)}
        finally:
            if connection:
                connection.disconnect()
    
    def get_global_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取MySQL全局权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询全局权限
            query = """
                SELECT 
                    PRIVILEGE_TYPE as privilege,
                    IS_GRANTABLE = 'YES' as grantable
                FROM information_schema.USER_PRIVILEGES 
                WHERE GRANTEE = %s
                ORDER BY PRIVILEGE_TYPE
            """
            
            # 处理host字段为空的情况
            host = account.host if account.host and account.host.strip() else ''
            grantee = f"'{account.username}'@'{host}'"
            results = connection.execute_query(query, (grantee,))
            
            return [
                {
                    "privilege": row[0],
                    "granted": True,
                    "grantable": row[1]
                }
                for row in results
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def get_database_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取MySQL数据库权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询数据库权限
            query = """
                SELECT 
                    TABLE_SCHEMA as database_name,
                    GROUP_CONCAT(PRIVILEGE_TYPE) as privileges
                FROM information_schema.SCHEMA_PRIVILEGES 
                WHERE GRANTEE = %s
                GROUP BY TABLE_SCHEMA
                ORDER BY TABLE_SCHEMA
            """
            
            # 处理host字段为空的情况
            host = account.host if account.host and account.host.strip() else ''
            grantee = f"'{account.username}'@'{host}'"
            results = connection.execute_query(query, (grantee,))
            
            return [
                {
                    "database": row[0],
                    "privileges": row[1].split(',') if row[1] else []
                }
                for row in results
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def get_table_permissions(self, account: Account, database: str) -> List[Dict[str, Any]]:
        """获取MySQL表权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询表权限
            query = """
                SELECT 
                    TABLE_NAME as table_name,
                    GROUP_CONCAT(PRIVILEGE_TYPE) as privileges
                FROM information_schema.TABLE_PRIVILEGES 
                WHERE GRANTEE = %s AND TABLE_SCHEMA = %s
                GROUP BY TABLE_NAME
                ORDER BY TABLE_NAME
            """
            
            # 处理host字段为空的情况
            host = account.host if account.host and account.host.strip() else ''
            grantee = f"'{account.username}'@'{host}'"
            results = connection.execute_query(query, (grantee, database))
            
            return [
                {
                    "table": row[0],
                    "privileges": row[1].split(',') if row[1] else []
                }
                for row in results
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()


class PostgreSQLPermissionQuery(PermissionQuery):
    """PostgreSQL权限查询"""
    
    def get_account_permissions(self, account: Account) -> Dict[str, Any]:
        """获取PostgreSQL账户权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return {"success": False, "error": "无法建立数据库连接"}
            
            global_perms = self.get_global_permissions(account)
            database_perms = self.get_database_permissions(account)
            
            # 分离预定义角色和角色属性
            predefined_roles = []
            role_attributes = []
            
            for perm in global_perms:
                if perm["privilege"] in ["SUPERUSER", "CREATEROLE", "CREATEDB", "REPLICATION"]:
                    role_attributes.append(perm["privilege"])
                else:
                    predefined_roles.append(perm["privilege"])
            
            return {
                "success": True,
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "host": account.host,
                    "plugin": account.plugin
                },
                "permissions": {
                    "predefined_roles": predefined_roles,
                    "role_attributes": role_attributes,
                    "database": database_perms
                }
            }
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return {"success": False, "error": str(e)}
        finally:
            if connection:
                connection.disconnect()
    
    def get_global_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取PostgreSQL全局权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            permissions = []
            
            # 查询角色属性（全局权限）
            query = """
                SELECT 
                    rolname as role_name,
                    rolsuper as is_superuser,
                    rolinherit as can_inherit,
                    rolcreaterole as can_create_role,
                    rolcreatedb as can_create_db,
                    rolcanlogin as can_login,
                    rolreplication as can_replicate
                FROM pg_roles 
                WHERE rolname = %s
            """
            
            results = connection.execute_query(query, (account.username,))
            
            if results:
                row = results[0]
                
                if row[1]:  # is_superuser
                    permissions.append({"privilege": "SUPERUSER", "granted": True, "grantable": False})
                if row[3]:  # can_create_role
                    permissions.append({"privilege": "CREATEROLE", "granted": True, "grantable": False})
                if row[4]:  # can_create_db
                    permissions.append({"privilege": "CREATEDB", "granted": True, "grantable": False})
                if row[6]:  # can_replicate
                    permissions.append({"privilege": "REPLICATION", "granted": True, "grantable": False})
            
            # 查询预定义角色
            predefined_roles_query = """
                SELECT 
                    r.rolname as role_name
                FROM pg_roles r
                JOIN pg_auth_members m ON r.oid = m.roleid
                JOIN pg_roles u ON m.member = u.oid
                WHERE u.rolname = %s
                AND r.rolname IN ('pg_read_all_data', 'pg_write_all_data', 'pg_monitor', 'pg_read_all_settings', 'pg_read_all_stats', 'pg_stat_scan_tables', 'pg_signal_backend', 'pg_read_server_files', 'pg_write_server_files', 'pg_execute_server_program')
            """
            
            predefined_results = connection.execute_query(predefined_roles_query, (account.username,))
            
            for row in predefined_results:
                permissions.append({"privilege": row[0], "granted": True, "grantable": False})
            
            return permissions
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def get_database_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取PostgreSQL数据库权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询数据库权限
            query = """
                SELECT 
                    datname as database_name,
                    has_database_privilege(%s, datname, 'CONNECT') as can_connect,
                    has_database_privilege(%s, datname, 'CREATE') as can_create,
                    has_database_privilege(%s, datname, 'TEMPORARY') as can_temp
                FROM pg_database 
                WHERE datistemplate = false
                ORDER BY datname
            """
            
            results = connection.execute_query(query, (account.username, account.username, account.username))
            
            return [
                {
                    "database": row[0],
                    "privileges": [
                        perm for perm, granted in [
                            ("CONNECT", row[1]),
                            ("CREATE", row[2]),
                            ("TEMPORARY", row[3])
                        ] if granted
                    ]
                }
                for row in results
                if any([row[1], row[2], row[3]])  # 只返回有权限的数据库
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def get_table_permissions(self, account: Account, database: str) -> List[Dict[str, Any]]:
        """获取PostgreSQL表权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询表权限
            query = """
                SELECT 
                    schemaname as schema_name,
                    tablename as table_name,
                    has_table_privilege(%s, schemaname||'.'||tablename, 'SELECT') as can_select,
                    has_table_privilege(%s, schemaname||'.'||tablename, 'INSERT') as can_insert,
                    has_table_privilege(%s, schemaname||'.'||tablename, 'UPDATE') as can_update,
                    has_table_privilege(%s, schemaname||'.'||tablename, 'DELETE') as can_delete
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, tablename
            """
            
            results = connection.execute_query(query, (account.username, account.username, account.username, account.username))
            
            return [
                {
                    "table": f"{row[0]}.{row[1]}",
                    "privileges": [
                        perm for perm, granted in [
                            ("SELECT", row[2]),
                            ("INSERT", row[3]),
                            ("UPDATE", row[4]),
                            ("DELETE", row[5])
                        ] if granted
                    ]
                }
                for row in results
                if any([row[2], row[3], row[4], row[5]])  # 只返回有权限的表
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()


class SQLServerPermissionQuery(PermissionQuery):
    """SQL Server权限查询"""
    
    def get_account_permissions(self, account: Account) -> Dict[str, Any]:
        """获取SQL Server账户权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return {"success": False, "error": "无法建立数据库连接"}
            
            global_perms = self.get_global_permissions(account)
            database_perms = self.get_database_permissions(account)
            
            # 分离SQL Server权限类型
            server_roles = []
            database_roles = {}
            
            for perm in global_perms:
                if perm.get("type") == "SERVER_ROLE":
                    server_roles.append({
                        "role": perm["name"],
                        "type": perm.get("type_desc", "SERVER_ROLE")
                    })
            
            for perm in database_perms:
                db_name = perm.get("database", "default")
                if db_name not in database_roles:
                    database_roles[db_name] = []
                
                roles = perm.get("roles", [])
                for role in roles:
                    database_roles[db_name].append({
                        "role": role["name"],
                        "type": role.get("type_desc", "DATABASE_ROLE")
                    })
            
            return {
                "success": True,
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "host": account.host,
                    "plugin": account.plugin
                },
                "permissions": {
                    "server_roles": server_roles,
                    "database_roles": database_roles
                }
            }
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return {"success": False, "error": str(e)}
        finally:
            if connection:
                connection.disconnect()
    
    def get_global_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取SQL Server全局权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询服务器角色
            query = """
                SELECT 
                    r.name as role_name,
                    r.type_desc as role_type
                FROM sys.server_role_members rm
                JOIN sys.server_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.server_principals p ON rm.member_principal_id = p.principal_id
                WHERE p.name = %s
            """
            
            results = connection.execute_query(query, (account.username,))
            
            return [
                {
                    "name": row[0],
                    "type": "SERVER_ROLE",
                    "type_desc": row[1],
                    "granted": True,
                    "grantable": False
                }
                for row in results
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def get_database_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取SQL Server数据库权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询数据库角色
            query = """
                SELECT 
                    db_name() as database_name,
                    r.name as role_name
                FROM sys.database_role_members rm
                JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.database_principals p ON rm.member_principal_id = p.principal_id
                WHERE p.name = %s
            """
            
            results = connection.execute_query(query, (account.username,))
            
            # 按数据库分组
            db_permissions = {}
            for row in results:
                db_name = row[0]
                role_name = row[1]
                
                if db_name not in db_permissions:
                    db_permissions[db_name] = []
                db_permissions[db_name].append({
                    "name": role_name,
                    "type": "DATABASE_ROLE",
                    "type_desc": "DATABASE_ROLE"
                })
            
            return [
                {
                    "database": db_name,
                    "roles": roles
                }
                for db_name, roles in db_permissions.items()
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def get_table_permissions(self, account: Account, database: str) -> List[Dict[str, Any]]:
        """获取SQL Server表权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询表权限
            query = """
                SELECT 
                    SCHEMA_NAME(t.schema_id) as schema_name,
                    t.name as table_name,
                    p.permission_name as permission
                FROM sys.tables t
                JOIN sys.database_permissions p ON p.major_id = t.object_id
                JOIN sys.database_principals pr ON p.grantee_principal_id = pr.principal_id
                WHERE pr.name = %s AND p.state = 'G'
                ORDER BY SCHEMA_NAME(t.schema_id), t.name
            """
            
            results = connection.execute_query(query, (account.username,))
            
            # 按表分组
            table_permissions = {}
            for row in results:
                table_name = f"{row[0]}.{row[1]}"
                permission = row[2]
                
                if table_name not in table_permissions:
                    table_permissions[table_name] = []
                table_permissions[table_name].append(permission)
            
            return [
                {
                    "table": table_name,
                    "privileges": permissions
                }
                for table_name, permissions in table_permissions.items()
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()


class OraclePermissionQuery(PermissionQuery):
    """Oracle权限查询"""
    
    def get_account_permissions(self, account: Account) -> Dict[str, Any]:
        """获取Oracle账户权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return {"success": False, "error": "无法建立数据库连接"}
            
            global_perms = self.get_global_permissions(account)
            database_perms = self.get_database_permissions(account)
            
            # 分离Oracle权限类型
            roles = []
            system_privileges = []
            tablespace_privileges = []
            tablespace_quotas = []
            
            for perm in global_perms:
                if perm["privilege"].startswith("ROLE_"):
                    roles.append(perm["privilege"])
                elif perm["privilege"].startswith("TABLESPACE_"):
                    tablespace_privileges.append(perm["privilege"])
                else:
                    system_privileges.append(perm["privilege"])
            
            # 处理表空间配额
            for perm in database_perms:
                if "quota" in perm:
                    tablespace_quotas.append(perm["quota"])
            
            return {
                "success": True,
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "host": account.host,
                    "plugin": account.plugin
                },
                "permissions": {
                    "roles": roles,
                    "system_privileges": system_privileges,
                    "tablespace_privileges": tablespace_privileges,
                    "tablespace_quotas": tablespace_quotas
                }
            }
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return {"success": False, "error": str(e)}
        finally:
            if connection:
                connection.disconnect()
    
    def get_global_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取Oracle全局权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            permissions = []
            
            # 查询系统权限
            sys_privs_query = """
                SELECT 
                    privilege,
                    admin_option
                FROM user_sys_privs
                ORDER BY privilege
            """
            
            sys_results = connection.execute_query(sys_privs_query, ())
            
            for row in sys_results:
                permissions.append({
                    "privilege": row[0],
                    "granted": True,
                    "grantable": row[1] == 'YES'
                })
            
            # 查询角色权限
            roles_query = """
                SELECT 
                    granted_role,
                    admin_option
                FROM user_role_privs
                ORDER BY granted_role
            """
            
            role_results = connection.execute_query(roles_query, ())
            
            for row in role_results:
                permissions.append({
                    "privilege": f"ROLE_{row[0]}",
                    "granted": True,
                    "grantable": row[1] == 'YES'
                })
            
            return permissions
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def get_database_permissions(self, account: Account) -> List[Dict[str, Any]]:
        """获取Oracle数据库权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            permissions = []
            
            # 查询表空间配额
            quota_query = """
                SELECT 
                    tablespace_name,
                    bytes,
                    max_bytes
                FROM user_ts_quotas
                ORDER BY tablespace_name
            """
            
            quota_results = connection.execute_query(quota_query, ())
            
            for row in quota_results:
                tablespace_name = row[0]
                current_bytes = row[1] if row[1] else 0
                max_bytes = row[2] if row[2] else 0
                
                if max_bytes > 0:
                    quota_info = f"{tablespace_name}: {self._format_bytes(current_bytes)}/{self._format_bytes(max_bytes)}"
                else:
                    quota_info = f"{tablespace_name}: {self._format_bytes(current_bytes)}/UNLIMITED"
                
                permissions.append({
                    "quota": quota_info
                })
            
            return permissions
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()
    
    def _format_bytes(self, bytes_value):
        """格式化字节数"""
        if bytes_value is None:
            return "0B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"
    
    def get_table_permissions(self, account: Account, database: str) -> List[Dict[str, Any]]:
        """获取Oracle表权限"""
        try:
            connection = self._get_connection()
            if not connection or not connection.connect():
                return []
            
            # 查询表权限
            query = """
                SELECT 
                    owner,
                    table_name,
                    privilege,
                    grantable
                FROM user_tab_privs
                WHERE grantee = :1
                ORDER BY owner, table_name, privilege
            """
            
            results = connection.execute_query(query, (account.username,))
            
            # 按表分组
            table_permissions = {}
            for row in results:
                table_name = f"{row[0]}.{row[1]}"
                privilege = row[2]
                
                if table_name not in table_permissions:
                    table_permissions[table_name] = []
                table_permissions[table_name].append(privilege)
            
            return [
                {
                    "table": table_name,
                    "privileges": permissions
                }
                for table_name, permissions in table_permissions.items()
            ]
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "account_id": account.id})
            return []
        finally:
            if connection:
                connection.disconnect()


class PermissionQueryFactory:
    """权限查询工厂"""
    
    # 数据库类型到权限查询类的映射
    QUERY_CLASSES = {
        "mysql": MySQLPermissionQuery,
        "postgresql": PostgreSQLPermissionQuery,
        "sqlserver": SQLServerPermissionQuery,
        "oracle": OraclePermissionQuery,
    }
    
    @staticmethod
    def create_query(instance: Instance) -> Optional[PermissionQuery]:
        """
        创建权限查询对象
        
        Args:
            instance: 数据库实例
            
        Returns:
            权限查询对象，如果类型不支持则返回None
        """
        db_type = instance.db_type.lower()
        
        if db_type not in PermissionQueryFactory.QUERY_CLASSES:
            log_error(
                f"不支持的数据库类型: {db_type}",
                context={"instance_id": instance.id, "db_type": db_type}
            )
            return None
        
        query_class = PermissionQueryFactory.QUERY_CLASSES[db_type]
        return query_class(instance)
    
    @staticmethod
    def get_account_permissions(instance: Instance, account: Account) -> Dict[str, Any]:
        """
        获取账户权限
        
        Args:
            instance: 数据库实例
            account: 账户对象
            
        Returns:
            权限信息字典
        """
        query = PermissionQueryFactory.create_query(instance)
        if not query:
            return {
                "success": False,
                "error": f"不支持的数据库类型: {instance.db_type}"
            }
        
        return query.get_account_permissions(account)
    
    @staticmethod
    def get_supported_types() -> list:
        """
        获取支持的数据库类型列表
        
        Returns:
            支持的数据库类型列表
        """
        return list(PermissionQueryFactory.QUERY_CLASSES.keys())
    
    @staticmethod
    def is_type_supported(db_type: str) -> bool:
        """
        检查数据库类型是否支持
        
        Args:
            db_type: 数据库类型名称
            
        Returns:
            是否支持该数据库类型
        """
        return db_type.lower() in PermissionQueryFactory.QUERY_CLASSES
