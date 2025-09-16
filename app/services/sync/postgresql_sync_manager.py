"""
泰摸鱼吧 - PostgreSQL同步管理器
"""

from typing import Any, Dict, List

from app.models.current_account_sync_data import CurrentAccountSyncData
from app.utils import time_utils
from .base_sync_manager import BaseSyncManager


class PostgreSQLSyncManager(BaseSyncManager):
    """PostgreSQL同步管理器"""

    def get_db_type(self) -> str:
        """获取数据库类型"""
        return "postgresql"

    def get_accounts(self, conn) -> List[Dict[str, Any]]:
        """获取PostgreSQL账户信息"""
        try:
            # 获取过滤规则
            from app.services.database_filter_manager import DatabaseFilterManager

            filter_manager = DatabaseFilterManager()
            filter_conditions = filter_manager.get_safe_sql_filter_conditions("postgresql", "rolname")

            # 构建查询SQL
            where_clause, params = filter_conditions
            sql = f"""
                SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, 
                       rolcanlogin, rolreplication, rolbypassrls, rolconnlimit, 
                       rolpassword, rolvaliduntil
                FROM pg_roles 
                WHERE {where_clause}
            """

            # 查询角色信息
            roles = conn.execute_query(sql, params)

            accounts = []
            for row in roles:
                (rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, 
                 rolcanlogin, rolreplication, rolbypassrls, rolconnlimit, 
                 rolpassword, rolvaliduntil) = row

                # 获取用户权限
                permissions = self.get_user_permissions(conn, rolname)

                # 判断是否为超级用户
                is_superuser = bool(rolsuper)

                accounts.append({
                    "username": rolname,
                    "permissions": permissions,
                    "is_superuser": is_superuser
                })

            self.sync_logger.info(f"获取到 {len(accounts)} 个PostgreSQL账户")
            return accounts

        except Exception as e:
            self.sync_logger.error("获取PostgreSQL账户失败", error=str(e))
            return []

    def get_user_permissions(self, conn, username: str) -> Dict[str, Any]:
        """获取PostgreSQL用户权限信息"""
        try:
            permissions = {
                "predefined_roles": [],
                "role_attributes": {},
                "database_privileges": {},
                "tablespace_privileges": {},
                "system_privileges": []
            }

            # 获取角色属性
            role_sql = """
                SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, 
                       rolcanlogin, rolreplication, rolbypassrls, rolconnlimit, 
                       rolvaliduntil
                FROM pg_roles 
                WHERE rolname = %s
            """
            role_info = conn.execute_query(role_sql, (username,))
            
            if role_info:
                row = role_info[0]
                permissions["role_attributes"] = {
                    "SUPERUSER": bool(row[1]),
                    "INHERIT": bool(row[2]),
                    "CREATEROLE": bool(row[3]),
                    "CREATEDB": bool(row[4]),
                    "LOGIN": bool(row[5]),
                    "REPLICATION": bool(row[6]),
                    "BYPASSRLS": bool(row[7]),
                    "CONNECTION_LIMIT": row[8] if row[8] != -1 else None,
                    "VALID_UNTIL": row[9].isoformat() if row[9] else None
                }

            # 获取表空间权限
            tablespace_sql = """
                SELECT spcname, 'CREATE' as privilege
                FROM pg_tablespace t
                WHERE has_tablespace_privilege(%s, t.oid, 'CREATE')
            """
            tablespace_privs = conn.execute_query(tablespace_sql, (username,))
            tablespace_privileges = {}
            for priv in tablespace_privs:
                ts_name = priv[0]
                priv_type = priv[1]
                if ts_name not in tablespace_privileges:
                    tablespace_privileges[ts_name] = []
                tablespace_privileges[ts_name].append(priv_type)
            
            permissions["tablespace_privileges"] = tablespace_privileges

            # 获取数据库权限
            db_privs_sql = """
                SELECT table_catalog, privilege_type
                FROM information_schema.table_privileges
                WHERE grantee = %s
                ORDER BY table_catalog, privilege_type
            """
            db_privs = conn.execute_query(db_privs_sql, (username,))
            database_privileges = {}
            for priv in db_privs:
                db_name = priv[0]
                priv_type = priv[1]
                if db_name not in database_privileges:
                    database_privileges[db_name] = []
                database_privileges[db_name].append(priv_type)
            
            permissions["database_privileges"] = database_privileges

            # 获取角色成员关系（预定义角色）
            role_members_sql = """
                SELECT r.rolname
                FROM pg_auth_members m
                JOIN pg_roles r ON m.roleid = r.oid
                WHERE m.member = (SELECT oid FROM pg_roles WHERE rolname = %s)
            """
            role_members = conn.execute_query(role_members_sql, (username,))
            permissions["predefined_roles"] = [member[0] for member in role_members]

            return permissions

        except Exception as e:
            self.sync_logger.error(f"获取PostgreSQL权限失败: {username}", error=str(e))
            return {
                "predefined_roles": [],
                "role_attributes": {},
                "database_privileges": {},
                "tablespace_privileges": {},
                "system_privileges": [],
            }

    def create_account(self, instance_id: int, username: str, permissions_data: Dict[str, Any], 
                      is_superuser: bool, session_id: str = None) -> CurrentAccountSyncData:
        """创建PostgreSQL账户"""
        account = CurrentAccountSyncData(
            instance_id=instance_id,
            db_type="postgresql",
            username=username,
            predefined_roles=permissions_data.get("predefined_roles", []),
            role_attributes=permissions_data.get("role_attributes", {}),
            database_privileges_pg=permissions_data.get("database_privileges", {}),
            tablespace_privileges=permissions_data.get("tablespace_privileges", {}),
            system_privileges=permissions_data.get("system_privileges", []),
            type_specific=permissions_data.get("type_specific", {}),
            is_superuser=is_superuser,
            last_change_type="add",
            session_id=session_id,
        )
        return account

    def update_account(self, account: CurrentAccountSyncData, permissions_data: Dict[str, Any], 
                      is_superuser: bool) -> None:
        """更新PostgreSQL账户数据"""
        account.predefined_roles = permissions_data.get("predefined_roles", [])
        account.role_attributes = permissions_data.get("role_attributes", {})
        account.database_privileges_pg = permissions_data.get("database_privileges", {})
        account.tablespace_privileges = permissions_data.get("tablespace_privileges", {})
        account.system_privileges = permissions_data.get("system_privileges", [])
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.last_change_type = "modify_privilege"
        account.last_change_time = time_utils.now()
        account.last_sync_time = time_utils.now()

    def detect_changes(self, account: CurrentAccountSyncData, new_permissions: Dict[str, Any]) -> Dict[str, Any]:
        """检测PostgreSQL权限变更"""
        changes = {}

        # 检测预定义角色变更
        old_roles = set(account.predefined_roles or [])
        new_roles = set(new_permissions.get("predefined_roles", []))
        if old_roles != new_roles:
            changes["predefined_roles"] = {
                "added": list(new_roles - old_roles),
                "removed": list(old_roles - new_roles),
            }

        # 检测角色属性变更
        old_attrs = account.role_attributes or {}
        new_attrs = new_permissions.get("role_attributes", {})
        if old_attrs != new_attrs:
            changes["role_attributes"] = {
                "added": {k: v for k, v in new_attrs.items() 
                         if k not in old_attrs or old_attrs[k] != v},
                "removed": {k: v for k, v in old_attrs.items() 
                           if k not in new_attrs or new_attrs[k] != v},
            }

        # 检测数据库权限变更
        old_db_perms = account.database_privileges_pg or {}
        new_db_perms = new_permissions.get("database_privileges", {})
        if old_db_perms != new_db_perms:
            changes["database_privileges"] = {
                "added": {
                    k: v for k, v in new_db_perms.items() 
                    if k not in old_db_perms or set(old_db_perms[k]) != set(v)
                },
                "removed": {
                    k: v for k, v in old_db_perms.items()
                    if k not in new_db_perms or set(new_db_perms.get(k, [])) != set(v)
                },
            }

        # 检测表空间权限变更
        old_ts_perms = account.tablespace_privileges or {}
        new_ts_perms = new_permissions.get("tablespace_privileges", {})
        if old_ts_perms != new_ts_perms:
            changes["tablespace_privileges"] = {
                "added": {
                    k: v for k, v in new_ts_perms.items() 
                    if k not in old_ts_perms or set(old_ts_perms[k]) != set(v)
                },
                "removed": {
                    k: v for k, v in old_ts_perms.items()
                    if k not in new_ts_perms or set(new_ts_perms.get(k, [])) != set(v)
                },
            }

        # 检测系统权限变更
        old_system_perms = set(account.system_privileges or [])
        new_system_perms = set(new_permissions.get("system_privileges", []))
        if old_system_perms != new_system_perms:
            changes["system_privileges"] = {
                "added": list(new_system_perms - old_system_perms),
                "removed": list(old_system_perms - new_system_perms),
            }

        # 检测type_specific字段中的属性变更
        old_type_specific = account.type_specific or {}
        new_type_specific = new_permissions.get("type_specific", {})
        
        if old_type_specific != new_type_specific:
            changes["type_specific"] = {
                "added": {k: v for k, v in new_type_specific.items() 
                         if k not in old_type_specific or old_type_specific[k] != v},
                "removed": {k: v for k, v in old_type_specific.items() 
                           if k not in new_type_specific or new_type_specific[k] != v},
            }

        return changes

    def validate_permissions_data(self, permissions_data: Dict[str, Any], username: str) -> bool:
        """验证PostgreSQL权限数据完整性"""
        if not permissions_data:
            self.sync_logger.warning(f"PostgreSQL用户 {username} 权限数据为空")
            return False

        required_fields = [
            "predefined_roles", "role_attributes", "database_privileges", 
            "tablespace_privileges", "system_privileges"
        ]
        missing_fields = []

        for field in required_fields:
            if field not in permissions_data:
                missing_fields.append(field)

        if missing_fields:
            self.sync_logger.warning(f"PostgreSQL用户 {username} 权限数据缺少字段: {missing_fields}")
            return False

        # 检查数据类型
        if not isinstance(permissions_data.get("predefined_roles"), list):
            self.sync_logger.warning(f"PostgreSQL用户 {username} 预定义角色应该是列表格式")
            return False

        if not isinstance(permissions_data.get("role_attributes"), dict):
            self.sync_logger.warning(f"PostgreSQL用户 {username} 角色属性应该是字典格式")
            return False

        if not isinstance(permissions_data.get("database_privileges"), dict):
            self.sync_logger.warning(f"PostgreSQL用户 {username} 数据库权限应该是字典格式")
            return False

        if not isinstance(permissions_data.get("tablespace_privileges"), dict):
            self.sync_logger.warning(f"PostgreSQL用户 {username} 表空间权限应该是字典格式")
            return False

        if not isinstance(permissions_data.get("system_privileges"), list):
            self.sync_logger.warning(f"PostgreSQL用户 {username} 系统权限应该是列表格式")
            return False

        return True
