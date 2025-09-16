"""
泰摸鱼吧 - Oracle同步管理器
"""

from typing import Any, Dict, List

from app.models.current_account_sync_data import CurrentAccountSyncData
from app.utils import time_utils
from .base_sync_manager import BaseSyncManager


class OracleSyncManager(BaseSyncManager):
    """Oracle同步管理器"""

    def get_db_type(self) -> str:
        """获取数据库类型"""
        return "oracle"

    def get_accounts(self, conn) -> List[Dict[str, Any]]:
        """获取Oracle账户信息"""
        try:
            # 获取过滤规则
            from app.services.database_filter_manager import DatabaseFilterManager

            filter_manager = DatabaseFilterManager()
            filter_conditions = filter_manager.get_safe_sql_filter_conditions("oracle", "username")

            # 构建查询SQL
            where_clause, params = filter_conditions
            sql = f"""
                SELECT username, account_status, lock_date, expiry_date, 
                       created, profile, authentication_type
                FROM dba_users 
                WHERE {where_clause}
            """

            # 查询用户信息
            users = conn.execute_query(sql, params)

            accounts = []
            for row in users:
                username, account_status, lock_date, expiry_date, created, profile, auth_type = row

                # 获取用户权限
                permissions = self.get_user_permissions(conn, username)

                # 判断是否为超级用户（具有DBA角色或系统权限）
                roles = permissions.get("roles", [])
                system_privileges = permissions.get("system_privileges", [])
                is_superuser = (
                    "DBA" in roles or 
                    "SYSDBA" in roles or 
                    "SYSOPER" in roles or
                    "GRANT ANY PRIVILEGE" in system_privileges
                )

                accounts.append({
                    "username": username,
                    "permissions": permissions,
                    "is_superuser": is_superuser
                })

            self.sync_logger.info(f"获取到 {len(accounts)} 个Oracle账户")
            return accounts

        except Exception as e:
            self.sync_logger.error("获取Oracle账户失败", error=str(e))
            return []

    def get_user_permissions(self, conn, username: str) -> Dict[str, Any]:
        """获取Oracle用户权限信息"""
        try:
            permissions = {
                "roles": [],
                "system_privileges": [],
                "tablespace_privileges": {},
            }
            
            # 获取用户角色
            roles_sql = """
                SELECT granted_role 
                FROM dba_role_privs 
                WHERE grantee = :username
            """
            roles = conn.execute_query(roles_sql, {"username": username})
            permissions["roles"] = [role[0] for role in roles] if roles else []
            
            # 获取系统权限
            system_privs_sql = """
                SELECT privilege 
                FROM dba_sys_privs 
                WHERE grantee = :username
            """
            system_privs = conn.execute_query(system_privs_sql, {"username": username})
            permissions["system_privileges"] = [priv[0] for priv in system_privs] if system_privs else []
            
            # 获取表空间权限
            permissions["tablespace_privileges"] = self._get_tablespace_privileges(conn, username)

            return permissions
            
        except Exception as e:
            self.sync_logger.error(f"获取Oracle用户权限失败: {username}", error=str(e))
            return {
                "roles": [],
                "system_privileges": [],
                "tablespace_privileges": {},
            }

    def _get_tablespace_privileges(self, conn, username: str) -> Dict[str, List[str]]:
        """获取Oracle表空间权限"""
        tablespace_privileges = {}
        
        try:
            # 1. 检查是否有UNLIMITED TABLESPACE系统权限
            unlimited_ts_sql = """
                SELECT privilege 
                FROM dba_sys_privs 
                WHERE grantee = :username AND privilege = 'UNLIMITED TABLESPACE'
            """
            unlimited_result = conn.execute_query(unlimited_ts_sql, {"username": username})
            
            if unlimited_result:
                # 如果有UNLIMITED TABLESPACE权限，设置通用表空间权限标识
                tablespace_privileges["ALL_TABLESPACES"] = ["UNLIMITED"]
            
            # 2. 尝试获取具体的表空间配额信息
            try:
                ts_quota_sql = """
                    SELECT tablespace_name, 
                           CASE 
                               WHEN max_bytes = -1 THEN 'UNLIMITED'
                               ELSE 'QUOTA'
                           END as privilege
                    FROM dba_ts_quotas 
                    WHERE username = :username
                """
                ts_quota_privs = conn.execute_query(ts_quota_sql, {"username": username})
                if ts_quota_privs:
                    for ts_name, privilege in ts_quota_privs:
                        if ts_name not in tablespace_privileges:
                            tablespace_privileges[ts_name] = []
                        if privilege not in tablespace_privileges[ts_name]:
                            tablespace_privileges[ts_name].append(privilege)
            except Exception as e:
                # 如果dba_ts_quotas不可用，尝试使用user_ts_quotas
                try:
                    user_quota_sql = """
                        SELECT tablespace_name, 
                               CASE 
                                   WHEN max_bytes = -1 THEN 'UNLIMITED'
                                   ELSE 'QUOTA'
                               END as privilege
                        FROM user_ts_quotas
                    """
                    user_quota_privs = conn.execute_query(user_quota_sql)
                    if user_quota_privs:
                        for ts_name, privilege in user_quota_privs:
                            if ts_name not in tablespace_privileges:
                                tablespace_privileges[ts_name] = []
                            if privilege not in tablespace_privileges[ts_name]:
                                tablespace_privileges[ts_name].append(privilege)
                except Exception as e2:
                    self.sync_logger.debug(f"无法获取表空间配额信息: {e2}")
            
            # 3. 尝试获取用户在表空间中的对象权限
            try:
                user_tables_sql = """
                    SELECT DISTINCT tablespace_name, 'OWNER' as privilege
                    FROM dba_tables 
                    WHERE owner = :username
                    AND tablespace_name IS NOT NULL
                """
                user_tables = conn.execute_query(user_tables_sql, {"username": username})
                if user_tables:
                    for ts_name, privilege in user_tables:
                        if ts_name not in tablespace_privileges:
                            tablespace_privileges[ts_name] = []
                        if privilege not in tablespace_privileges[ts_name]:
                            tablespace_privileges[ts_name].append(privilege)
            except Exception as e:
                # 如果dba_tables不可用，尝试使用user_tables
                try:
                    user_tables_sql = """
                        SELECT DISTINCT tablespace_name, 'OWNER' as privilege
                        FROM user_tables 
                        WHERE tablespace_name IS NOT NULL
                    """
                    user_tables = conn.execute_query(user_tables_sql)
                    if user_tables:
                        for ts_name, privilege in user_tables:
                            if ts_name not in tablespace_privileges:
                                tablespace_privileges[ts_name] = []
                            if privilege not in tablespace_privileges[ts_name]:
                                tablespace_privileges[ts_name].append(privilege)
                except Exception as e2:
                    self.sync_logger.debug(f"无法获取用户表空间对象权限: {e2}")
            
            # 4. 尝试获取用户在表空间中的索引权限
            try:
                user_indexes_sql = """
                    SELECT DISTINCT tablespace_name, 'INDEX_OWNER' as privilege
                    FROM dba_indexes 
                    WHERE owner = :username
                    AND tablespace_name IS NOT NULL
                """
                user_indexes = conn.execute_query(user_indexes_sql, {"username": username})
                if user_indexes:
                    for ts_name, privilege in user_indexes:
                        if ts_name not in tablespace_privileges:
                            tablespace_privileges[ts_name] = []
                        if privilege not in tablespace_privileges[ts_name]:
                            tablespace_privileges[ts_name].append(privilege)
            except Exception as e:
                # 如果dba_indexes不可用，尝试使用user_indexes
                try:
                    user_indexes_sql = """
                        SELECT DISTINCT tablespace_name, 'INDEX_OWNER' as privilege
                        FROM user_indexes 
                        WHERE tablespace_name IS NOT NULL
                    """
                    user_indexes = conn.execute_query(user_indexes_sql)
                    if user_indexes:
                        for ts_name, privilege in user_indexes:
                            if ts_name not in tablespace_privileges:
                                tablespace_privileges[ts_name] = []
                            if privilege not in tablespace_privileges[ts_name]:
                                tablespace_privileges[ts_name].append(privilege)
                except Exception as e2:
                    self.sync_logger.debug(f"无法获取用户表空间索引权限: {e2}")
            
        except Exception as e:
            self.sync_logger.error(f"获取Oracle表空间权限失败: {username}", error=str(e))
        
        return tablespace_privileges

    def create_account(self, instance_id: int, username: str, permissions_data: Dict[str, Any], 
                      is_superuser: bool, session_id: str = None) -> CurrentAccountSyncData:
        """创建Oracle账户"""
        account = CurrentAccountSyncData(
            instance_id=instance_id,
            db_type="oracle",
            username=username,
            oracle_roles=permissions_data.get("roles", []),
            system_privileges=permissions_data.get("system_privileges", []),
            tablespace_privileges_oracle=permissions_data.get("tablespace_privileges", {}),
            type_specific=permissions_data.get("type_specific", {}),
            is_superuser=is_superuser,
            last_change_type="add",
            session_id=session_id,
        )
        return account

    def update_account(self, account: CurrentAccountSyncData, permissions_data: Dict[str, Any], 
                      is_superuser: bool) -> None:
        """更新Oracle账户数据"""
        account.oracle_roles = permissions_data.get("roles", [])
        account.system_privileges = permissions_data.get("system_privileges", [])
        account.tablespace_privileges_oracle = permissions_data.get("tablespace_privileges", {})
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.is_deleted = False
        account.deleted_time = None
        account.last_change_type = "modify_privilege"
        account.last_change_time = time_utils.now()
        account.last_sync_time = time_utils.now()

    def detect_changes(self, account: CurrentAccountSyncData, new_permissions: Dict[str, Any]) -> Dict[str, Any]:
        """检测Oracle权限变更"""
        changes = {}

        # 检测角色变更
        old_roles = set(account.oracle_roles or [])
        new_roles = set(new_permissions.get("roles", []))
        if old_roles != new_roles:
            changes["roles"] = {
                "added": list(new_roles - old_roles),
                "removed": list(old_roles - new_roles),
            }

        # 检测系统权限变更
        old_system_perms = set(account.system_privileges or [])
        new_system_perms = set(new_permissions.get("system_privileges", []))
        if old_system_perms != new_system_perms:
            changes["system_privileges"] = {
                "added": list(new_system_perms - old_system_perms),
                "removed": list(old_system_perms - new_system_perms),
            }

        # 检测表空间权限变更
        old_tablespace_perms = account.tablespace_privileges_oracle or {}
        new_tablespace_perms = new_permissions.get("tablespace_privileges", {})
        if old_tablespace_perms != new_tablespace_perms:
            changes["tablespace_privileges"] = {
                "added": {
                    k: v for k, v in new_tablespace_perms.items() 
                    if k not in old_tablespace_perms or set(old_tablespace_perms[k]) != set(v)
                },
                "removed": {
                    k: v for k, v in old_tablespace_perms.items()
                    if k not in new_tablespace_perms or set(new_tablespace_perms.get(k, [])) != set(v)
                },
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
        """验证Oracle权限数据完整性"""
        if not permissions_data:
            self.sync_logger.warning(f"Oracle用户 {username} 权限数据为空")
            return False

        required_fields = ["roles", "system_privileges", "tablespace_privileges"]
        missing_fields = []

        for field in required_fields:
            if field not in permissions_data:
                missing_fields.append(field)

        if missing_fields:
            self.sync_logger.warning(f"Oracle用户 {username} 权限数据缺少字段: {missing_fields}")
            return False

        # 检查数据类型
        if not isinstance(permissions_data.get("roles"), list):
            self.sync_logger.warning(f"Oracle用户 {username} 角色应该是列表格式")
            return False

        if not isinstance(permissions_data.get("system_privileges"), list):
            self.sync_logger.warning(f"Oracle用户 {username} 系统权限应该是列表格式")
            return False

        if not isinstance(permissions_data.get("tablespace_privileges"), dict):
            self.sync_logger.warning(f"Oracle用户 {username} 表空间权限应该是字典格式")
            return False

        return True
