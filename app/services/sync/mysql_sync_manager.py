"""
泰摸鱼吧 - MySQL同步管理器
"""

from typing import Any, Dict, List

from app.models.current_account_sync_data import CurrentAccountSyncData
from app.utils import time_utils
from .base_sync_manager import BaseSyncManager


class MySQLSyncManager(BaseSyncManager):
    """MySQL同步管理器"""

    def get_db_type(self) -> str:
        """获取数据库类型"""
        return "mysql"

    def get_accounts(self, conn) -> List[Dict[str, Any]]:
        """获取MySQL账户信息"""
        try:
            # 获取过滤规则
            from app.services.database_filter_manager import DatabaseFilterManager

            filter_manager = DatabaseFilterManager()
            filter_conditions = filter_manager.get_safe_sql_filter_conditions("mysql", "User")

            # 构建查询SQL
            where_clause, params = filter_conditions
            sql = f"""
                SELECT User, Host,
                       account_locked as is_locked,
                       password_expired as password_expired
                FROM mysql.user
                WHERE {where_clause}
            """

            # 查询用户信息
            users = conn.execute_query(sql, params)

            accounts = []
            for row in users:
                username, host, is_locked, password_expired = row
                full_username = f"{username}@{host}"

                # 获取用户权限
                permissions = self.get_user_permissions(conn, full_username)

                # 判断是否为超级用户（具有SUPER权限）
                global_privileges = permissions.get("global_privileges", [])
                is_superuser = False
                
                if isinstance(global_privileges, list):
                    # 处理列表格式的权限数据
                    is_superuser = "SUPER" in global_privileges
                else:
                    # 处理字典格式的权限数据
                    for perm in global_privileges:
                        if isinstance(perm, dict) and perm.get("privilege") == "SUPER" and perm.get("granted", False):
                            is_superuser = True
                            break

                accounts.append({
                    "username": full_username,
                    "permissions": permissions,
                    "is_superuser": is_superuser
                })

            self.sync_logger.info(f"获取到 {len(accounts)} 个MySQL账户")
            return accounts

        except Exception as e:
            self.sync_logger.error("获取MySQL账户失败", error=str(e))
            return []

    def get_user_permissions(self, conn, username: str) -> Dict[str, Any]:
        """获取MySQL用户权限信息"""
        try:
            # 解析用户名和主机
            if "@" in username:
                user, host = username.split("@", 1)
            else:
                user, host = username, "%"

            permissions = {
                "global_privileges": [],
                "database_privileges": {},
                "type_specific": {}
            }

            # 获取全局权限
            global_sql = """
                SELECT 
                    Select_priv, Insert_priv, Update_priv, Delete_priv, Create_priv, Drop_priv,
                    Reload_priv, Shutdown_priv, Process_priv, File_priv, Grant_priv, References_priv,
                    Index_priv, Alter_priv, Show_db_priv, Super_priv, Create_tmp_table_priv,
                    Lock_tables_priv, Execute_priv, Repl_slave_priv, Repl_client_priv,
                    Create_view_priv, Show_view_priv, Create_routine_priv, Alter_routine_priv,
                    Create_user_priv, Event_priv, Trigger_priv, Create_tablespace_priv,
                    ssl_type, ssl_cipher, x509_issuer, x509_subject,
                    max_questions, max_updates, max_connections, max_user_connections,
                    plugin, authentication_string, password_expired, password_last_changed
                FROM mysql.user 
                WHERE User = %s AND Host = %s
            """
            
            global_privs = conn.execute_query(global_sql, (user, host))
            if global_privs:
                row = global_privs[0]
                # 全局权限字段映射
                priv_fields = [
                    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
                    'RELOAD', 'SHUTDOWN', 'PROCESS', 'FILE', 'GRANT', 'REFERENCES',
                    'INDEX', 'ALTER', 'SHOW DATABASES', 'SUPER', 'CREATE TEMPORARY TABLES',
                    'LOCK TABLES', 'EXECUTE', 'REPLICATION SLAVE', 'REPLICATION CLIENT',
                    'CREATE VIEW', 'SHOW VIEW', 'CREATE ROUTINE', 'ALTER ROUTINE',
                    'CREATE USER', 'EVENT', 'TRIGGER', 'CREATE TABLESPACE'
                ]
                
                global_privileges = []
                for i, priv_field in enumerate(priv_fields):
                    if row[i] == 'Y':
                        global_privileges.append(priv_field)
                
                permissions["global_privileges"] = global_privileges
                
                # 存储type_specific信息
                permissions["type_specific"] = {
                    "ssl_type": row[28],
                    "ssl_cipher": row[29],
                    "x509_issuer": row[30],
                    "x509_subject": row[31],
                    "max_questions": row[32],
                    "max_updates": row[33],
                    "max_connections": row[34],
                    "max_user_connections": row[35],
                    "plugin": row[36],
                    "authentication_string": row[37],
                    "password_expired": bool(row[38]) if row[38] is not None else False,
                    "password_last_changed": row[39].isoformat() if row[39] else None
                }

            # 获取数据库权限
            db_sql = """
                SELECT Db,
                       Select_priv, Insert_priv, Update_priv, Delete_priv, Create_priv, Drop_priv,
                       Grant_priv, References_priv, Index_priv, Alter_priv, Create_tmp_table_priv,
                       Lock_tables_priv, Create_view_priv, Show_view_priv, Create_routine_priv,
                       Alter_routine_priv, Execute_priv, Event_priv, Trigger_priv
                FROM mysql.db 
                WHERE User = %s AND Host = %s
            """
            
            db_privs = conn.execute_query(db_sql, (user, host))
            database_privileges = {}
            
            if db_privs:
                db_priv_fields = [
                    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
                    'GRANT', 'REFERENCES', 'INDEX', 'ALTER', 'CREATE TEMPORARY TABLES',
                    'LOCK TABLES', 'CREATE VIEW', 'SHOW VIEW', 'CREATE ROUTINE',
                    'ALTER ROUTINE', 'EXECUTE', 'EVENT', 'TRIGGER'
                ]
                
                for row in db_privs:
                    db_name = row[0]
                    db_privileges = []
                    for i, priv_field in enumerate(db_priv_fields):
                        if row[i + 1] == 'Y':  # 跳过第一个字段（数据库名）
                            db_privileges.append(priv_field)
                    
                    if db_privileges:
                        database_privileges[db_name] = db_privileges
                
            permissions["database_privileges"] = database_privileges

            return permissions

        except Exception as e:
            self.sync_logger.error(f"获取MySQL用户权限失败: {username}", error=str(e))
            return {
                "global_privileges": [],
                "database_privileges": {},
                "type_specific": {}
            }

    def create_account(self, instance_id: int, username: str, permissions_data: Dict[str, Any], 
                      is_superuser: bool, session_id: str = None) -> CurrentAccountSyncData:
        """创建MySQL账户"""
        account = CurrentAccountSyncData(
            instance_id=instance_id,
            db_type="mysql",
            username=username,
            global_privileges=permissions_data.get("global_privileges", []),
            database_privileges=permissions_data.get("database_privileges", {}),
            type_specific=permissions_data.get("type_specific", {}),
            is_superuser=is_superuser,
            last_change_type="add",
            session_id=session_id,
        )
        return account

    def update_account(self, account: CurrentAccountSyncData, permissions_data: Dict[str, Any], 
                      is_superuser: bool) -> None:
        """更新MySQL账户数据"""
        account.global_privileges = permissions_data.get("global_privileges", [])
        account.database_privileges = permissions_data.get("database_privileges", {})
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.last_change_type = "modify_privilege"
        account.last_change_time = time_utils.now()
        account.last_sync_time = time_utils.now()

    def detect_changes(self, account: CurrentAccountSyncData, new_permissions: Dict[str, Any]) -> Dict[str, Any]:
        """检测MySQL权限变更"""
        changes = {}

        # 检测全局权限变更
        old_global = set(account.global_privileges or [])
        new_global = set(new_permissions.get("global_privileges", []))
        if old_global != new_global:
            changes["global_privileges"] = {
                "added": list(new_global - old_global),
                "removed": list(old_global - new_global),
            }

        # 检测数据库权限变更
        old_db_perms = account.database_privileges or {}
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
        """验证MySQL权限数据完整性"""
        if not permissions_data:
            self.sync_logger.warning(f"MySQL用户 {username} 权限数据为空")
            return False

        required_fields = ["global_privileges", "database_privileges", "type_specific"]
        missing_fields = []

        for field in required_fields:
            if field not in permissions_data:
                missing_fields.append(field)

        if missing_fields:
            self.sync_logger.warning(f"MySQL用户 {username} 权限数据缺少字段: {missing_fields}")
            return False

        # 检查数据类型
        if not isinstance(permissions_data.get("global_privileges"), list):
            self.sync_logger.warning(f"MySQL用户 {username} 全局权限应该是列表格式")
            return False

        if not isinstance(permissions_data.get("database_privileges"), dict):
            self.sync_logger.warning(f"MySQL用户 {username} 数据库权限应该是字典格式")
            return False

        if not isinstance(permissions_data.get("type_specific"), dict):
            self.sync_logger.warning(f"MySQL用户 {username} type_specific应该是字典格式")
            return False

        return True
