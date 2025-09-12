"""
泰摸鱼吧 - 账户同步服务
统一处理手动同步和定时任务的账户同步逻辑
"""

import logging

# 可选导入数据库驱动
try:
    import psycopg
except ImportError:
    psycopg = None

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    import oracledb
except ImportError:
    oracledb = None
from typing import Any

from app import db
from app.models import Instance
from app.models.account import Account
from app.services.database_filter_manager import database_filter_manager
from app.utils.enhanced_logger import log_sync_error, sync_logger
from app.utils.timezone import now


class AccountSyncService:
    """账户同步服务 - 统一处理所有账户同步逻辑"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def sync_accounts(self, instance: Instance, sync_type: str = "batch") -> dict[str, Any]:
        """
        同步账户信息 - 统一入口

        Args:
            instance: 数据库实例
            sync_type: 同步类型 ('batch' 或 'task')

        Returns:
            Dict: 同步结果
        """
        try:
            sync_logger.info(f"开始账户同步: {instance.name} ({instance.db_type})", "account_sync_service")

            # 获取数据库连接
            conn = self._get_connection(instance)
            if not conn:
                error_msg = "无法获取数据库连接"
                sync_logger.error(error_msg, "account_sync_service", f"实例: {instance.name}, 类型: {instance.db_type}")
                return {"success": False, "error": error_msg}

            # 记录同步前的账户数量
            before_count = Account.query.filter_by(instance_id=instance.id).count()
            sync_logger.info(f"同步前账户数量: {before_count}", "account_sync_service", f"实例: {instance.name}")

            # 获取同步前的账户快照
            self._get_account_snapshot(instance)

            synced_count = 0
            added_count = 0
            removed_count = 0
            modified_count = 0

            # 根据数据库类型执行同步
            sync_logger.info(f"开始同步 {instance.db_type} 数据库账户 - 实例: {instance.name}", "account_sync_service")

            if instance.db_type == "mysql":
                result = self._sync_mysql_accounts(instance, conn)
            elif instance.db_type == "postgresql":
                sync_logger.info("调用PostgreSQL账户同步函数...", "account_sync_service")
                result = self._sync_postgresql_accounts(instance, conn)
                sync_logger.info(f"PostgreSQL同步结果: {result}", "account_sync_service")
            elif instance.db_type == "sqlserver":
                result = self._sync_sqlserver_accounts(instance, conn)
            elif instance.db_type == "oracle":
                result = self._sync_oracle_accounts(instance, conn)
            else:
                error_msg = f"不支持的数据库类型: {instance.db_type}"
                sync_logger.warning(error_msg, "account_sync_service", f"实例: {instance.name}")
                return {
                    "success": False,
                    "error": error_msg,
                }

            synced_count = result["synced_count"]
            added_count = result["added_count"]
            removed_count = result["removed_count"]
            modified_count = result["modified_count"]

            # 计算变化
            after_count = Account.query.filter_by(instance_id=instance.id).count()
            net_change = after_count - before_count

            # 创建同步报告记录（定时任务跳过单个实例记录，只创建聚合记录）
            if sync_type != "task":
                from app import db
                from app.models.sync_data import SyncData

                sync_record = SyncData(
                    sync_type=sync_type,  # 手动同步或任务同步
                    instance_id=instance.id,
                    task_id=None,
                    data={
                        "before_count": before_count,
                        "after_count": after_count,
                        "net_change": net_change,
                        "db_type": instance.db_type,
                        "instance_name": instance.name,
                    },
                    status="success",
                    message=f"成功同步 {synced_count} 个{instance.db_type.upper()}账户",
                    synced_count=synced_count,
                    added_count=added_count,
                    removed_count=removed_count,
                    modified_count=modified_count,
                    records_count=synced_count,
                )
                db.session.add(sync_record)
                db.session.commit()

            return {
                "success": True,
                "message": f"成功同步 {synced_count} 个{instance.db_type.upper()}账户",
                "synced_count": synced_count,
                "added_count": added_count,
                "removed_count": removed_count,
                "modified_count": modified_count,
                "net_change": net_change,
            }

        except Exception as e:
            # 记录详细的错误日志
            log_sync_error(
                "账户同步",
                e,
                "account_sync_service",
                f"实例: {instance.name}, 类型: {instance.db_type}, 同步类型: {sync_type}",
            )

            # 创建失败的同步报告记录（定时任务跳过单个实例记录，只创建聚合记录）
            if sync_type != "task":
                from app import db
                from app.models.sync_data import SyncData

                sync_record = SyncData(
                    sync_type=sync_type,  # 手动同步或任务同步
                    instance_id=instance.id,
                    task_id=None,
                    data={
                        "db_type": instance.db_type,
                        "instance_name": instance.name,
                        "error": str(e),
                    },
                    status="failed",
                    message=f"{instance.db_type.upper()}账户同步失败: {str(e)}",
                    synced_count=0,
                    added_count=0,
                    removed_count=0,
                    modified_count=0,
                    error_message=str(e),
                    records_count=0,
                )
                db.session.add(sync_record)
                db.session.commit()

            return {
                "success": False,
                "error": f"{instance.db_type.upper()}账户同步失败: {str(e)}",
                "synced_count": 0,
            }

    def _get_connection(self, instance: Instance):
        """获取数据库连接 - 使用统一的连接工厂"""
        try:
            # 使用统一的连接工厂创建连接
            from app.services.connection_factory import ConnectionFactory

            connection_obj = ConnectionFactory.create_connection(instance)

            if not connection_obj:
                self.logger.error(f"不支持的数据库类型: {instance.db_type}")
                return None

            # 建立连接
            if connection_obj.connect():
                return connection_obj.connection
            self.logger.error(f"无法建立{instance.db_type}连接")
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
            "SQL Server Native Client 11.0",
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
                "server": instance.host,
                "port": instance.port,
                "database": instance.database_name or "master",
                "user": instance.credential.username,
                "password": instance.credential.get_plain_password(),
            }
        except ImportError:
            return None

    def _get_account_snapshot(self, instance: Instance) -> dict[str, dict]:
        """获取同步前的账户快照"""
        before_accounts = {}
        existing_accounts = Account.query.filter_by(instance_id=instance.id).all()
        for account in existing_accounts:
            key = f"{account.username}@{account.host}"
            before_accounts[key] = {
                "id": account.id,
                "username": account.username,
                "host": account.host,
                "database_name": account.database_name,
                "account_type": account.account_type,
                "plugin": account.plugin,
                "password_expired": account.password_expired,
                "password_last_changed": (
                    account.password_last_changed.isoformat() if account.password_last_changed else None
                ),
                "is_locked": account.is_locked,
                "is_active": account.is_active,
                "last_login": (account.last_login.isoformat() if account.last_login else None),
            }
        return before_accounts

    def _sync_mysql_accounts(self, instance: Instance, conn) -> dict[str, int]:
        """同步MySQL账户"""
        cursor = conn.cursor()

        # 获取MySQL过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions("mysql", "User")

        # 查询用户信息 - 包含完整的账户信息
        cursor.execute(
            f"""
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
            WHERE {filter_conditions}
            ORDER BY User, Host
        """
        )

        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        removed_count = 0
        modified_count = 0

        for account_data in accounts:
            (
                username,
                host,
                account_type,
                database_name,
                plugin,
                password_expired,
                password_last_changed,
                account_locked,
                password_lifetime,
                can_select,
                can_insert,
                can_update,
                can_delete,
                can_create,
                can_drop,
                is_superuser,
            ) = account_data

            # 查找或创建账户记录
            account = Account.query.filter_by(instance_id=instance.id, username=username, host=host).first()

            # 处理插件信息
            plugin_name = plugin if plugin else "mysql_native_password"

            # 处理密码过期状态
            is_password_expired = password_expired == "Y" if password_expired else False

            # 处理锁定状态
            is_locked = account_locked == "Y" if account_locked else False

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
                    permissions=permissions_info["permissions_json"],
                    is_superuser=permissions_info["is_superuser"],
                    can_grant=permissions_info["can_grant"],
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
                if account.permissions != permissions_info["permissions_json"]:
                    account.permissions = permissions_info["permissions_json"]
                    has_changes = True
                if account.is_superuser != permissions_info["is_superuser"]:
                    account.is_superuser = permissions_info["is_superuser"]
                    has_changes = True
                if account.can_grant != permissions_info["can_grant"]:
                    account.can_grant = permissions_info["can_grant"]
                    has_changes = True

                if has_changes:
                    account.updated_at = now()
                    modified_count += 1

            synced_count += 1

        # 删除服务器端不存在的本地账户
        server_accounts = set()
        for account_data in accounts:
            (
                username,
                host,
                account_type,
                database_name,
                plugin_name,
                password_expired,
                password_last_changed,
                account_locked,
                password_lifetime,
                can_select,
                can_insert,
                can_update,
                can_delete,
                can_create,
                can_drop,
                is_superuser,
            ) = account_data
            server_accounts.add((username, host))

        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []

        for local_account in local_accounts:
            if (local_account.username, local_account.host) not in server_accounts:
                removed_accounts.append(
                    {
                        "username": local_account.username,
                        "host": local_account.host,
                        "database_name": local_account.database_name,
                        "account_type": local_account.account_type,
                        "plugin": local_account.plugin,
                        "password_expired": local_account.password_expired,
                        "password_last_changed": (
                            local_account.password_last_changed.isoformat()
                            if local_account.password_last_changed
                            else None
                        ),
                        "is_locked": local_account.is_locked,
                        "is_active": local_account.is_active,
                    }
                )
                db.session.delete(local_account)
                removed_count += 1

        db.session.commit()
        cursor.close()

        return {
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": modified_count,
            "removed_accounts": removed_accounts,
        }

    def _sync_postgresql_accounts(self, instance: Instance, conn) -> dict[str, int]:
        """同步PostgreSQL账户"""
        cursor = conn.cursor()

        # 获取PostgreSQL过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions("postgresql", "rolname")

        # 查询角色信息（PostgreSQL中用户和角色是同一个概念）
        cursor.execute(
            f"""
            SELECT
                    rolname as username,
                    rolsuper as is_superuser,
                    rolinherit as can_inherit,
                    rolcreaterole as can_create_role,
                    rolcreatedb as can_create_db,
                    rolcanlogin as can_login,
                    rolconnlimit as conn_limit,
                    CASE
                        WHEN rolvaliduntil = 'infinity'::timestamp THEN NULL
                        ELSE rolvaliduntil
                    END as valid_until,
                    rolbypassrls as can_bypass_rls,
                    rolreplication as can_replicate
                FROM pg_roles
                WHERE {filter_conditions}
                ORDER BY rolname
            """
        )

        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        modified_count = 0
        removed_count = 0

        # 记录服务器端的账户
        server_accounts = set()

        for account_data in accounts:
            (
                username,
                is_superuser,
                can_inherit,
                can_create_role,
                can_create_db,
                can_login,
                conn_limit,
                valid_until,
                can_bypass_rls,
                can_replicate,
            ) = account_data

            # 记录服务器端的账户（PostgreSQL没有主机概念）
            server_accounts.add((username, ""))

            # PostgreSQL认证类型默认为scram-sha-256（定义在本地配置文件中）
            account_type = "scram-sha-256"

            # 检查密码是否过期
            # 处理PostgreSQL的'infinity'时间戳值
            password_expired = False
            if valid_until is not None:
                try:
                    # 检查是否为'infinity'字符串
                    if str(valid_until).lower() == "infinity":
                        password_expired = False
                    else:
                        password_expired = valid_until < now()
                except (ValueError, TypeError, OverflowError):
                    # 如果时间戳无法解析或超出范围，认为密码未过期
                    password_expired = False

            # 检查账户是否被锁定
            is_locked = not can_login

            # 检查账户是否活跃
            is_active = can_login and not password_expired

            # 查找或创建账户记录
            account = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host="",  # PostgreSQL没有主机概念
            ).first()

            if not account:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host="",  # PostgreSQL没有主机概念
                    database_name="postgres",  # PostgreSQL默认数据库
                    account_type=account_type,
                    is_superuser=is_superuser,
                    is_active=is_active,
                    is_locked=is_locked,
                    password_expired=password_expired,
                    created_at=now(),
                    updated_at=now(),
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
                    account.is_superuser = permissions.get("is_superuser", False)
                    account.can_grant = permissions.get("can_grant", False)
                    # 标记有权限更新
                    changes = True
                    self.logger.info(f"PostgreSQL账户 {username} 权限已更新: {permissions}")
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
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": modified_count,
        }

    def _get_postgresql_account_permissions(self, instance: Instance, conn, username: str) -> dict[str, Any]:
        """获取PostgreSQL账户权限 - 根据新的权限配置结构"""

        cursor = conn.cursor()
        permissions = {
            "predefined_roles": [],
            "role_attributes": [],
            "database_privileges": [],
            "tablespace_privileges": [],
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
                cursor.execute(
                    """
                    SELECT r.rolname
                    FROM pg_roles r
                    JOIN pg_auth_members m ON r.oid = m.roleid
                    JOIN pg_roles u ON m.member = u.oid
                    WHERE u.rolname = %s
                    AND r.rolname LIKE %s
                    ORDER BY r.rolname
                """,
                    (username, "pg_%"),
                )

                predefined_roles = cursor.fetchall()
                if predefined_roles:
                    for role in predefined_roles:
                        if role and len(role) > 0:
                            permissions["predefined_roles"].append(role[0])
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 预定义角色失败: {e}")

            # 获取角色属性
            try:
                cursor.execute(
                    """
                    SELECT
                        rolsuper, rolcreatedb, rolcreaterole, rolinherit,
                        rolcanlogin, rolreplication, rolbypassrls
                    FROM pg_roles
                    WHERE rolname = %s
                """,
                    (username,),
                )

                role_attrs = cursor.fetchone()
                if role_attrs:
                    (
                        is_super,
                        can_create_db,
                        can_create_role,
                        can_inherit,
                        can_login,
                        can_replicate,
                        can_bypass_rls,
                    ) = role_attrs

                    if is_super:
                        permissions["role_attributes"].append("SUPERUSER")
                    if can_create_db:
                        permissions["role_attributes"].append("CREATEDB")
                    if can_create_role:
                        permissions["role_attributes"].append("CREATEROLE")
                    if can_inherit:
                        permissions["role_attributes"].append("INHERIT")
                    if can_login:
                        permissions["role_attributes"].append("LOGIN")
                    if can_replicate:
                        permissions["role_attributes"].append("REPLICATION")
                    if can_bypass_rls:
                        permissions["role_attributes"].append("BYPASSRLS")
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 角色属性失败: {e}")

            # 获取数据库权限（多数据库版本）
            try:
                # 获取所有数据库列表
                cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
                databases = [row[0] for row in cursor.fetchall()]

                self.logger.info(f"PostgreSQL用户 {username} 权限查询使用默认数据库: postgres")

                # 为每个数据库查询权限
                for db_name in databases:
                    try:
                        cursor.execute(
                            """
                            SELECT
                                CASE WHEN has_database_privilege(%s, %s, 'CONNECT') THEN 'CONNECT' END,
                                CASE WHEN has_database_privilege(%s, %s, 'CREATE') THEN 'CREATE' END,
                                CASE WHEN has_database_privilege(%s, %s, 'TEMPORARY') THEN 'TEMPORARY' END
                            """,
                            (username, db_name, username, db_name, username, db_name),
                        )

                        row = cursor.fetchone()
                        if row:
                            connect, create, temp = row
                            db_privileges = []
                            if connect:
                                db_privileges.append("CONNECT")
                            if create:
                                db_privileges.append("CREATE")
                            if temp:
                                db_privileges.append("TEMPORARY")

                            if db_privileges:
                                permissions["database_privileges"].append(
                                    {"database": db_name, "privileges": db_privileges}
                                )
                    except Exception as db_error:
                        self.logger.debug(f"查询数据库 {db_name} 的权限失败: {db_error}")
                        continue

            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 数据库权限失败: {e}")

            # 获取表空间权限
            try:
                cursor.execute(
                    """
                    SELECT
                        CASE WHEN has_tablespace_privilege(%s, 'pg_default', 'CREATE') THEN 'CREATE' END
                """,
                    (username,),
                )

                row = cursor.fetchone()
                if row:
                    create = row[0]
                    if create:
                        permissions["tablespace_privileges"].append("CREATE")
            except Exception as e:
                self.logger.warning(f"获取PostgreSQL用户 {username} 表空间权限失败: {e}")

            # 确定是否为超级用户和是否可以授权
            is_superuser = "SUPERUSER" in permissions["role_attributes"]
            can_grant = is_superuser or "CREATEROLE" in permissions["role_attributes"]

            permissions["is_superuser"] = is_superuser
            permissions["can_grant"] = can_grant

            self.logger.info(f"PostgreSQL用户 {username} 权限获取成功: {permissions}")

        except Exception as e:
            self.logger.error(f"获取PostgreSQL账户 {username} 权限失败: {e}")
            # 返回基本权限结构而不是空字典
            permissions["is_superuser"] = False
            permissions["can_grant"] = False
        finally:
            cursor.close()

        return permissions

    def _sync_sqlserver_accounts(self, instance: Instance, conn) -> dict[str, int]:
        """同步SQL Server账户"""
        cursor = conn.cursor()

        # 获取SQL Server过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions("sqlserver", "name")

        # 查询用户信息 - 只同步sa和用户创建的账户，排除内置账户
        cursor.execute(
            f"""
            SELECT
                name as username,
                type_desc as account_type,
                'master' as database_name,
                is_disabled as is_disabled,
                create_date as created_date,
                modify_date as modified_date
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G')
            AND {filter_conditions}
            AND (name = 'sa' OR name NOT LIKE 'NT %')
            ORDER BY name
        """
        )

        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        removed_count = 0
        modified_count = 0

        for account_data in accounts:
            (
                username,
                account_type,
                database_name,
                is_disabled,
                created_date,
                modified_date,
            ) = account_data

            # 直接使用SQL Server的原始type_desc名称
            account_type = account_type.lower()

            # 获取权限信息
            permissions_info = self._get_sqlserver_account_permissions(conn, username)

            # 查找或创建账户记录
            account = Account.query.filter_by(instance_id=instance.id, username=username).first()

            if not account:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    database_name=database_name,
                    account_type=account_type,
                    is_active=not is_disabled,
                    permissions=permissions_info["permissions_json"],
                    is_superuser=permissions_info["is_superuser"],
                    can_grant=permissions_info["can_grant"],
                    account_created_at=created_date,
                    password_last_changed=modified_date,
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
                if account.account_created_at != created_date:
                    account.account_created_at = created_date
                    has_changes = True
                if account.password_last_changed != modified_date:
                    account.password_last_changed = modified_date
                    has_changes = True

                # 更新权限信息
                if account.permissions != permissions_info["permissions_json"]:
                    account.permissions = permissions_info["permissions_json"]
                    has_changes = True
                if account.is_superuser != permissions_info["is_superuser"]:
                    account.is_superuser = permissions_info["is_superuser"]
                    has_changes = True
                if account.can_grant != permissions_info["can_grant"]:
                    account.can_grant = permissions_info["can_grant"]
                    has_changes = True

                if has_changes:
                    account.updated_at = now()
                    modified_count += 1

            synced_count += 1

        # 删除服务器端不存在的本地账户
        server_accounts = set()
        for account_data in accounts:
            (
                username,
                account_type,
                database_name,
                is_disabled,
                created_date,
                modified_date,
            ) = account_data
            server_accounts.add(username)

        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []

        for local_account in local_accounts:
            if local_account.username not in server_accounts:
                removed_accounts.append(
                    {
                        "username": local_account.username,
                        "host": local_account.host,
                        "database_name": local_account.database_name,
                        "account_type": local_account.account_type,
                        "plugin": local_account.plugin,
                        "password_expired": local_account.password_expired,
                        "password_last_changed": (
                            local_account.password_last_changed.isoformat()
                            if local_account.password_last_changed
                            else None
                        ),
                        "is_locked": local_account.is_locked,
                        "is_active": local_account.is_active,
                    }
                )
                db.session.delete(local_account)
                removed_count += 1

        db.session.commit()
        cursor.close()

        return {
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": modified_count,
            "removed_accounts": removed_accounts,
        }

    def _sync_oracle_accounts(self, instance: Instance, conn) -> dict[str, int]:
        """同步Oracle账户"""
        print("DEBUG: 开始Oracle账户同步 - 函数被调用")
        cursor = conn.cursor()

        # 获取Oracle过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions("oracle", "username")

        # 查询用户信息
        cursor.execute(
            f"""
            SELECT
                username,
                authentication_type as account_type,
                '' as database_name,
                account_status,
                created,
                expiry_date,
                profile
            FROM dba_users
            WHERE {filter_conditions}
            ORDER BY username
        """
        )

        accounts = cursor.fetchall()
        synced_count = 0
        added_count = 0
        modified_count = 0
        removed_count = 0

        # 记录服务器端的账户
        server_accounts = set()

        for account_data in accounts:
            (
                username,
                account_type,
                database_name,
                account_status,
                created,
                expiry_date,
                profile,
            ) = account_data

            # 记录服务器端的账户
            server_accounts.add(username)

            # 获取权限信息
            permissions_info = self._get_oracle_account_permissions(conn, username)

            # 查找或创建账户记录
            account = Account.query.filter_by(instance_id=instance.id, username=username).first()

            if not account:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    database_name=database_name,
                    account_type=account_type,
                    is_active=account_status == "OPEN",
                    permissions=permissions_info["permissions_json"],
                    is_superuser=permissions_info["is_superuser"],
                    can_grant=permissions_info["can_grant"],
                )
                db.session.add(account)
                added_count += 1
            else:
                # 检查是否有变化
                is_active = account_status == "OPEN"
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
                if account.permissions != permissions_info["permissions_json"]:
                    account.permissions = permissions_info["permissions_json"]
                    has_changes = True
                if account.is_superuser != permissions_info["is_superuser"]:
                    account.is_superuser = permissions_info["is_superuser"]
                    has_changes = True
                if account.can_grant != permissions_info["can_grant"]:
                    account.can_grant = permissions_info["can_grant"]
                    has_changes = True

                if has_changes:
                    account.updated_at = now()
                    modified_count += 1

            synced_count += 1

        # 删除服务器端不存在的本地账户
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []

        print(f"DEBUG: Oracle账户清理 - 服务器端账户: {server_accounts}")
        print(f"DEBUG: Oracle账户清理 - 本地账户数量: {len(local_accounts)}")
        self.logger.info(f"Oracle账户清理 - 服务器端账户: {server_accounts}")
        self.logger.info(f"Oracle账户清理 - 本地账户数量: {len(local_accounts)}")

        for local_account in local_accounts:
            if local_account.username not in server_accounts:
                print(f"DEBUG: Oracle账户清理 - 删除账户: {local_account.username}")
                self.logger.info(f"Oracle账户清理 - 删除账户: {local_account.username}")
                removed_accounts.append(
                    {
                        "username": local_account.username,
                        "host": local_account.host,
                        "database_name": local_account.database_name,
                        "account_type": local_account.account_type,
                        "plugin": local_account.plugin,
                        "password_expired": local_account.password_expired,
                        "password_last_changed": (
                            local_account.password_last_changed.isoformat()
                            if local_account.password_last_changed
                            else None
                        ),
                        "is_locked": local_account.is_locked,
                        "is_active": local_account.is_active,
                    }
                )
                db.session.delete(local_account)
                removed_count += 1

        db.session.commit()
        cursor.close()

        return {
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": modified_count,
            "removed_accounts": removed_accounts,
        }

    def _get_mysql_account_permissions(self, conn, username: str, host: str) -> dict[str, Any]:
        """获取MySQL账户权限信息"""
        import json

        cursor = conn.cursor()

        try:
            # 获取全局权限 - 使用mysql.user表获取更完整的权限信息
            cursor.execute(
                """
                SELECT
                    User, Host, Select_priv, Insert_priv, Update_priv, Delete_priv,
                    Create_priv, Drop_priv, Reload_priv, Shutdown_priv, Process_priv,
                    File_priv, Grant_priv, References_priv, Index_priv, Alter_priv,
                    Show_db_priv, Super_priv, Create_tmp_table_priv, Lock_tables_priv,
                    Execute_priv, Repl_slave_priv, Repl_client_priv, Create_view_priv,
                    Show_view_priv, Create_routine_priv, Alter_routine_priv, Create_user_priv,
                    Event_priv, Trigger_priv, Create_tablespace_priv
                FROM mysql.user
                WHERE User = %s AND Host = %s
            """,
                (username, host),
            )

            global_permissions = []
            can_grant = False
            is_superuser = False

            user_row = cursor.fetchone()
            if user_row:
                # 定义权限映射
                privilege_map = {
                    "Select_priv": "SELECT",
                    "Insert_priv": "INSERT",
                    "Update_priv": "UPDATE",
                    "Delete_priv": "DELETE",
                    "Create_priv": "CREATE",
                    "Drop_priv": "DROP",
                    "Reload_priv": "RELOAD",
                    "Shutdown_priv": "SHUTDOWN",
                    "Process_priv": "PROCESS",
                    "File_priv": "FILE",
                    "Grant_priv": "GRANT OPTION",
                    "References_priv": "REFERENCES",
                    "Index_priv": "INDEX",
                    "Alter_priv": "ALTER",
                    "Show_db_priv": "SHOW DATABASES",
                    "Super_priv": "SUPER",
                    "Create_tmp_table_priv": "CREATE TEMPORARY TABLES",
                    "Lock_tables_priv": "LOCK TABLES",
                    "Execute_priv": "EXECUTE",
                    "Repl_slave_priv": "REPLICATION SLAVE",
                    "Repl_client_priv": "REPLICATION CLIENT",
                    "Create_view_priv": "CREATE VIEW",
                    "Show_view_priv": "SHOW VIEW",
                    "Create_routine_priv": "CREATE ROUTINE",
                    "Alter_routine_priv": "ALTER ROUTINE",
                    "Create_user_priv": "CREATE USER",
                    "Event_priv": "EVENT",
                    "Trigger_priv": "TRIGGER",
                    "Create_tablespace_priv": "CREATE TABLESPACE",
                }

                # 检查每个权限
                for i, (field_name, privilege_name) in enumerate(privilege_map.items()):
                    if i + 2 < len(user_row) and user_row[i + 2] == "Y":  # +2 因为前两个字段是User和Host
                        global_permissions.append({"privilege": privilege_name, "granted": True, "grantable": False})

                        if privilege_name == "SUPER":
                            is_superuser = True
                        if privilege_name == "GRANT OPTION":
                            can_grant = True

            # 获取数据库权限
            cursor.execute(
                """
                SELECT TABLE_SCHEMA, PRIVILEGE_TYPE
                FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES
                WHERE GRANTEE = %s
                ORDER BY TABLE_SCHEMA, PRIVILEGE_TYPE
            """,
                (f"'{username}'@'{host}'",),
            )

            db_permissions = {}
            for row in cursor.fetchall():
                schema, privilege = row
                if schema not in db_permissions:
                    db_permissions[schema] = []
                db_permissions[schema].append(privilege)

            # 转换为前端需要的格式
            database_permissions = []
            for schema, privileges in db_permissions.items():
                database_permissions.append({"database": schema, "privileges": privileges})

            permissions_data = {
                "global_privileges": global_permissions,
                "database_privileges": database_permissions,
            }

            return {
                "permissions_json": json.dumps(permissions_data),
                "is_superuser": is_superuser,
                "can_grant": can_grant,
            }

        except Exception as e:
            self.logger.error(f"获取MySQL权限失败: {e}")
            return {
                "permissions_json": json.dumps({"global_privileges": [], "database_privileges": []}),
                "is_superuser": False,
                "can_grant": False,
            }
        finally:
            cursor.close()

    def _get_sqlserver_account_permissions(self, conn, username: str) -> dict[str, Any]:
        """获取SQL Server账户权限信息"""
        import json

        cursor = conn.cursor()

        try:
            # 获取服务器角色
            cursor.execute(
                """
                SELECT r.name as role_name
                FROM sys.server_role_members rm
                JOIN sys.server_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.server_principals p ON rm.member_principal_id = p.principal_id
                WHERE p.name = %s
            """,
                (username,),
            )

            server_roles = []
            is_sysadmin = False
            for row in cursor.fetchall():
                role_name = row[0]
                server_roles.append({"role": role_name, "granted": True})
                if role_name == "sysadmin":
                    is_sysadmin = True

            # 获取服务器权限
            cursor.execute(
                """
                SELECT p.permission_name, p.state_desc
                FROM sys.server_permissions p
                JOIN sys.server_principals sp ON p.grantee_principal_id = sp.principal_id
                WHERE sp.name = %s
            """,
                (username,),
            )

            server_permissions = []
            for row in cursor.fetchall():
                permission, state = row
                server_permissions.append({"permission": permission, "granted": state == "GRANT"})

            # 获取数据库角色和权限
            database_roles = []
            database_permissions = []

            # 获取所有数据库的角色
            try:
                # 首先获取所有数据库列表
                cursor.execute("SELECT name FROM sys.databases WHERE state = 0")
                databases = [row[0] for row in cursor.fetchall()]

                db_roles = {}

                # 遍历每个数据库查询角色
                for db_name in databases:
                    try:
                        # 切换到目标数据库
                        cursor.execute(f"USE [{db_name}]")

                        # 查询该数据库的角色
                        cursor.execute(
                            """
                            SELECT r.name as role_name
                            FROM sys.database_role_members rm
                            JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
                            JOIN sys.database_principals p ON rm.member_principal_id = p.principal_id
                            WHERE p.name = %s
                            """,
                            (username,),
                        )

                        roles = cursor.fetchall()
                        if roles:
                            db_roles[db_name] = [row[0] for row in roles]

                    except Exception as db_error:
                        # 如果某个数据库查询失败，记录日志但继续处理其他数据库
                        self.logger.debug(f"查询数据库 {db_name} 的角色失败: {db_error}")
                        continue

                # 转换格式
                for db_name, roles in db_roles.items():
                    database_roles.append({"database": db_name, "roles": roles})

            except Exception as e:
                self.logger.debug(f"获取数据库角色失败: {e}")

            # 获取数据库权限
            try:
                db_permissions = {}

                # 遍历每个数据库查询权限
                for db_name in databases:
                    try:
                        # 切换到目标数据库
                        cursor.execute(f"USE [{db_name}]")

                        # 查询该数据库的权限
                        cursor.execute(
                            """
                            SELECT
                                p.permission_name,
                                p.state_desc
                            FROM sys.database_permissions p
                            JOIN sys.database_principals dp ON p.grantee_principal_id = dp.principal_id
                            WHERE dp.name = %s
                            """,
                            (username,),
                        )

                        permissions = cursor.fetchall()
                        if permissions:
                            db_permissions[db_name] = []
                            for perm_row in permissions:
                                perm_name, state = perm_row
                                db_permissions[db_name].append({"permission": perm_name, "granted": state == "GRANT"})

                    except Exception as db_error:
                        # 如果某个数据库查询失败，记录日志但继续处理其他数据库
                        self.logger.debug(f"查询数据库 {db_name} 的权限失败: {db_error}")
                        continue

                # 转换格式
                for db_name, perms in db_permissions.items():
                    database_permissions.append({"database": db_name, "permissions": perms})

            except Exception as e:
                self.logger.debug(f"获取数据库权限失败: {e}")

            # 转换数据格式以匹配前端期望的格式
            server_roles_list = [role["role"] for role in server_roles]
            server_permissions_list = [perm["permission"] for perm in server_permissions]

            # 转换数据库角色格式
            database_roles_dict = {}
            for db_role in database_roles:
                db_name = db_role["database"]
                roles = db_role["roles"]
                database_roles_dict[db_name] = roles

            # 转换数据库权限格式
            database_privileges_dict = {}
            for db_perm in database_permissions:
                db_name = db_perm["database"]
                permissions = db_perm["permissions"]
                database_privileges_dict[db_name] = [perm["permission"] for perm in permissions if perm["granted"]]

            permissions_data = {
                "server_roles": server_roles_list,
                "server_permissions": server_permissions_list,
                "database_roles": database_roles_dict,
                "database_privileges": database_privileges_dict,
            }

            return {
                "permissions_json": json.dumps(permissions_data),
                "is_superuser": is_sysadmin,
                "can_grant": is_sysadmin,  # sysadmin角色可以授权
            }

        except Exception as e:
            self.logger.error(f"获取SQL Server权限失败: {e}")
            return {
                "permissions_json": json.dumps(
                    {
                        "server_roles": [],
                        "server_permissions": [],
                        "database_roles": [],
                        "database": [],
                    }
                ),
                "is_superuser": False,
                "can_grant": False,
            }
        finally:
            cursor.close()

    def _get_oracle_account_permissions(self, conn, username: str) -> dict[str, Any]:
        """获取Oracle账户权限信息 - 使用统一的权限查询工厂"""
        import json

        try:
            # 使用统一的权限查询工厂
            from app.models.account import Account

            # 创建临时账户对象用于权限查询
            temp_account = Account()
            temp_account.username = username
            temp_account.instance_id = None  # 这里不需要实例ID，因为我们直接使用连接

            # 直接使用连接查询权限，不使用权限查询工厂
            cursor = conn.cursor()
            permissions = {
                "roles": [],
                "system_privileges": [],
                "tablespace_privileges": [],
                "tablespace_quotas": [],
            }

            try:
                # 查询系统权限
                cursor.execute(
                    """
                    SELECT privilege, admin_option
                    FROM dba_sys_privs
                    WHERE grantee = :username
                    ORDER BY privilege
                """,
                    {"username": username.upper()},
                )

                for row in cursor.fetchall():
                    privilege, admin_option = row
                    permissions["system_privileges"].append(privilege)

                # 查询角色权限
                cursor.execute(
                    """
                    SELECT granted_role, admin_option
                    FROM dba_role_privs
                    WHERE grantee = :username
                    ORDER BY granted_role
                """,
                    {"username": username.upper()},
                )

                for row in cursor.fetchall():
                    role, admin_option = row
                    permissions["roles"].append(role)

                # 查询表空间配额（使用user_ts_quotas，因为当前连接用户是SYS）
                try:
                    cursor.execute(
                        """
                        SELECT tablespace_name, bytes, max_bytes
                        FROM user_ts_quotas
                        ORDER BY tablespace_name
                    """
                    )

                    for row in cursor.fetchall():
                        tablespace_name = row[0]
                        current_bytes = row[1] if row[1] else 0
                        max_bytes = row[2] if row[2] else 0

                        if max_bytes > 0:
                            quota_info = f"{tablespace_name}: {current_bytes}/{max_bytes} bytes"
                        else:
                            quota_info = f"{tablespace_name}: {current_bytes}/UNLIMITED"

                        permissions["tablespace_quotas"].append(quota_info)
                except Exception as e:
                    print(f"DEBUG: 表空间配额查询失败: {e}")

                # 确定是否为超级用户和是否可以授权
                is_superuser = any(role in ["DBA", "SYSDBA", "SYSOPER"] for role in permissions["roles"])
                can_grant = is_superuser or any(
                    priv in ["GRANT ANY PRIVILEGE", "GRANT ANY ROLE"] for priv in permissions["system_privileges"]
                )

                return {
                    "permissions_json": json.dumps(permissions),
                    "is_superuser": is_superuser,
                    "can_grant": can_grant,
                }

            finally:
                cursor.close()

        except Exception as e:
            self.logger.error(f"获取Oracle权限失败: {e}")
            return {
                "permissions_json": json.dumps(
                    {
                        "roles": [],
                        "system_privileges": [],
                        "tablespace_privileges": [],
                        "tablespace_quotas": [],
                    }
                ),
                "is_superuser": False,
                "can_grant": False,
            }


# 全局实例
account_sync_service = AccountSyncService()
