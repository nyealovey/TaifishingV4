"""
泰摸鱼吧 - 统一同步数据管理器
"""

from datetime import datetime

from app import db
from app.models.account_change_log import AccountChangeLog
from app.models.current_account_sync_data import CurrentAccountSyncData
from app.utils.structlog_config import get_sync_logger


class SyncDataManager:
    """统一同步数据管理器"""

    def __init__(self):
        self.sync_logger = get_sync_logger()

    @classmethod
    def get_account_latest(
        cls, db_type: str, instance_id: int, username: str = None, include_deleted: bool = False
    ) -> CurrentAccountSyncData | None:
        """获取账户最新状态"""
        query = CurrentAccountSyncData.query.filter_by(instance_id=instance_id, db_type=db_type)
        if username:
            query = query.filter_by(username=username)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.first()

    @classmethod
    def get_accounts_by_instance(cls, instance_id: int, include_deleted: bool = False) -> list[CurrentAccountSyncData]:
        """获取实例的所有账户"""
        query = CurrentAccountSyncData.query.filter_by(instance_id=instance_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.all()

    @classmethod
    def get_account_changes(cls, instance_id: int, db_type: str, username: str) -> list[AccountChangeLog]:
        """获取账户变更历史"""
        return (
            AccountChangeLog.query.filter_by(instance_id=instance_id, db_type=db_type, username=username)
            .order_by(AccountChangeLog.change_time.desc())
            .all()
        )

    @classmethod
    def upsert_account(
        cls,
        instance_id: int,
        db_type: str,
        username: str,
        permissions_data: dict,
        is_superuser: bool = False,
        session_id: str = None,
    ) -> CurrentAccountSyncData:
        """根据数据库类型更新账户权限"""

        if db_type == "mysql":
            return cls._upsert_mysql_account(instance_id, username, permissions_data, is_superuser, session_id)
        if db_type == "postgresql":
            return cls._upsert_postgresql_account(instance_id, username, permissions_data, is_superuser, session_id)
        if db_type == "sqlserver":
            return cls._upsert_sqlserver_account(instance_id, username, permissions_data, is_superuser, session_id)
        if db_type == "oracle":
            return cls._upsert_oracle_account(instance_id, username, permissions_data, is_superuser, session_id)
        raise ValueError(f"不支持的数据库类型: {db_type}")

    @classmethod
    def _upsert_mysql_account(
        cls, instance_id: int, username: str, permissions_data: dict, is_superuser: bool, session_id: str = None
    ) -> CurrentAccountSyncData:
        """更新MySQL账户权限"""
        account = cls.get_account_latest("mysql", instance_id, username, include_deleted=True)

        if account:
            # 检查权限变更
            changes = cls._detect_mysql_changes(account, permissions_data)
            if changes:
                cls._log_changes(instance_id, "mysql", username, changes, session_id)
                cls._update_mysql_account(account, permissions_data, is_superuser)
            return account
        # 创建新账户
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
        db.session.add(account)
        db.session.commit()
        return account

    @classmethod
    def _upsert_postgresql_account(
        cls, instance_id: int, username: str, permissions_data: dict, is_superuser: bool, session_id: str = None
    ) -> CurrentAccountSyncData:
        """更新PostgreSQL账户权限"""
        account = cls.get_account_latest("postgresql", instance_id, username, include_deleted=True)

        if account:
            # 检查权限变更
            changes = cls._detect_postgresql_changes(account, permissions_data)
            if changes:
                cls._log_changes(instance_id, "postgresql", username, changes, session_id)
                cls._update_postgresql_account(account, permissions_data, is_superuser)
            return account
        # 创建新账户
        account = CurrentAccountSyncData(
            instance_id=instance_id,
            db_type="postgresql",
            username=username,
            predefined_roles=permissions_data.get("predefined_roles", []),
            role_attributes=permissions_data.get("role_attributes", []),
            database_privileges_pg=permissions_data.get("database_privileges", {}),
            tablespace_privileges=permissions_data.get("tablespace_privileges", []),
            type_specific=permissions_data.get("type_specific", {}),
            is_superuser=is_superuser,
            last_change_type="add",
            session_id=session_id,
        )
        db.session.add(account)
        db.session.commit()
        return account

    @classmethod
    def _upsert_sqlserver_account(
        cls, instance_id: int, username: str, permissions_data: dict, is_superuser: bool, session_id: str = None
    ) -> CurrentAccountSyncData:
        """更新SQL Server账户权限"""
        account = cls.get_account_latest("sqlserver", instance_id, username, include_deleted=True)

        if account:
            # 检查权限变更
            changes = cls._detect_sqlserver_changes(account, permissions_data)
            if changes:
                cls._log_changes(instance_id, "sqlserver", username, changes, session_id)
                cls._update_sqlserver_account(account, permissions_data, is_superuser)
            return account
        # 创建新账户
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
        db.session.add(account)
        db.session.commit()
        return account

    @classmethod
    def _upsert_oracle_account(
        cls, instance_id: int, username: str, permissions_data: dict, is_superuser: bool, session_id: str = None
    ) -> CurrentAccountSyncData:
        """更新Oracle账户权限（移除表空间配额）"""
        account = cls.get_account_latest("oracle", instance_id, username, include_deleted=True)

        if account:
            # 检查权限变更
            changes = cls._detect_oracle_changes(account, permissions_data)
            if changes:
                cls._log_changes(instance_id, "oracle", username, changes, session_id)
                cls._update_oracle_account(account, permissions_data, is_superuser)
            return account
        # 创建新账户
        account = CurrentAccountSyncData(
            instance_id=instance_id,
            db_type="oracle",
            username=username,
            oracle_roles=permissions_data.get("roles", []),
            system_privileges=permissions_data.get("system_privileges", []),
            tablespace_privileges_oracle=permissions_data.get("tablespace_privileges", []),
            type_specific=permissions_data.get("type_specific", {}),
            is_superuser=is_superuser,
            last_change_type="add",
            session_id=session_id,
        )
        db.session.add(account)
        db.session.commit()
        return account

    @classmethod
    def _detect_mysql_changes(cls, account: CurrentAccountSyncData, new_permissions: dict) -> dict:
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
                    k: v for k, v in new_db_perms.items() if k not in old_db_perms or set(old_db_perms[k]) != set(v)
                },
                "removed": {
                    k: v
                    for k, v in old_db_perms.items()
                    if k not in new_db_perms or set(new_db_perms.get(k, [])) != set(v)
                },
            }

        return changes

    @classmethod
    def _detect_postgresql_changes(cls, account: CurrentAccountSyncData, new_permissions: dict) -> dict:
        """检测PostgreSQL权限变更"""
        changes = {}

        # 检测预定义角色变更
        old_roles = set(account.predefined_roles or [])
        new_roles = set(new_permissions.get("predefined_roles", []))
        if old_roles != new_roles:
            changes["predefined_roles"] = {"added": list(new_roles - old_roles), "removed": list(old_roles - new_roles)}

        # 检测角色属性变更
        old_attrs = set(account.role_attributes or [])
        new_attrs = set(new_permissions.get("role_attributes", []))
        if old_attrs != new_attrs:
            changes["role_attributes"] = {"added": list(new_attrs - old_attrs), "removed": list(old_attrs - new_attrs)}

        # 检测数据库权限变更
        old_db_perms = account.database_privileges_pg or {}
        new_db_perms = new_permissions.get("database_privileges", {})
        if old_db_perms != new_db_perms:
            changes["database_privileges"] = {
                "added": {
                    k: v for k, v in new_db_perms.items() if k not in old_db_perms or set(old_db_perms[k]) != set(v)
                },
                "removed": {
                    k: v
                    for k, v in old_db_perms.items()
                    if k not in new_db_perms or set(new_db_perms.get(k, [])) != set(v)
                },
            }

        return changes

    @classmethod
    def _detect_sqlserver_changes(cls, account: CurrentAccountSyncData, new_permissions: dict) -> dict:
        """检测SQL Server权限变更"""
        changes = {}

        # 检测服务器角色变更
        old_roles = set(account.server_roles or [])
        new_roles = set(new_permissions.get("server_roles", []))
        if old_roles != new_roles:
            changes["server_roles"] = {"added": list(new_roles - old_roles), "removed": list(old_roles - new_roles)}

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
                    k: v for k, v in new_db_roles.items() if k not in old_db_roles or set(old_db_roles[k]) != set(v)
                },
                "removed": {
                    k: v
                    for k, v in old_db_roles.items()
                    if k not in new_db_roles or set(new_db_roles.get(k, [])) != set(v)
                },
            }

        # 检测数据库权限变更
        old_db_perms = account.database_permissions or {}
        new_db_perms = new_permissions.get("database_permissions", {})
        if old_db_perms != new_db_perms:
            changes["database_permissions"] = {
                "added": {
                    k: v for k, v in new_db_perms.items() if k not in old_db_perms or set(old_db_perms[k]) != set(v)
                },
                "removed": {
                    k: v
                    for k, v in old_db_perms.items()
                    if k not in new_db_perms or set(new_db_perms.get(k, [])) != set(v)
                },
            }

        return changes

    @classmethod
    def _detect_oracle_changes(cls, account: CurrentAccountSyncData, new_permissions: dict) -> dict:
        """检测Oracle权限变更（移除表空间配额检测）"""
        changes = {}

        # 检测角色变更
        old_roles = set(account.oracle_roles or [])
        new_roles = set(new_permissions.get("roles", []))
        if old_roles != new_roles:
            changes["roles"] = {"added": list(new_roles - old_roles), "removed": list(old_roles - new_roles)}

        # 检测系统权限变更
        old_system_perms = set(account.system_privileges or [])
        new_system_perms = set(new_permissions.get("system_privileges", []))
        if old_system_perms != new_system_perms:
            changes["system_privileges"] = {
                "added": list(new_system_perms - old_system_perms),
                "removed": list(old_system_perms - new_system_perms),
            }

        # 检测表空间权限变更（移除表空间配额）
        old_tablespace_perms = set(account.tablespace_privileges_oracle or [])
        new_tablespace_perms = set(new_permissions.get("tablespace_privileges", []))
        if old_tablespace_perms != new_tablespace_perms:
            changes["tablespace_privileges"] = {
                "added": list(new_tablespace_perms - old_tablespace_perms),
                "removed": list(old_tablespace_perms - new_tablespace_perms),
            }

        return changes

    @classmethod
    def _update_mysql_account(cls, account: CurrentAccountSyncData, permissions_data: dict, is_superuser: bool):
        """更新MySQL账户数据"""
        account.global_privileges = permissions_data.get("global_privileges", [])
        account.database_privileges = permissions_data.get("database_privileges", {})
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.last_change_type = "modify_privilege"
        account.last_change_time = datetime.utcnow()
        account.last_sync_time = datetime.utcnow()
        db.session.commit()

    @classmethod
    def _update_postgresql_account(cls, account: CurrentAccountSyncData, permissions_data: dict, is_superuser: bool):
        """更新PostgreSQL账户数据"""
        account.predefined_roles = permissions_data.get("predefined_roles", [])
        account.role_attributes = permissions_data.get("role_attributes", [])
        account.database_privileges_pg = permissions_data.get("database_privileges", {})
        account.tablespace_privileges = permissions_data.get("tablespace_privileges", [])
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.last_change_type = "modify_privilege"
        account.last_change_time = datetime.utcnow()
        account.last_sync_time = datetime.utcnow()
        db.session.commit()

    @classmethod
    def _update_sqlserver_account(cls, account: CurrentAccountSyncData, permissions_data: dict, is_superuser: bool):
        """更新SQL Server账户数据"""
        account.server_roles = permissions_data.get("server_roles", [])
        account.server_permissions = permissions_data.get("server_permissions", [])
        account.database_roles = permissions_data.get("database_roles", {})
        account.database_permissions = permissions_data.get("database_permissions", {})
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.last_change_type = "modify_privilege"
        account.last_change_time = datetime.utcnow()
        account.last_sync_time = datetime.utcnow()
        db.session.commit()

    @classmethod
    def _update_oracle_account(cls, account: CurrentAccountSyncData, permissions_data: dict, is_superuser: bool):
        """更新Oracle账户数据"""
        account.oracle_roles = permissions_data.get("roles", [])
        account.system_privileges = permissions_data.get("system_privileges", [])
        account.tablespace_privileges_oracle = permissions_data.get("tablespace_privileges", [])
        account.type_specific = permissions_data.get("type_specific", {})
        account.is_superuser = is_superuser
        account.last_change_type = "modify_privilege"
        account.last_change_time = datetime.utcnow()
        account.last_sync_time = datetime.utcnow()
        db.session.commit()

    @classmethod
    def _log_changes(cls, instance_id: int, db_type: str, username: str, changes: dict, session_id: str = None):
        """记录权限变更日志"""
        change_log = AccountChangeLog(
            instance_id=instance_id,
            db_type=db_type,
            username=username,
            change_type="modify_privilege",
            session_id=session_id,
            privilege_diff=changes,
            status="success",
        )
        db.session.add(change_log)
        db.session.commit()

    @classmethod
    def mark_account_deleted(cls, instance_id: int, db_type: str, username: str, session_id: str = None):
        """标记账户为已删除（不支持恢复）"""
        account = cls.get_account_latest(db_type, instance_id, username, include_deleted=True)
        if account and not account.is_deleted:
            account.is_deleted = True
            account.deleted_time = datetime.utcnow()
            account.last_change_type = "delete"
            account.last_change_time = datetime.utcnow()

            # 记录删除日志
            change_log = AccountChangeLog(
                instance_id=instance_id,
                db_type=db_type,
                username=username,
                change_type="delete",
                session_id=session_id,
                status="success",
            )
            db.session.add(change_log)
            db.session.commit()

    @classmethod
    def get_accounts_by_db_type(cls, db_type: str, include_deleted: bool = False) -> list[CurrentAccountSyncData]:
        """根据数据库类型获取账户列表"""
        query = CurrentAccountSyncData.query.filter_by(db_type=db_type)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.all()

    @classmethod
    def get_accounts_by_instance_and_db_type(
        cls, instance_id: int, db_type: str, include_deleted: bool = False
    ) -> list[CurrentAccountSyncData]:
        """根据实例ID和数据库类型获取账户列表"""
        query = CurrentAccountSyncData.query.filter_by(instance_id=instance_id, db_type=db_type)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.all()
