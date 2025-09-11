"""
泰摸鱼吧 - 数据库连接管理服务
"""

import pymysql
import logging
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
            if instance.db_type == "postgresql":
                return self._test_postgresql_connection(instance)
            elif instance.db_type == "mysql":
                return self._test_mysql_connection(instance)
            elif instance.db_type == "sqlserver":
                return self._test_sqlserver_connection(instance)
            elif instance.db_type == "oracle":
                return self._test_oracle_connection(instance)
            else:
                return {
                    "success": False,
                    "error": f"不支持的数据库类型: {instance.db_type}",
                }
        except Exception as e:
            return {"success": False, "error": f"连接测试失败: {str(e)}"}

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
        cursor.execute(
            """
            SELECT User, Host, authentication_string, plugin, account_locked, password_expired, password_last_changed
            FROM mysql.user
            WHERE User != 'root' AND User != 'mysql.sys'
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
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, 
                rolcanlogin, rolconnlimit, rolvaliduntil, rolbypassrls, rolreplication
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%' 
            AND rolname NOT IN ('postgres', 'rdsadmin', 'rds_superuser')
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
            from datetime import datetime
            from app.utils.timezone import now

            password_expired = valid_until is not None and valid_until < now()

            # 检查账户是否被锁定
            is_locked = not can_login

            # 检查账户是否活跃
            is_active = can_login and not password_expired

            account_data = {
                "username": username,
                "host": "",  # PostgreSQL没有主机概念
                "database_name": instance.database_name or "postgres",
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
                    database_name="postgres",  # PostgreSQL默认数据库
                    account_type=(
                        "superuser" if is_super else "user"
                    ),  # PostgreSQL有明确的角色概念
                    plugin="postgresql",
                    password_expired=valid_until is not None and valid_until < now(),
                    password_last_changed=None,  # PostgreSQL不直接提供此信息
                    is_locked=not can_login,  # PostgreSQL的rolcanlogin字段，False表示被禁用
                    is_active=can_login
                    and (valid_until is None or valid_until > now()),
                )
                db.session.add(account)
                added_count += 1
                added_accounts.append(account_data)
            else:
                # 检查是否有变化
                has_changes = (
                    existing.account_type != ("superuser" if is_super else "user")
                    or existing.password_expired
                    != (valid_until is not None and valid_until < now())
                    or existing.is_locked != (not can_login)
                    or existing.is_active
                    != (can_login and (valid_until is None or valid_until > now()))
                )

                if has_changes:
                    # 更新现有账户信息
                    existing.account_type = "superuser" if is_super else "user"
                    existing.password_expired = (
                        valid_until is not None and valid_until < now()
                    )
                    existing.is_locked = (
                        not can_login
                    )  # PostgreSQL的rolcanlogin字段，False表示被禁用
                    existing.is_active = can_login and (
                        valid_until is None or valid_until > now()
                    )
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
        cursor.execute(
            """
            SELECT name, type_desc, is_disabled, create_date, modify_date
            FROM sys.server_principals
            WHERE type IN ('S', 'U', 'G')
            AND name NOT LIKE '##%'
            AND name NOT LIKE 'NT SERVICE\%'
            AND name NOT LIKE 'NT AUTHORITY\%'
            AND name NOT LIKE 'BUILTIN\%'
            AND name NOT IN ('public', 'guest', 'dbo')
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
                "database_name": instance.database_name or "master",
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
                    database_name=instance.database_name or "master",
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
        cursor.execute(
            """
            SELECT username, user_id, account_status, lock_date, expiry_date, 
                   default_tablespace, created, authentication_type
            FROM dba_users
            WHERE username NOT IN (
                -- Oracle示例账户
                'SCOTT',
                -- Oracle功能账户（根据官方文档）
                'CTXSYS', 'EXFSYS', 'MDDATA', 'APPQOSSYS', 'OUTLN', 'DIP', 'TSMSYS', 'WMSYS', 
                'XDB', 'ANONYMOUS', 'ORDPLUGINS', 'ORDSYS', 'SI_INFORMTN_SCHEMA', 'MDSYS', 
                'OLAPSYS', 'SPATIAL_CSW_ADMIN_USR', 'SPATIAL_WFS_ADMIN_USR', 'APEX_PUBLIC_USER', 
                'APEX_030200', 'FLOWS_FILES', 'HR', 'OE', 'PM', 'IX', 'SH', 'BI', 'DEMO', 
                'ADMIN', 'AUDSYS', 'GSMADMIN_INTERNAL', 'GSMCATUSER', 'GSMUSER', 'LBACSYS', 
                'OJVMSYS', 'ORACLE_OCM', 'ORDDATA', 'ORDPLUGINS', 'ORDS_METADATA', 
                'ORDS_PUBLIC_USER', 'PDBADMIN', 'RDSADMIN', 'REMOTE_SCHEDULER_AGENT', 
                'SYSBACKUP', 'SYSDG', 'SYSKM', 'SYSRAC', 'SYS$UMF', 'XS$NULL', 'OWBSYS', 
                'OWBSYS_AUDIT'
            )
            -- 排除系统模式账户
            AND username NOT LIKE 'SYS$%'
            AND username NOT LIKE 'GSM%'
            AND username NOT LIKE 'XDB%'
            AND username NOT LIKE 'APEX%'
            AND username NOT LIKE 'ORD%'
            AND username NOT LIKE 'SPATIAL_%'
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
                "database_name": instance.database_name or "ORCL",
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
                    database_name=instance.database_name or "ORCL",
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

    def _test_postgresql_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试PostgreSQL连接"""
        try:
            import psycopg

            # 验证必需参数
            if not instance.host:
                return {"success": False, "error": "主机地址不能为空"}

            if not instance.port or instance.port <= 0:
                return {"success": False, "error": "端口号必须大于0"}

            if not instance.credential:
                return {"success": False, "error": "数据库凭据不能为空"}

            if not instance.credential.username:
                return {"success": False, "error": "数据库用户名不能为空"}

            # 尝试连接PostgreSQL
            password = instance.credential.get_plain_password()
            conn = psycop.connect(
                host=instance.host,
                port=instance.port,
                database="postgres",  # PostgreSQL默认数据库
                user=instance.credential.username,
                password=password,
                connect_timeout=10,
            )

            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception("连接测试查询失败")

                # 获取数据库版本
                cursor.execute("SELECT version()")
                version_result = cursor.fetchone()
                full_version = version_result[0] if version_result else None

                # 提取简洁的版本号（如13.4）
                import re

                if full_version:
                    version_match = re.search(r"PostgreSQL (\d+\.\d+)", full_version)
                    database_version = (
                        version_match.group(1) if version_match else full_version
                    )
                else:
                    database_version = None

            conn.close()

            # 更新实例的数据库版本和最后连接时间
            from app import db
            from app.utils.timezone import now

            if database_version:
                instance.database_version = database_version

            # 更新最后连接时间
            instance.last_connected = now()
            db.session.commit()

            return {
                "success": True,
                "message": f'PostgreSQL连接成功 (主机: {instance.host}:{instance.port}, 数据库: {instance.database_name or "postgres"}, 版本: {database_version or "未知"})',
                "database_version": database_version,
            }

        except ImportError:
            return {
                "success": False,
                "error": "PostgreSQL驱动未安装",
                "details": "系统缺少psycopg驱动包",
                "solution": "请运行命令安装: pip install psycopg[binary]",
                "error_type": "missing_driver",
            }
        except psycopg.OperationalError as e:
            error_msg = str(e)
            if "Connection refused" in error_msg:
                return {
                    "success": False,
                    "error": "PostgreSQL服务未运行",
                    "details": f"无法连接到 {instance.host}:{instance.port}，服务器拒绝连接",
                    "solution": "请确保PostgreSQL服务正在运行，并检查端口号是否正确",
                    "error_type": "connection_refused",
                }
            elif "authentication failed" in error_msg.lower():
                return {
                    "success": False,
                    "error": "PostgreSQL认证失败",
                    "details": f"用户名或密码错误: {instance.credential.username}",
                    "solution": "请检查数据库凭据中的用户名和密码是否正确",
                    "error_type": "authentication_failed",
                }
            elif (
                "database" in error_msg.lower()
                and "does not exist" in error_msg.lower()
            ):
                return {
                    "success": False,
                    "error": "PostgreSQL数据库不存在",
                    "details": f'数据库 "{instance.database_name or "postgres"}" 不存在',
                    "solution": "请检查数据库名称是否正确，或创建该数据库",
                    "error_type": "database_not_found",
                }
            else:
                return {
                    "success": False,
                    "error": "PostgreSQL连接失败",
                    "details": error_msg,
                    "solution": "请检查网络连接、服务器状态和连接参数",
                    "error_type": "operational_error",
                }
        except psycopg.Error as e:
            return {
                "success": False,
                "error": "PostgreSQL错误",
                "details": str(e),
                "solution": "请检查PostgreSQL服务器配置和日志",
                "error_type": "psycopg2_error",
            }
        except Exception as e:
            return {
                "success": False,
                "error": "PostgreSQL连接失败",
                "details": str(e),
                "solution": "请检查所有连接参数和服务器状态",
                "error_type": "unknown_error",
            }

    def _test_mysql_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试MySQL连接"""
        try:
            # 验证必需参数
            if not instance.host:
                return {"success": False, "error": "主机地址不能为空"}

            if not instance.port or instance.port <= 0:
                return {"success": False, "error": "端口号必须大于0"}

            if not instance.credential:
                return {"success": False, "error": "数据库凭据不能为空"}

            if not instance.credential.username:
                return {"success": False, "error": "数据库用户名不能为空"}

            # 尝试连接MySQL
            # 获取原始密码
            password = instance.credential.get_plain_password()

            conn = pymysql.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name,
                user=instance.credential.username,
                password=password,
                charset="utf8mb4",
                autocommit=True,
                connect_timeout=10,  # 连接超时10秒
                read_timeout=30,  # 读取超时30秒
                write_timeout=30,  # 写入超时30秒
                sql_mode="TRADITIONAL",
            )

            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception("连接测试查询失败")

                # 获取数据库版本
                cursor.execute("SELECT VERSION()")
                version_result = cursor.fetchone()
                database_version = version_result[0] if version_result else None

            conn.close()

            # 更新实例的数据库版本和最后连接时间
            from app import db
            from app.utils.timezone import now

            if database_version:
                instance.database_version = database_version

            # 更新最后连接时间
            instance.last_connected = now()
            db.session.commit()

            return {
                "success": True,
                "message": f'MySQL连接成功 (主机: {instance.host}:{instance.port}, 数据库: {instance.database_name or "默认"}, 版本: {database_version or "未知"})',
                "database_version": database_version,
            }

        except pymysql.Error as e:
            error_code, error_msg = e.args
            if error_code == 2003:
                return {
                    "success": False,
                    "error": "MySQL服务未运行",
                    "details": f"无法连接到 {instance.host}:{instance.port}，服务器拒绝连接",
                    "solution": "请确保MySQL服务正在运行，并检查端口号是否正确",
                    "error_type": "connection_refused",
                }
            elif error_code == 1045:
                return {
                    "success": False,
                    "error": "MySQL认证失败",
                    "details": f"用户名或密码错误: {instance.credential.username}",
                    "solution": "请检查数据库凭据中的用户名和密码是否正确",
                    "error_type": "authentication_failed",
                }
            elif error_code == 1049:
                return {
                    "success": False,
                    "error": "MySQL数据库不存在",
                    "details": f'数据库 "{instance.database_name}" 不存在',
                    "solution": "请检查数据库名称是否正确，或创建该数据库",
                    "error_type": "database_not_found",
                }
            else:
                return {
                    "success": False,
                    "error": "MySQL连接失败",
                    "details": f"错误代码 {error_code}: {error_msg}",
                    "solution": "请检查MySQL服务器配置和日志",
                    "error_type": "mysql_error",
                }
        except Exception as e:
            return {
                "success": False,
                "error": "MySQL连接失败",
                "details": str(e),
                "solution": "请检查所有连接参数和服务器状态",
                "error_type": "unknown_error",
            }

    def _test_sqlserver_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试SQL Server连接"""
        try:
            import pymssql

            # 验证必需参数
            if not instance.host:
                return {"success": False, "error": "主机地址不能为空"}

            if not instance.port or instance.port <= 0:
                return {"success": False, "error": "端口号必须大于0"}

            if not instance.credential:
                return {"success": False, "error": "数据库凭据不能为空"}

            if not instance.credential.username:
                return {"success": False, "error": "数据库用户名不能为空"}

            # 尝试连接SQL Server
            # 获取原始密码
            password = instance.credential.get_plain_password()

            conn = pymssql.connect(
                server=instance.host,
                port=instance.port,
                database=instance.database_name or "master",
                user=instance.credential.username,
                password=password,
                timeout=10,
            )

            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception("连接测试查询失败")

                # 获取数据库版本
                cursor.execute("SELECT @@VERSION")
                version_result = cursor.fetchone()
                full_version = version_result[0] if version_result else None

                # 使用正则表达式提取版本号（如2017, 2019, 2022等）
                import re

                if full_version:
                    version_match = re.search(
                        r"Microsoft SQL Server (\d{4})", full_version
                    )
                    database_version = (
                        version_match.group(1) if version_match else full_version
                    )
                else:
                    database_version = None

            conn.close()

            # 更新实例的数据库版本和最后连接时间
            from app import db
            from app.utils.timezone import now

            if database_version:
                instance.database_version = database_version

            # 更新最后连接时间
            instance.last_connected = now()
            db.session.commit()

            return {
                "success": True,
                "message": f'SQL Server连接成功 (主机: {instance.host}:{instance.port}, 数据库: {instance.database_name or "master"}, 版本: {database_version or "未知"})',
                "database_version": database_version,
            }

        except ImportError:
            return {
                "success": False,
                "error": "SQL Server驱动未安装，请安装pymssql或pyodbc",
            }
        except pymssql.Error as e:
            return {"success": False, "error": f"SQL Server连接失败: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"SQL Server连接失败: {str(e)}"}

    def _test_oracle_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试Oracle连接"""
        try:
            import oracledb

            # 验证必需参数
            if not instance.host:
                return {"success": False, "error": "主机地址不能为空"}

            if not instance.port or instance.port <= 0:
                return {"success": False, "error": "端口号必须大于0"}

            if not instance.credential:
                return {"success": False, "error": "数据库凭据不能为空"}

            if not instance.credential.username:
                return {"success": False, "error": "数据库用户名不能为空"}

            # 尝试连接Oracle (使用python-oracledb)
            # 构建连接字符串
            database_name = instance.database_name or "ORCL"

            # 优先使用服务名格式，因为大多数现代Oracle配置都使用服务名
            # 如果包含点号(.)，则认为是Service Name，否则也尝试服务名格式
            if "." in database_name:
                # Service Name格式: host:port/service_name
                dsn = f"{instance.host}:{instance.port}/{database_name}"
            else:
                # 对于简单名称，优先尝试服务名格式，如果失败再尝试SID格式
                dsn = f"{instance.host}:{instance.port}/{database_name}"
            password = instance.credential.get_plain_password()

            # 优先使用Thick模式连接（适用于所有Oracle版本，包括11g）
            conn = None
            thick_mode_failed = False

            # 首先尝试Thick模式连接
            try:
                # 初始化Thick模式（需要Oracle Instant Client）
                oracledb.init_oracle_client()
                conn = oracledb.connect(
                    user=instance.credential.username, password=password, dsn=dsn
                )
            except Exception as e:
                # Thick模式失败，记录错误并尝试Thin模式
                thick_mode_failed = True
                error_msg = str(e)

                # 如果Thick模式失败，尝试Thin模式（适用于Oracle 12c+）
                if (
                    "DPI-1047" in error_msg
                    or "Oracle Client library" in error_msg
                    or "thin mode" in error_msg.lower()
                ):
                    # Thick模式失败，尝试Thin模式
                    try:
                        conn = oracledb.connect(
                            user=instance.credential.username,
                            password=password,
                            dsn=dsn,
                        )
                    except Exception as thin_error:
                        # 如果Thin模式也失败，尝试SID格式（如果当前是服务名格式）
                        if (
                            not dsn.endswith(f":{database_name}")
                            and not "." in database_name
                        ):
                            try:
                                sid_dsn = (
                                    f"{instance.host}:{instance.port}:{database_name}"
                                )
                                conn = oracledb.connect(
                                    user=instance.credential.username,
                                    password=password,
                                    dsn=sid_dsn,
                                )
                            except Exception as sid_error:
                                # 如果SID格式也失败，抛出原始错误
                                raise e
                        else:
                            raise e
                else:
                    # 如果不是驱动问题，尝试SID格式（如果当前是服务名格式）
                    if (
                        not dsn.endswith(f":{database_name}")
                        and not "." in database_name
                    ):
                        try:
                            sid_dsn = f"{instance.host}:{instance.port}:{database_name}"
                            conn = oracledb.connect(
                                user=instance.credential.username,
                                password=password,
                                dsn=sid_dsn,
                            )
                        except Exception as sid_error:
                            # 如果SID格式也失败，抛出原始错误
                            raise e
                    else:
                        raise

            if not conn:
                raise Exception("无法建立Oracle连接")

            # 测试连接有效性
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                result = cursor.fetchone()
                if result[0] != 1:
                    raise Exception("连接测试查询失败")

                # 获取数据库版本
                cursor.execute("SELECT * FROM v$version WHERE rownum = 1")
                version_result = cursor.fetchone()
                full_version = version_result[0] if version_result else None

                # 提取简洁的版本号（如11g, 12c, 19c等）
                import re

                if full_version:
                    # 匹配11g, 12c, 18c, 19c, 21c等格式
                    match = re.search(r"Oracle Database (\d+[gc])", full_version)
                    if match:
                        database_version = match.group(1)
                    else:
                        # 如果没有找到g或c后缀，尝试匹配版本号
                        match = re.search(r"Oracle Database (\d+)", full_version)
                        if match:
                            version_num = match.group(1)
                            # 根据版本号添加后缀
                            if version_num.startswith("11"):
                                database_version = "11g"
                            elif version_num.startswith("12"):
                                database_version = "12c"
                            elif version_num.startswith("18"):
                                database_version = "18c"
                            elif version_num.startswith("19"):
                                database_version = "19c"
                            elif version_num.startswith("21"):
                                database_version = "21c"
                            else:
                                database_version = version_num
                        else:
                            database_version = full_version
                else:
                    database_version = None

            conn.close()

            # 更新实例的数据库版本和最后连接时间
            from app import db
            from app.utils.timezone import now

            if database_version:
                instance.database_version = database_version

            # 更新最后连接时间
            instance.last_connected = now()
            db.session.commit()

            return {
                "success": True,
                "message": f'Oracle连接成功 (主机: {instance.host}:{instance.port}, 服务: {instance.database_name or "ORCL"}, 版本: {database_version or "未知"})',
                "database_version": database_version,
            }

        except ImportError:
            return {
                "success": False,
                "error": "Oracle驱动未安装",
                "details": "系统缺少python-oracledb驱动包",
                "solution": "请运行命令安装: pip install python-oracledb",
                "error_type": "missing_driver",
            }
        except oracledb.DatabaseError as e:
            error_msg = str(e)
            if "DPI-1047" in error_msg:
                return {
                    "success": False,
                    "error": "Oracle连接失败",
                    "details": "网络连接问题或Oracle服务不可达",
                    "solution": "请检查网络连接和Oracle服务状态，Oracle 11g需要使用Thick模式，请确保已安装Oracle Instant Client",
                    "error_type": "connection_failed",
                }
            elif "ORA-01017" in error_msg:
                return {
                    "success": False,
                    "error": "Oracle认证失败",
                    "details": f"用户名或密码错误: {instance.credential.username}",
                    "solution": "请检查数据库凭据中的用户名和密码是否正确",
                    "error_type": "authentication_failed",
                }
            elif "ORA-12541" in error_msg:
                return {
                    "success": False,
                    "error": "Oracle服务未运行",
                    "details": f"无法连接到 {instance.host}:{instance.port}，TNS监听器未启动",
                    "solution": "请确保Oracle数据库服务正在运行，并检查端口号是否正确",
                    "error_type": "connection_refused",
                }
            elif "ORA-12514" in error_msg:
                return {
                    "success": False,
                    "error": "Oracle服务名不存在",
                    "details": f'服务名 "{instance.database_name or "ORCL"}" 不存在',
                    "solution": "请检查服务名是否正确，或使用正确的服务名",
                    "error_type": "service_not_found",
                }
            elif "ORA-12545" in error_msg:
                return {
                    "success": False,
                    "error": "Oracle连接失败",
                    "details": f"目标主机或对象不存在: {instance.host}:{instance.port}",
                    "solution": "请检查主机地址和端口号是否正确，确保Oracle服务正在运行",
                    "error_type": "host_not_found",
                }
            else:
                return {
                    "success": False,
                    "error": "Oracle数据库错误",
                    "details": error_msg,
                    "solution": "请检查Oracle数据库配置和日志",
                    "error_type": "oracle_error",
                }
        except oracledb.Error as e:
            return {
                "success": False,
                "error": "Oracle连接失败",
                "details": str(e),
                "solution": "请检查网络连接和Oracle服务配置",
                "error_type": "oracledb_error",
            }
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__

            # 添加详细的调试信息
            debug_info = f"错误类型: {error_type}, 错误信息: {error_msg}"

            return {
                "success": False,
                "error": "Oracle连接失败",
                "details": f"{error_msg} (调试信息: {debug_info})",
                "solution": "请检查所有连接参数和服务器状态，确保Oracle Instant Client已正确安装",
                "error_type": "unknown_error",
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
            if instance.db_type == "mysql":
                conn = self._get_mysql_connection(instance)
            elif instance.db_type == "postgresql":
                conn = self._get_postgresql_connection(instance)
            elif instance.db_type == "sqlserver":
                conn = self._get_sqlserver_connection(instance)
            elif instance.db_type == "oracle":
                conn = self._get_oracle_connection(instance)
            else:
                log_error(f"不支持的数据库类型: {instance.db_type}")
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

    def _get_mysql_connection(self, instance: Instance) -> Optional[Any]:
        """获取MySQL连接"""
        try:
            # 获取原始密码
            password = (
                instance.credential.get_plain_password() if instance.credential else ""
            )

            conn = pymysql.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name,
                user=instance.credential.username if instance.credential else "",
                password=password,
                charset="utf8mb4",
                autocommit=True,
                connect_timeout=30,  # 连接超时30秒
                read_timeout=60,  # 读取超时60秒
                write_timeout=60,  # 写入超时60秒
                sql_mode="TRADITIONAL",
            )
            return conn
        except Exception as e:
            log_error(e, context={"instance_id": instance.id, "db_type": "MySQL"})
            return None

    def _get_postgresql_connection(self, instance: Instance) -> Optional[Any]:
        """获取PostgreSQL连接"""
        try:
            import psycopg

            password = (
                instance.credential.get_plain_password() if instance.credential else ""
            )
            conn = psycop.connect(
                host=instance.host,
                port=instance.port,
                database="postgres",  # PostgreSQL默认数据库
                user=instance.credential.username if instance.credential else "",
                password=password,
                connect_timeout=30,
            )
            return conn
        except Exception as e:
            log_error(e, context={"instance_id": instance.id, "db_type": "PostgreSQL"})
            return None

    def _get_sqlserver_connection(self, instance: Instance) -> Optional[Any]:
        """获取SQL Server连接"""
        try:
            import pymssql

            password = (
                instance.credential.get_plain_password() if instance.credential else ""
            )
            conn = pymssql.connect(
                server=instance.host,
                port=instance.port,
                database=instance.database_name or "master",
                user=instance.credential.username if instance.credential else "",
                password=password,
                timeout=30,
            )
            return conn
        except Exception as e:
            log_error(e, context={"instance_id": instance.id, "db_type": "SQL Server"})
            return None

    def _get_oracle_connection(self, instance: Instance) -> Optional[Any]:
        """获取Oracle连接"""
        try:
            import oracledb

            # 构建连接字符串
            database_name = instance.database_name or "ORCL"

            # 优先使用服务名格式，因为大多数现代Oracle配置都使用服务名
            # 如果包含点号(.)，则认为是Service Name，否则也尝试服务名格式
            if "." in database_name:
                # Service Name格式: host:port/service_name
                dsn = f"{instance.host}:{instance.port}/{database_name}"
            else:
                # 对于简单名称，优先尝试服务名格式，如果失败再尝试SID格式
                dsn = f"{instance.host}:{instance.port}/{database_name}"
            password = (
                instance.credential.get_plain_password() if instance.credential else ""
            )

            # 优先使用Thick模式连接（适用于所有Oracle版本，包括11g）
            try:
                # 初始化Thick模式（需要Oracle Instant Client）
                oracledb.init_oracle_client()
                conn = oracledb.connect(
                    user=instance.credential.username if instance.credential else "",
                    password=password,
                    dsn=dsn,
                )
                return conn
            except oracledb.DatabaseError as e:
                # 如果Thick模式失败，尝试Thin模式（适用于Oracle 12c+）
                if "DPI-1047" in str(e) or "Oracle Client library" in str(e):
                    # Thick模式失败，尝试Thin模式
                    try:
                        conn = oracledb.connect(
                            user=(
                                instance.credential.username
                                if instance.credential
                                else ""
                            ),
                            password=password,
                            dsn=dsn,
                        )
                        return conn
                    except oracledb.DatabaseError as thin_error:
                        # 如果Thin模式也失败，尝试SID格式（如果当前是服务名格式）
                        if (
                            not dsn.endswith(f":{database_name}")
                            and not "." in database_name
                        ):
                            try:
                                sid_dsn = (
                                    f"{instance.host}:{instance.port}:{database_name}"
                                )
                                conn = oracledb.connect(
                                    user=(
                                        instance.credential.username
                                        if instance.credential
                                        else ""
                                    ),
                                    password=password,
                                    dsn=sid_dsn,
                                )
                                return conn
                            except oracledb.DatabaseError as sid_error:
                                # 如果SID格式也失败，抛出原始错误
                                raise e
                        else:
                            raise e
                else:
                    # 如果不是驱动问题，尝试SID格式（如果当前是服务名格式）
                    if (
                        not dsn.endswith(f":{database_name}")
                        and not "." in database_name
                    ):
                        try:
                            sid_dsn = f"{instance.host}:{instance.port}:{database_name}"
                            conn = oracledb.connect(
                                user=(
                                    instance.credential.username
                                    if instance.credential
                                    else ""
                                ),
                                password=password,
                                dsn=sid_dsn,
                            )
                            return conn
                        except oracledb.DatabaseError as sid_error:
                            # 如果SID格式也失败，抛出原始错误
                            raise e
                    else:
                        raise
        except Exception as e:
            log_error(e, context={"instance_id": instance.id, "db_type": "Oracle"})
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
            if instance.db_type == "mysql":
                return self._get_mysql_permissions(instance, account)
            elif instance.db_type == "postgresql":
                return self._get_postgresql_permissions(instance, account)
            elif instance.db_type == "sqlserver":
                return self._get_sqlserver_permissions(instance, account)
            elif instance.db_type == "oracle":
                return self._get_oracle_permissions(instance, account)
            else:
                return {
                    "global": [],
                    "database": [],
                    "error": f"暂不支持 {instance.db_type} 数据库的权限查询",
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
