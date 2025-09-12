"""
泰摸鱼吧 - 数据库连接管理服务
"""

import logging
from typing import Dict, Any, Optional, List
from app.models import Instance, Credential
from app.models.account import Account
from app import db
from app.utils.enhanced_logger import log_operation, log_error
from app.utils.enhanced_logger import db_logger, log_database_error, log_database_operation
from app.services.database_filter_manager import database_filter_manager
from app.utils.database_type_utils import DatabaseTypeUtils
from app.services.connection_factory import ConnectionFactory
from app.services.permission_query_factory import PermissionQueryFactory


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
            db_logger.info(f"开始测试数据库连接: {instance.name} ({instance.db_type})", "database_service")
            
            # 使用连接工厂测试连接
            result = ConnectionFactory.test_connection(instance)
            
            if result.get("success"):
                db_logger.info(f"数据库连接测试成功: {instance.name}", "database_service")
                # 更新最后连接时间
                from app.utils.timezone import now
                instance.last_connected = now()
                db.session.commit()
            else:
                db_logger.warning(f"数据库连接测试失败: {instance.name} - {result.get('error')}", "database_service")
            
            return result
            
        except Exception as e:
            error_msg = f"连接测试失败: {str(e)}"
            log_database_error("test_connection", e, "database_service", 
                             f"实例: {instance.name}, 类型: {instance.db_type}")
            return {"success": False, "error": error_msg}

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
            from app.models.account_change import AccountChange
            from app import db

            # 获取数据库连接
            conn = self.get_connection(instance)
            if not conn:
                return {"success": False, "error": "无法获取数据库连接"}

            # 获取数据库版本信息
            version_info = self.get_database_version(instance, conn)
            if version_info and version_info != instance.database_version:
                instance.database_version = version_info
                db.session.commit()

            # 记录同步前的账户数量
            before_count = Account.query.filter_by(instance_id=instance.id).count()

            # 获取同步前的账户快照
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
                        account.password_last_changed.isoformat()
                        if account.password_last_changed
                        else None
                    ),
                    "is_locked": account.is_locked,
                    "is_active": account.is_active,
                    "last_login": (
                        account.last_login.isoformat() if account.last_login else None
                    ),
                }

            synced_count = 0
            added_count = 0
            removed_count = 0
            modified_count = 0

            if instance.db_type == "mysql":
                result = self._sync_mysql_accounts(instance, conn)
                synced_count = result["synced_count"]
                added_count = result["added_count"]
                removed_count = result["removed_count"]
                modified_count = result["modified_count"]
            elif instance.db_type == "postgresql":
                result = self._sync_postgresql_accounts(instance, conn)
                synced_count = result["synced_count"]
                added_count = result["added_count"]
                removed_count = result["removed_count"]
                modified_count = result["modified_count"]
            elif instance.db_type == "sqlserver":
                result = self._sync_sqlserver_accounts(instance, conn)
                synced_count = result["synced_count"]
                added_count = result["added_count"]
                removed_count = result["removed_count"]
                modified_count = result["modified_count"]
            elif instance.db_type == "oracle":
                result = self._sync_oracle_accounts(instance, conn)
                synced_count = result["synced_count"]
                added_count = result["added_count"]
                removed_count = result["removed_count"]
                modified_count = result["modified_count"]
            else:
                return {
                    "success": False,
                    "error": f"不支持的数据库类型: {instance.db_type}",
                }

            # 记录同步后的账户数量
            after_count = Account.query.filter_by(instance_id=instance.id).count()

            # 计算变化（简化计算）
            net_change = after_count - before_count
            total_operations = synced_count

            # 创建同步报告记录
            from app.models.sync_data import SyncData

            sync_record = SyncData(
                sync_type="manual",  # 手动同步
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
                message=f"成功同步 {total_operations} 个账户",
                synced_count=total_operations,
                added_count=added_count,
                removed_count=removed_count,
                modified_count=modified_count,
                records_count=total_operations,
            )
            db.session.add(sync_record)
            db.session.commit()

            return {
                "success": True,
                "message": f"账户同步完成，共同步 {total_operations} 个账户，净变化: {net_change:+d}",
                "synced_count": total_operations,
                "added_count": added_count,
                "removed_count": removed_count,
                "modified_count": modified_count,
                "details": {
                    "added": max(0, net_change) if net_change > 0 else 0,
                    "updated": total_operations - abs(net_change),
                    "deleted": max(0, -net_change) if net_change < 0 else 0,
                    "before_count": before_count,
                    "after_count": after_count,
                    "net_change": net_change,
                },
            }
        except Exception as e:
            # 创建失败的同步报告记录
            from app.models.sync_data import SyncData

            sync_record = SyncData(
                sync_type="manual",  # 手动同步
                instance_id=instance.id,
                task_id=None,
                data={
                    "db_type": instance.db_type,
                    "instance_name": instance.name,
                    "error": str(e),
                },
                status="failed",
                message=f"账户同步失败: {str(e)}",
                synced_count=0,
                added_count=0,
                removed_count=0,
                modified_count=0,
                error_message=str(e),
                records_count=0,
            )
            db.session.add(sync_record)
            db.session.commit()

            return {"success": False, "error": f"账户同步失败: {str(e)}"}

    def _sync_mysql_accounts(self, instance: Instance, conn) -> Dict[str, Any]:
        """同步MySQL账户"""
        cursor = conn.cursor()
        
        # 获取MySQL过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions('mysql', 'User')
        
        cursor.execute(
            f"""
            SELECT User, Host, authentication_string, plugin, account_locked, password_expired, password_last_changed
            FROM mysql.user
            WHERE {filter_conditions}
        """
        )

        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        removed_count = 0

        # 记录新增和修改的账户
        added_accounts = []
        modified_accounts = []

        for row in cursor.fetchall():
            (
                username,
                host,
                password_hash,
                plugin,
                locked,
                expired,
                password_last_changed,
            ) = row

            # 记录服务器端的账户
            server_accounts.add((username, host))

            # 检查账户是否已存在
            existing = Account.query.filter_by(
                instance_id=instance.id, username=username, host=host
            ).first()

            account_data = {
                "username": username,
                "host": host,
                "database_name": "mysql",
                "account_type": None,
                "plugin": plugin,
                "password_expired": expired == "Y",
                "password_last_changed": (
                    password_last_changed.isoformat() if password_last_changed else None
                ),
                "is_locked": locked == "Y",
                "is_active": locked != "Y" and expired != "Y",
            }

            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host=host,
                    database_name="mysql",
                    account_type=None,  # MySQL没有账户类型概念
                    plugin=plugin,
                    password_expired=expired
                    == "Y",  # MySQL的password_expired字段，'Y'表示已过期
                    password_last_changed=password_last_changed,
                    is_locked=locked == "Y",  # MySQL的account_locked字段，'Y'表示锁定
                    is_active=locked != "Y" and expired != "Y",
                )
                db.session.add(account)
                added_count += 1
                added_accounts.append(account_data)
            else:
                # 检查是否有变化
                has_changes = (
                    existing.plugin != plugin
                    or existing.password_expired != (expired == "Y")
                    or existing.password_last_changed != password_last_changed
                    or existing.is_locked != (locked == "Y")
                    or existing.is_active != (locked != "Y" and expired != "Y")
                )

                if has_changes:
                    # 更新现有账户信息
                    existing.plugin = plugin
                    existing.password_expired = expired == "Y"
                    existing.password_last_changed = password_last_changed
                    existing.is_locked = locked == "Y"
                    existing.is_active = locked != "Y" and expired != "Y"
                    updated_count += 1
                    modified_accounts.append(account_data)

        # 删除服务器端不存在的本地账户
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

        synced_count = added_count + updated_count + removed_count

        db.session.commit()
        cursor.close()

        # 记录同步结果
        logging.info(
            f"MySQL账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {removed_count}, 总计: {synced_count}"
        )

        return {
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": updated_count,
            "added_accounts": added_accounts,
            "removed_accounts": removed_accounts,
            "modified_accounts": modified_accounts,
        }

    def _sync_postgresql_accounts(self, instance: Instance, conn) -> Dict[str, Any]:
        """同步PostgreSQL账户"""
        
        def is_password_expired(valid_until):
            """检查PostgreSQL密码是否过期，处理infinity值"""
            if valid_until is None:
                return False
            try:
                # 检查是否为'infinity'字符串
                if str(valid_until).lower() == 'infinity':
                    return False
                else:
                    from app.utils.timezone import now
                    return valid_until < now()
            except (ValueError, TypeError, OverflowError):
                # 如果时间戳无法解析或超出范围，认为密码未过期
                return False
        
        cursor = conn.cursor()
        
        # 获取PostgreSQL过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions('postgresql', 'rolname')
        
        cursor.execute(
            f"""
            SELECT 
                rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, 
                rolcanlogin, rolconnlimit, 
                CASE 
                    WHEN rolvaliduntil = 'infinity'::timestamp THEN NULL
                    ELSE rolvaliduntil 
                END as rolvaliduntil,
                rolbypassrls, rolreplication
            FROM pg_roles
            WHERE {filter_conditions}
        """
        )

        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        removed_count = 0

        # 记录新增和修改的账户
        added_accounts = []
        modified_accounts = []

        for row in cursor.fetchall():
            (
                username,
                is_super,
                inherits,
                can_create_role,
                can_create_db,
                can_login,
                conn_limit,
                valid_until,
                can_bypass_rls,
                can_replicate,
            ) = row

            # 记录服务器端的账户（PostgreSQL没有主机概念）
            server_accounts.add((username, ""))

            # 确定账户类型（PostgreSQL中用户和角色是同一个概念）
            if is_super:
                account_type = "role"  # 超级用户角色
            elif can_create_db or can_create_role:
                account_type = "role"  # 管理员角色
            else:
                account_type = "user"  # 普通用户

            # 检查密码是否过期
            password_expired = is_password_expired(valid_until)

            # 检查账户是否被锁定
            is_locked = not can_login

            # 检查账户是否活跃
            is_active = can_login and not password_expired

            account_data = {
                "username": username,
                "host": "",  # PostgreSQL没有主机概念
                "database_name": instance.database_name or DatabaseTypeUtils.get_database_type_config("postgresql").default_schema or "postgres",
                "account_type": account_type,
                "plugin": "postgresql",
                "password_expired": password_expired,
                "password_last_changed": None,
                "is_locked": is_locked,
                "is_active": is_active,
                "is_superuser": is_super,
                "can_create_db": can_create_db,
                "can_create_role": can_create_role,
                "can_bypass_rls": can_bypass_rls,
                "can_replicate": can_replicate,
            }

            # 检查账户是否已存在（PostgreSQL没有主机概念）
            existing = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host="",  # PostgreSQL没有主机概念
            ).first()

            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host="",  # PostgreSQL没有主机概念
                    database_name=DatabaseTypeUtils.get_database_type_config("postgresql").default_schema or "postgres",  # PostgreSQL默认数据库
                    account_type=(
                        "superuser" if is_super else "user"
                    ),  # PostgreSQL有明确的角色概念
                    plugin="postgresql",
                    password_expired=is_password_expired(valid_until),
                    password_last_changed=None,  # PostgreSQL不直接提供此信息
                    is_locked=not can_login,  # PostgreSQL的rolcanlogin字段，False表示被禁用
                    is_active=can_login
                    and not is_password_expired(valid_until),
                )
                db.session.add(account)
                added_count += 1
                added_accounts.append(account_data)
            else:
                # 检查是否有变化
                has_changes = (
                    existing.account_type != ("superuser" if is_super else "user")
                    or existing.password_expired
                    != is_password_expired(valid_until)
                    or existing.is_locked != (not can_login)
                    or existing.is_active
                    != (can_login and not is_password_expired(valid_until))
                )

                if has_changes:
                    # 更新现有账户信息
                    existing.account_type = "superuser" if is_super else "user"
                    existing.password_expired = is_password_expired(valid_until)
                    existing.is_locked = (
                        not can_login
                    )  # PostgreSQL的rolcanlogin字段，False表示被禁用
                    existing.is_active = can_login and not is_password_expired(valid_until)
                    updated_count += 1
                    modified_accounts.append(account_data)

        # 删除服务器端不存在的本地账户
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

        synced_count = added_count + updated_count + removed_count

        db.session.commit()
        cursor.close()

        # 记录同步结果
        logging.info(
            f"PostgreSQL账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {removed_count}, 总计: {synced_count}"
        )

        return {
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": updated_count,
            "added_accounts": added_accounts,
            "removed_accounts": removed_accounts,
            "modified_accounts": modified_accounts,
        }

    def _sync_sqlserver_accounts(self, instance: Instance, conn) -> Dict[str, Any]:
        """同步SQL Server账户"""
        cursor = conn.cursor()
        
        # 获取SQL Server过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions('sqlserver', 'name')
        
        cursor.execute(
            f"""
            SELECT name, type_desc, is_disabled, create_date, modify_date
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G')
            AND {filter_conditions}
            AND (name = 'sa' OR name NOT LIKE 'NT %')
        """
        )

        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        removed_count = 0

        # 记录新增和修改的账户
        added_accounts = []
        modified_accounts = []

        for row in cursor.fetchall():
            username, type_desc, is_disabled, create_date, modify_date = row

            # 记录服务器端的账户（SQL Server没有主机概念，使用用户名作为唯一标识）
            server_accounts.add((username, None))

            account_data = {
                "username": username,
                "host": None,
                "database_name": instance.database_name or DatabaseTypeUtils.get_database_type_config("sqlserver").default_schema or "master",
                "account_type": type_desc.lower(),
                "plugin": None,
                "password_expired": False,
                "password_last_changed": (
                    modify_date.isoformat() if modify_date else None
                ),
                "is_locked": bool(is_disabled),
                "is_active": not is_disabled,
                "account_created_at": create_date.isoformat() if create_date else None,
            }

            # 检查账户是否已存在（SQL Server没有主机概念）
            existing = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host=None,  # SQL Server没有主机概念
            ).first()

            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host=None,  # SQL Server没有主机概念
                    database_name=instance.database_name or DatabaseTypeUtils.get_database_type_config("sqlserver").default_schema or "master",
                    account_type=type_desc.lower(),  # 直接使用原始type_desc名称
                    plugin=None,  # SQL Server没有插件概念
                    password_expired=False,  # SQL Server不直接提供此信息
                    password_last_changed=modify_date,
                    is_locked=bool(is_disabled),  # SQL Server的is_disabled字段
                    is_active=not is_disabled,
                    account_created_at=create_date,
                )
                db.session.add(account)
                added_count += 1
                added_accounts.append(account_data)
            else:
                # 检查是否有变化
                has_changes = (
                    existing.account_type != type_desc.lower()
                    or existing.password_last_changed != modify_date
                    or existing.is_locked != bool(is_disabled)
                    or existing.is_active != (not is_disabled)
                    or existing.account_created_at != create_date
                )

                if has_changes:
                    # 更新现有账户信息
                    existing.account_type = type_desc.lower()
                    existing.password_last_changed = modify_date
                    existing.is_locked = bool(
                        is_disabled
                    )  # SQL Server的is_disabled字段
                    existing.is_active = not is_disabled
                    existing.account_created_at = create_date
                    updated_count += 1
                    modified_accounts.append(account_data)

        # 删除服务器端不存在的本地账户（SQL Server没有主机概念）
        local_accounts = Account.query.filter_by(instance_id=instance.id).all()
        removed_accounts = []

        for local_account in local_accounts:
            # SQL Server没有主机概念，只比较用户名
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

        synced_count = added_count + updated_count + removed_count

        db.session.commit()
        cursor.close()

        # 记录同步结果
        logging.info(
            f"SQL Server账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {removed_count}, 总计: {synced_count}"
        )

        return {
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": updated_count,
            "added_accounts": added_accounts,
            "removed_accounts": removed_accounts,
            "modified_accounts": modified_accounts,
        }

    def _sync_oracle_accounts(self, instance: Instance, conn) -> Dict[str, Any]:
        """同步Oracle账户"""
        cursor = conn.cursor()
        
        # 获取Oracle过滤规则
        filter_conditions = database_filter_manager.get_sql_filter_conditions('oracle', 'username')
        
        cursor.execute(
            f"""
            SELECT username, user_id, account_status, lock_date, expiry_date, 
                   default_tablespace, created, authentication_type
            FROM dba_users
            WHERE {filter_conditions}
            ORDER BY username
        """
        )

        # 获取服务器端的所有账户
        server_accounts = set()
        synced_count = 0
        added_count = 0
        updated_count = 0
        removed_count = 0

        # 记录新增和修改的账户
        added_accounts = []
        modified_accounts = []

        for row in cursor.fetchall():
            (
                username,
                user_id,
                status,
                lock_date,
                expiry_date,
                default_tablespace,
                created,
                auth_type,
            ) = row

            # 记录服务器端的账户
            server_accounts.add((username, "localhost"))

            account_data = {
                "username": username,
                "user_id": user_id,  # Oracle数据库中的用户ID
                "host": "localhost",
                "database_name": instance.database_name or DatabaseTypeUtils.get_database_type_config("oracle").default_schema or "ORCL",
                "account_type": auth_type,  # 使用认证类型作为账户类型
                "plugin": "oracle",
                "password_expired": status in ["EXPIRED", "EXPIRED(GRACE)"],
                "password_last_changed": None,  # Oracle没有密码最后修改时间概念
                "is_locked": status in ["LOCKED", "LOCKED(TIMED)"]
                or lock_date is not None,
                "is_active": status == "OPEN",
                "created_at": created,  # Oracle的created字段映射到created_at
                "lock_date": lock_date,  # 锁定日期
                "expiry_date": expiry_date,  # 过期日期
                "default_tablespace": default_tablespace,  # 默认表空间
            }

            # 检查账户是否已存在
            existing = Account.query.filter_by(
                instance_id=instance.id,
                username=username,
                host="localhost",  # Oracle默认主机
            ).first()

            if not existing:
                account = Account(
                    instance_id=instance.id,
                    username=username,
                    host="localhost",
                    database_name=instance.database_name or DatabaseTypeUtils.get_database_type_config("oracle").default_schema or "ORCL",
                    account_type=auth_type,  # 使用认证类型作为账户类型
                    plugin="oracle",
                    password_expired=status in ["EXPIRED", "EXPIRED(GRACE)"],
                    password_last_changed=None,  # Oracle没有密码最后修改时间概念
                    is_locked=status in ["LOCKED", "LOCKED(TIMED)"]
                    or lock_date is not None,  # Oracle的锁定状态
                    is_active=status == "OPEN",
                    created_at=created,  # 使用Oracle的created字段作为创建时间
                    user_id=user_id,  # Oracle数据库中的用户ID
                    lock_date=lock_date,  # 锁定日期
                    expiry_date=expiry_date,  # 过期日期
                    default_tablespace=default_tablespace,  # 默认表空间
                )
                db.session.add(account)
                added_count += 1
                added_accounts.append(account_data)
            else:
                # 检查是否有变化
                has_changes = (
                    existing.password_expired
                    != (status in ["EXPIRED", "EXPIRED(GRACE)"])
                    or existing.is_locked
                    != (status in ["LOCKED", "LOCKED(TIMED)"] or lock_date is not None)
                    or existing.is_active != (status == "OPEN")
                    or existing.account_type != auth_type
                    or existing.user_id != user_id
                    or existing.lock_date != lock_date
                    or existing.expiry_date != expiry_date
                    or existing.default_tablespace != default_tablespace
                )

                if has_changes:
                    # 更新现有账户信息
                    existing.password_expired = status in ["EXPIRED", "EXPIRED(GRACE)"]
                    existing.is_locked = (
                        status in ["LOCKED", "LOCKED(TIMED)"] or lock_date is not None
                    )
                    existing.is_active = status == "OPEN"
                    existing.account_type = auth_type
                    existing.user_id = user_id
                    existing.lock_date = lock_date
                    existing.expiry_date = expiry_date
                    existing.default_tablespace = default_tablespace
                    # 注意：created_at字段在账户创建后不应该被更新
                    updated_count += 1
                    modified_accounts.append(account_data)

        # 删除服务器端不存在的本地账户
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

        synced_count = added_count + updated_count + removed_count

        db.session.commit()
        cursor.close()

        # 记录同步结果
        logging.info(
            f"Oracle账户同步完成 - 实例: {instance.name}, 新增: {added_count}, 更新: {updated_count}, 删除: {removed_count}, 总计: {synced_count}"
        )

        return {
            "synced_count": synced_count,
            "added_count": added_count,
            "removed_count": removed_count,
            "modified_count": updated_count,
            "added_accounts": added_accounts,
            "removed_accounts": removed_accounts,
            "modified_accounts": modified_accounts,
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

            # 使用ConnectionFactory创建新连接
            from app.services.connection_factory import ConnectionFactory
            connection_obj = ConnectionFactory.create_connection(instance)
            if not connection_obj:
                log_error(f"不支持的数据库类型: {instance.db_type}")
                return None
            
            # 建立连接
            if connection_obj.connect():
                conn = connection_obj.connection
            else:
                log_error(f"无法建立{instance.db_type}连接")
                return None

            if conn:
                # 存储连接
                self.connections[instance.id] = conn
                log_operation(
                    "database_connect",
                    details={
                        "instance_id": instance.id,
                        "db_type": instance.db_type,
                        "host": instance.host,
                    },
                )

            return conn

        except Exception as e:
            log_error(
                e, context={"instance_id": instance.id, "instance_name": instance.name}
            )
            return None

    def get_database_version(self, instance: Instance, conn) -> Optional[str]:
        """
        获取数据库版本信息

        Args:
            instance: 数据库实例
            conn: 数据库连接

        Returns:
            数据库版本字符串
        """
        try:
            if instance.db_type == "postgresql":
                return self._get_postgresql_version(conn)
            elif instance.db_type == "mysql":
                return self._get_mysql_version(conn)
            elif instance.db_type == "sqlserver":
                return self._get_sqlserver_version(conn)
            elif instance.db_type == "oracle":
                return self._get_oracle_version(conn)
            else:
                return None
        except Exception as e:
            logging.error(f"获取数据库版本失败: {e}")
            return None

    def _test_connection_validity(self, conn, db_type: str) -> bool:
        """测试连接有效性"""
        try:
            if db_type == "mysql":
                conn.ping(reconnect=False)
            elif db_type == "postgresql":
                conn.execute("SELECT 1")
            elif db_type == "sqlserver":
                conn.execute("SELECT 1")
            elif db_type == "oracle":
                conn.execute("SELECT 1 FROM DUAL")
            return True
        except:
            return False





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
                    if hasattr(conn, "close"):
                        conn.close()
                    elif hasattr(conn, "disconnect"):
                        conn.disconnect()
                del self.connections[instance.id]
                log_operation(
                    "database_disconnect",
                    details={"instance_id": instance.id, "db_type": instance.db_type},
                )
        except Exception as e:
            log_error(e, context={"instance_id": instance.id})
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
                    if hasattr(conn, "close"):
                        conn.close()
                    elif hasattr(conn, "disconnect"):
                        conn.disconnect()
            except Exception as e:
                log_error(e, context={"instance_id": instance_id})
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
                if hasattr(conn, "ping"):
                    conn.ping()
                elif hasattr(conn, "execute"):
                    conn.execute("SELECT 1")
            except Exception:
                stale_connections.append(instance_id)

        # 移除过期连接
        for instance_id in stale_connections:
            try:
                conn = self.connections[instance_id]
                if hasattr(conn, "close"):
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
                return {"connected": True, "status": "active", "message": "连接正常"}
            else:
                return {
                    "connected": False,
                    "status": "disconnected",
                    "message": "未连接",
                }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "message": f"连接错误: {str(e)}",
            }

    def execute_query(
        self, instance: Instance, query: str, params: tuple = None
    ) -> Dict[str, Any]:
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
                return {"success": False, "error": "查询包含不安全的操作，已被阻止"}

            conn = self.get_connection(instance)
            if not conn:
                return {"success": False, "error": "无法获取数据库连接"}

            cursor = conn.cursor()

            # 使用参数化查询防止SQL注入
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
                cursor.close()
                return {
                    "success": True,
                    "data": results,
                    "columns": columns,
                    "row_count": len(results),
                }
            else:
                conn.commit()
                cursor.close()
                return {
                    "success": True,
                    "message": "查询执行成功",
                    "affected_rows": cursor.rowcount,
                }

        except Exception as e:
            log_error(
                e,
                context={"instance_id": instance.id, "query": query, "params": params},
            )
            return {"success": False, "error": f"查询执行失败: {str(e)}"}

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
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "ALTER",
            "CREATE",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "SP_",
            "XP_",
            "BULK",
            "BULKINSERT",
            "UNION",
            "--",
            "/*",
            "*/",
            ";",
            "XP_CMDSHELL",
            "SP_EXECUTESQL",
        ]

        # 检查是否包含危险操作
        for operation in dangerous_operations:
            if operation in query_upper:
                return False

        # 只允许SELECT查询（用于数据查看）
        if not query_upper.startswith("SELECT"):
            return False

        # 检查查询长度（防止过长的查询）
        if len(query) > 10000:
            return False

        return True

    def get_account_permissions(
        self, instance: Instance, account: Account
    ) -> Dict[str, Any]:
        """
        获取账户权限详情

        Args:
            instance: 数据库实例
            account: 账户对象

        Returns:
            Dict: 权限信息
        """
        try:
            # 使用权限查询工厂获取权限
            result = PermissionQueryFactory.get_account_permissions(instance, account)
            
            if result.get("success"):
                return result
            else:
                return {
                    "global": [],
                    "database": [],
                    "error": result.get("error", "获取权限失败")
                }
        except Exception as e:
            return {"global": [], "database": [], "error": f"获取权限失败: {str(e)}"}

    def _get_mysql_permissions(
        self, instance: Instance, account: Account
    ) -> Dict[str, Any]:
        """获取MySQL账户权限"""
        try:
            # 优先使用本地数据库中已同步的权限数据
            if account.permissions:
                import json

                permissions = json.loads(account.permissions)

                # 直接返回本地权限数据，确保包含GRANT OPTION权限
                return {
                    "global": permissions.get("global", []),
                    "database": permissions.get("database", []),
                }

            # 如果本地没有权限数据，则从服务器查询（备用方案）
            conn = self.get_connection(instance)
            if not conn:
                return {"global": [], "database": [], "error": "无法获取数据库连接"}

            cursor = conn.cursor()

            try:
                # 获取全局权限
                cursor.execute(
                    """
                    SELECT PRIVILEGE_TYPE, IS_GRANTABLE
                    FROM INFORMATION_SCHEMA.USER_PRIVILEGES
                    WHERE GRANTEE = %s
                """,
                    (f"'{account.username}'@'{account.host}'",),
                )

                global_permissions = []
                can_grant = False
                for row in cursor.fetchall():
                    privilege, is_grantable = row
                    global_permissions.append(
                        {
                            "privilege": privilege,
                            "granted": True,
                            "grantable": bool(is_grantable),
                        }
                    )
                    if is_grantable:
                        can_grant = True

                # 检查用户是否真正拥有GRANT OPTION权限
                cursor.execute(
                    """
                    SELECT Grant_priv FROM mysql.user 
                    WHERE User = %s AND Host = %s
                """,
                    (account.username, account.host),
                )

                grant_result = cursor.fetchone()
                if grant_result and grant_result[0] == "Y":
                    # 用户真正拥有GRANT OPTION权限
                    global_permissions.append(
                        {
                            "privilege": "GRANT OPTION",
                            "granted": True,
                            "grantable": False,
                        }
                    )

                # 获取数据库权限
                cursor.execute(
                    """
                    SELECT TABLE_SCHEMA, PRIVILEGE_TYPE
                    FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES
                    WHERE GRANTEE = %s
                    ORDER BY TABLE_SCHEMA, PRIVILEGE_TYPE
                """,
                    (f"'{account.username}'@'{account.host}'",),
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
                    database_permissions.append(
                        {"database": schema, "privileges": privileges}
                    )

                return {"global": global_permissions, "database": database_permissions}

            finally:
                cursor.close()

        except Exception as e:
            return {"global": [], "database": [], "error": f"获取权限失败: {str(e)}"}

    def _get_postgresql_permissions(
        self, instance: Instance, account: Account
    ) -> Dict[str, Any]:
        """获取PostgreSQL账户权限 - 根据新的权限配置结构"""
        try:
            print(f"DEBUG: 获取PostgreSQL权限 - 账户: {account.username}")
            print(f"DEBUG: 本地权限数据: {account.permissions}")

            # 优先使用本地数据库中已同步的权限数据
            if account.permissions:
                import json

                permissions = json.loads(account.permissions)
                print(f"DEBUG: 解析后的权限数据: {permissions}")

                # 转换为前端显示格式
                result = {
                    "predefined_roles": permissions.get("predefined_roles", []),
                    "role_attributes": permissions.get("role_attributes", []),
                    "database_privileges": permissions.get("database_privileges", []),
                    "tablespace_privileges": permissions.get(
                        "tablespace_privileges", []
                    ),
                }
                print(f"DEBUG: 返回的权限结果: {result}")
                return result

            # 如果本地没有权限数据，则从服务器查询（备用方案）
            conn = self.get_connection(instance)
            if not conn:
                return {
                    "predefined_roles": [],
                    "role_attributes": [],
                    "database_privileges": [],
                    "tablespace_privileges": [],
                    "error": "无法获取数据库连接",
                }

            # 从服务器查询权限数据
            print("DEBUG: 从服务器实时查询权限数据")
            from app.services.account_sync_service import AccountSyncService

            sync_service = AccountSyncService()
            permissions = sync_service._get_postgresql_account_permissions(
                instance, conn, account.username
            )
            print(f"DEBUG: 实时查询的权限数据: {permissions}")

            if permissions:
                # 将实时查询到的权限数据保存到本地数据库
                import json

                account.permissions = json.dumps(permissions)
                account.is_superuser = permissions.get("is_superuser", False)
                account.can_grant = permissions.get("can_grant", False)
                db.session.commit()

                result = {
                    "predefined_roles": permissions.get("predefined_roles", []),
                    "role_attributes": permissions.get("role_attributes", []),
                    "database_privileges": permissions.get("database_privileges", []),
                    "tablespace_privileges": permissions.get(
                        "tablespace_privileges", []
                    ),
                }
                print(f"DEBUG: 实时查询返回的权限结果: {result}")
                return result
            else:
                print("DEBUG: 实时查询返回空权限数据")
                return {
                    "predefined_roles": [],
                    "role_attributes": [],
                    "database_privileges": [],
                    "tablespace_privileges": [],
                    "error": "权限数据未同步，请先同步账户",
                }

        except Exception as e:
            return {
                "predefined_roles": [],
                "role_attributes": [],
                "database_privileges": [],
                "tablespace_privileges": [],
                "error": f"获取权限失败: {str(e)}",
            }

    def _get_sqlserver_permissions(
        self, instance: Instance, account: Account
    ) -> Dict[str, Any]:
        """获取SQL Server账户权限"""
        conn = self.get_connection(instance)
        if not conn:
            return {
                "global": [],
                "database": [],
                "server_roles": [],
                "database_roles": [],
                "error": "无法获取数据库连接",
            }

        cursor = conn.cursor()

        try:
            # 获取服务器级权限
            cursor.execute(
                """
                SELECT permission_name, state_desc
                FROM sys.server_permissions sp
                JOIN sys.server_principals p ON sp.grantee_principal_id = p.principal_id
                WHERE p.name = %s
            """,
                (account.username,),
            )

            global_permissions = []
            for row in cursor.fetchall():
                permission, state = row
                global_permissions.append(
                    {
                        "privilege": permission,
                        "granted": state == "GRANT",
                        "grantable": False,  # SQL Server权限查询较复杂，暂时设为False
                    }
                )

            # 获取服务器级别角色
            cursor.execute(
                """
                SELECT r.name, r.type_desc
                FROM sys.server_role_members rm
                JOIN sys.server_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.server_principals m ON rm.member_principal_id = m.principal_id
                WHERE m.name = %s
            """,
                (account.username,),
            )

            server_roles = []
            for row in cursor.fetchall():
                role_name, role_type = row
                server_roles.append({"role": role_name, "type": role_type})

            # 获取数据库权限和角色
            cursor.execute(
                """
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
            """,
                (account.username, account.username),
            )

            db_permissions = {}
            for row in cursor.fetchall():
                db_name, permission, state = row
                if db_name and permission:
                    if db_name not in db_permissions:
                        db_permissions[db_name] = []
                    if state == "GRANT":
                        db_permissions[db_name].append(permission)

            # 获取数据库级别角色
            cursor.execute(
                """
                SELECT db.name, r.name, r.type_desc
                FROM sys.databases db
                CROSS JOIN sys.database_role_members rm
                JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
                JOIN sys.database_principals m ON rm.member_principal_id = m.principal_id
                WHERE m.name = %s OR m.name IN (
                    SELECT name FROM sys.database_principals WHERE sid = (
                        SELECT sid FROM sys.server_principals WHERE name = %s
                    )
                )
                ORDER BY db.name, r.name
            """,
                (account.username, account.username),
            )

            database_roles = {}
            for row in cursor.fetchall():
                db_name, role_name, role_type = row
                if db_name:
                    if db_name not in database_roles:
                        database_roles[db_name] = []
                    database_roles[db_name].append(
                        {"role": role_name, "type": role_type}
                    )

            database_permissions = []
            for db_name, privileges in db_permissions.items():
                if privileges:
                    database_permissions.append(
                        {"database": db_name, "privileges": privileges}
                    )

            return {
                "global": global_permissions,
                "database": database_permissions,
                "server_roles": server_roles,
                "database_roles": database_roles,
            }

        except Exception as e:
            return {
                "global": [],
                "database": [],
                "server_roles": [],
                "database_roles": [],
                "error": f"查询权限失败: {str(e)}",
            }
        finally:
            cursor.close()

    def _get_oracle_permissions(
        self, instance: Instance, account: Account
    ) -> Dict[str, Any]:
        """获取Oracle账户权限 - 根据新的权限配置结构"""
        try:
            # 优先使用本地数据库中已同步的权限数据
            if account.permissions:
                import json

                permissions = json.loads(account.permissions)

                # 转换为前端显示格式
                return {
                    "roles": permissions.get("roles", []),
                    "system_privileges": permissions.get("system_privileges", []),
                    "tablespace_privileges": permissions.get(
                        "tablespace_privileges", []
                    ),
                    "tablespace_quotas": permissions.get("tablespace_quotas", []),
                }

            # 如果本地没有权限数据，则从服务器查询（备用方案）
            conn = self.get_connection(instance)
            if not conn:
                return {
                    "roles": [],
                    "system_privileges": [],
                    "tablespace_privileges": [],
                    "tablespace_quotas": [],
                    "error": "无法获取数据库连接",
                }

            # 从服务器查询权限数据
            from app.services.account_sync_service import AccountSyncService

            sync_service = AccountSyncService()
            permissions_info = sync_service._get_oracle_account_permissions(
                conn, account.username
            )

            if permissions_info and "permissions_json" in permissions_info:
                import json

                permissions = json.loads(permissions_info["permissions_json"])

                # 将实时查询到的权限数据保存到本地数据库
                account.permissions = permissions_info["permissions_json"]
                account.is_superuser = permissions_info.get("is_superuser", False)
                account.can_grant = permissions_info.get("can_grant", False)
                db.session.commit()

                return {
                    "roles": permissions.get("roles", []),
                    "system_privileges": permissions.get("system_privileges", []),
                    "tablespace_privileges": permissions.get(
                        "tablespace_privileges", []
                    ),
                    "tablespace_quotas": permissions.get("tablespace_quotas", []),
                }
            else:
                return {
                    "roles": [],
                    "system_privileges": [],
                    "tablespace_privileges": [],
                    "tablespace_quotas": [],
                    "error": "权限数据未同步，请先同步账户",
                }

        except Exception as e:
            return {
                "roles": [],
                "system_privileges": [],
                "tablespace_privileges": [],
                "tablespace_quotas": [],
                "error": f"获取权限失败: {str(e)}",
            }

    def _get_mysql_version(self, conn) -> Optional[str]:
        """获取MySQL版本"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            return version
        except Exception as e:
            logging.error(f"获取MySQL版本失败: {e}")
            return None

    def _get_postgresql_version(self, conn) -> Optional[str]:
        """获取PostgreSQL版本"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.close()
            # 提取版本号，例如 "PostgreSQL 15.3 on x86_64-pc-linux-gnu"
            import re

            match = re.search(r"PostgreSQL (\d+\.\d+)", version)
            return match.group(1) if match else version
        except Exception as e:
            logging.error(f"获取PostgreSQL版本失败: {e}")
            return None

    def _get_sqlserver_version(self, conn) -> Optional[str]:
        """获取SQL Server版本"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            cursor.close()
            # 提取版本号，例如 "Microsoft SQL Server 2019 (RTM-CU18)"
            import re

            match = re.search(r"Microsoft SQL Server (\d+)", version)
            return match.group(1) if match else version
        except Exception as e:
            logging.error(f"获取SQL Server版本失败: {e}")
            return None

    def _get_oracle_version(self, conn) -> Optional[str]:
        """获取Oracle版本"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM v$version WHERE rownum = 1")
            version = cursor.fetchone()[0]
            cursor.close()
            # 提取版本号，例如 "Oracle Database 19c Enterprise Edition Release 19.0.0.0.0"
            import re

            match = re.search(r"Oracle Database (\d+c?)", version)
            return match.group(1) if match else version
        except Exception as e:
            logging.error(f"获取Oracle版本失败: {e}")
            return None
