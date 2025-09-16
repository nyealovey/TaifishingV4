"""
泰摸鱼吧 - SQL Server同步管理器
"""

from typing import Any, Dict, List, Tuple

from app.models.current_account_sync_data import CurrentAccountSyncData
from app.utils import time_utils
from .base_sync_manager import BaseSyncManager


class SQLServerSyncManager(BaseSyncManager):
    """SQL Server同步管理器"""

    def get_db_type(self) -> str:
        """获取数据库类型"""
        return "sqlserver"

    def get_accounts(self, conn) -> List[Dict[str, Any]]:
        """获取SQL Server账户信息"""
        try:
            # 获取过滤规则
            from app.services.database_filter_manager import DatabaseFilterManager

            filter_manager = DatabaseFilterManager()
            filter_conditions = filter_manager.get_safe_sql_filter_conditions("sqlserver", "sp.name")

            # 构建查询SQL
            where_clause, params = filter_conditions
            sql = f"""
                SELECT
                    sp.name as username,
                    sp.is_disabled as is_disabled,
                    sp.type_desc as login_type,
                    sp.type as type,
                    CASE 
                        WHEN sp.type = 'S' THEN LOGINPROPERTY(sp.name, 'PasswordLastSetTime')
                        ELSE NULL
                    END as password_last_set_time,
                    CASE 
                        WHEN sp.type = 'S' THEN sl.is_expiration_checked
                        ELSE NULL
                    END as is_expiration_checked
                FROM sys.server_principals sp
                LEFT JOIN sys.sql_logins sl ON sp.principal_id = sl.principal_id AND sp.type = 'S'
                WHERE sp.type IN ('S', 'U', 'G') AND {where_clause}
            """

            # 查询登录信息
            logins = conn.execute_query(sql, params)

            accounts = []
            for row in logins:
                username, is_disabled, login_type, type, password_last_set_time, is_expiration_checked = row

                # 获取用户权限
                permissions = self.get_user_permissions(conn, username)

                # 判断是否为超级用户（sa账户或sysadmin角色）
                server_roles = permissions.get("server_roles", [])
                is_superuser = username.lower() == "sa" or "sysadmin" in server_roles

                accounts.append({
                    "username": username,
                    "permissions": permissions,
                    "is_superuser": is_superuser
                })

            self.sync_logger.info(f"获取到 {len(accounts)} 个SQL Server账户")
            return accounts

        except Exception as e:
            self.sync_logger.error("获取SQL Server账户失败", error=str(e))
            return []

    def get_user_permissions(self, conn, username: str) -> Dict[str, Any]:
        """获取SQL Server用户权限信息"""
        try:
            permissions = {
                "server_roles": [],
                "server_permissions": [],
                "database_roles": {},
                "database_permissions": {},
                "type_specific": {}
            }

            # 获取服务器角色
            permissions["server_roles"] = self._get_server_roles(conn, username)

            # 获取服务器权限
            permissions["server_permissions"] = self._get_server_permissions(conn, username)

            # 获取数据库角色和权限
            db_roles, db_perms = self._get_database_permissions(conn, username)
            permissions["database_roles"] = db_roles
            permissions["database_permissions"] = db_perms

            # 获取账户详细信息
            account_info = self._get_account_info(conn, username)
            permissions["type_specific"] = account_info

            return permissions

        except Exception as e:
            self.sync_logger.error(f"获取SQL Server用户权限失败: {username}", error=str(e))
            return {
                "server_roles": [],
                "server_permissions": [],
                "database_roles": {},
                "database_permissions": {},
                "type_specific": {}
            }

    def _get_server_roles(self, conn, username: str) -> List[str]:
        """获取SQL Server服务器角色"""
        try:
            sql = """
                SELECT r.name
                FROM sys.server_role_members rm
                JOIN sys.server_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.server_principals p ON rm.member_principal_id = p.principal_id
                WHERE p.name = %s
            """
            roles = conn.execute_query(sql, (username,))
            return [role[0] for role in roles]
        except Exception as e:
            self.sync_logger.error(f"获取SQL Server服务器角色失败: {username}", error=str(e))
            return []

    def _get_server_permissions(self, conn, username: str) -> List[str]:
        """获取SQL Server服务器权限"""
        try:
            sql = """
                SELECT permission_name
                FROM sys.server_permissions
                WHERE grantee_principal_id = (
                    SELECT principal_id
                    FROM sys.server_principals
                    WHERE name = %s
                )
                AND state = 'G'
            """
            permissions = conn.execute_query(sql, (username,))
            return [perm[0] for perm in permissions]
        except Exception as e:
            self.sync_logger.error(f"获取SQL Server服务器权限失败: {username}", error=str(e))
            return []

    def _get_database_permissions(self, conn, username: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """获取SQL Server数据库角色和权限"""
        try:
            database_roles = {}
            database_permissions = {}

            # 获取所有在线数据库
            databases_sql = "SELECT name FROM sys.databases WHERE state = 0"
            databases = conn.execute_query(databases_sql)

            for db_row in databases:
                db_name = db_row[0]
                try:
                    # 检查用户是否存在于该数据库
                    user_exists_sql = f"""
                        SELECT principal_id, name, type_desc
                        FROM [{db_name}].sys.database_principals
                        WHERE name = %s
                    """
                    
                    user_info = conn.execute_query(user_exists_sql, (username,))
                    
                    if not user_info:
                        continue  # 用户不存在于该数据库
                        
                    user_principal_id = user_info[0][0]
                    
                    # 获取数据库角色
                    roles_sql = f"""
                        SELECT r.name
                        FROM [{db_name}].sys.database_role_members rm
                        JOIN [{db_name}].sys.database_principals r ON rm.role_principal_id = r.principal_id
                        WHERE rm.member_principal_id = %s
                    """
                    
                    roles = conn.execute_query(roles_sql, (user_principal_id,))
                    if roles:
                        database_roles[db_name] = [role[0] for role in roles]
                    
                    # 获取数据库权限
                    perms_sql = f"""
                        SELECT permission_name
                        FROM [{db_name}].sys.database_permissions
                        WHERE grantee_principal_id = %s AND state = 'G'
                    """
                    
                    permissions = conn.execute_query(perms_sql, (user_principal_id,))
                    if permissions:
                        database_permissions[db_name] = [perm[0] for perm in permissions]

                except Exception as e:
                    self.sync_logger.warning(f"无法访问数据库 {db_name}: {str(e)}")
                    continue

            return database_roles, database_permissions

        except Exception as e:
            self.sync_logger.error(f"获取SQL Server数据库权限失败: {username}", error=str(e))
            return {}, {}

    def _get_account_info(self, conn, username: str) -> Dict[str, Any]:
        """获取账户详细信息"""
        try:
            sql = """
                SELECT
                    sp.name as username,
                    sp.is_disabled as is_disabled,
                    sp.type_desc as login_type,
                    sp.type as type,
                    CASE 
                        WHEN sp.type = 'S' THEN LOGINPROPERTY(sp.name, 'PasswordLastSetTime')
                        ELSE NULL
                    END as password_last_set_time,
                    CASE 
                        WHEN sp.type = 'S' THEN sl.is_expiration_checked
                        ELSE NULL
                    END as is_expiration_checked
                FROM sys.server_principals sp
                LEFT JOIN sys.sql_logins sl ON sp.principal_id = sl.principal_id AND sp.type = 'S'
                WHERE sp.name = %s
            """
            
            result = conn.execute_query(sql, (username,))
            if not result:
                return {}
                
            row = result[0]
            username, is_disabled, login_type, type, password_last_set_time, is_expiration_checked = row
            
            account_info = {
                "is_locked": bool(is_disabled),
                "account_type": login_type,
                "login_type": type,
            }
            
            # 只有SQL登录(S)才存储密码相关信息
            if type == 'S':
                account_info.update({
                    "password_last_set_time": (
                        password_last_set_time.isoformat() 
                        if password_last_set_time and hasattr(password_last_set_time, 'isoformat') 
                        else None
                    ),
                    "is_expiration_checked": (
                        bool(is_expiration_checked) 
                        if is_expiration_checked is not None 
                        else None
                    )
                })
            
            return account_info
            
        except Exception as e:
            self.sync_logger.error(f"获取SQL Server账户信息失败: {username}", error=str(e))
            return {}

    def create_account(self, instance_id: int, username: str, permissions_data: Dict[str, Any], 
                      is_superuser: bool, session_id: str = None) -> CurrentAccountSyncData:
        """创建SQL Server账户"""
        account = CurrentAccountSyncData(
            instance_id=instance_id,
            db_type="sqlserver",
            username=username,
            server_roles=permissions_data.get("server_roles", []),
            server_permissions=permissions_data.get("server_permissions", []),
            database_roles=permissions_data.get("database_roles", {}),
            database_permissions=permissions_data.get("database_permissions", {}),
            type_specific=permissions_data.get("type_specific", {}),
            is_superuser=is_superuser,
            last_change_type="add",
            session_id=session_id,
        )
        return account

    def update_account(self, account: CurrentAccountSyncData, permissions_data: Dict[str, Any], 
                      is_superuser: bool) -> None:
        """更新SQL Server账户数据"""
        account.server_roles = permissions_data.get("server_roles", [])
        account.server_permissions = permissions_data.get("server_permissions", [])
        account.database_roles = permissions_data.get("database_roles", {})
        account.database_permissions = permissions_data.get("database_permissions", {})
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.is_deleted = False
        account.deleted_time = None
        account.last_change_type = "modify_privilege"
        account.last_change_time = time_utils.now()
        account.last_sync_time = time_utils.now()

    def detect_changes(self, account: CurrentAccountSyncData, new_permissions: Dict[str, Any]) -> Dict[str, Any]:
        """检测SQL Server权限变更"""
        changes = {}

        # 检测服务器角色变更
        old_roles = set(account.server_roles or [])
        new_roles = set(new_permissions.get("server_roles", []))
        if old_roles != new_roles:
            changes["server_roles"] = {
                "added": list(new_roles - old_roles),
                "removed": list(old_roles - new_roles),
            }

        # 检测服务器权限变更
        old_perms = set(account.server_permissions or [])
        new_perms = set(new_permissions.get("server_permissions", []))
        if old_perms != new_perms:
            changes["server_permissions"] = {
                "added": list(new_perms - old_perms),
                "removed": list(old_perms - new_perms),
            }

        # 检测数据库角色变更
        old_db_roles = account.database_roles or {}
        new_db_roles = new_permissions.get("database_roles", {})
        if old_db_roles != new_db_roles:
            changes["database_roles"] = {
                "added": {
                    k: v for k, v in new_db_roles.items() 
                    if k not in old_db_roles or set(old_db_roles[k]) != set(v)
                },
                "removed": {
                    k: v for k, v in old_db_roles.items()
                    if k not in new_db_roles or set(new_db_roles.get(k, [])) != set(v)
                },
            }

        # 检测数据库权限变更
        old_db_perms = account.database_permissions or {}
        new_db_perms = new_permissions.get("database_permissions", {})
        if old_db_perms != new_db_perms:
            changes["database_permissions"] = {
                "added": {
                    k: v for k, v in new_db_perms.items() 
                    if k not in old_db_perms or set(old_db_perms[k]) != set(v)
                },
                "removed": {
                    k: v for k, v in old_db_perms.items()
                    if k not in new_db_perms or set(new_db_perms.get(k, [])) != set(v)
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
        """验证SQL Server权限数据完整性"""
        if not permissions_data:
            self.sync_logger.warning(f"SQL Server用户 {username} 权限数据为空")
            return False

        required_fields = [
            "server_roles", "server_permissions", "database_roles", "database_permissions"
        ]
        missing_fields = []

        for field in required_fields:
            if field not in permissions_data:
                missing_fields.append(field)

        if missing_fields:
            self.sync_logger.warning(f"SQL Server用户 {username} 权限数据缺少字段: {missing_fields}")
            return False

        # 检查数据类型
        if not isinstance(permissions_data.get("server_roles"), list):
            self.sync_logger.warning(f"SQL Server用户 {username} 服务器角色应该是列表格式")
            return False

        if not isinstance(permissions_data.get("server_permissions"), list):
            self.sync_logger.warning(f"SQL Server用户 {username} 服务器权限应该是列表格式")
            return False

        if not isinstance(permissions_data.get("database_roles"), dict):
            self.sync_logger.warning(f"SQL Server用户 {username} 数据库角色应该是字典格式")
            return False

        if not isinstance(permissions_data.get("database_permissions"), dict):
            self.sync_logger.warning(f"SQL Server用户 {username} 数据库权限应该是字典格式")
            return False

        return True
