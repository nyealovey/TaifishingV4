"""
泰摸鱼吧 - 基础同步管理器抽象类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Tuple

from app import db
from app.models.current_account_sync_data import CurrentAccountSyncData
from app.models.account_change_log import AccountChangeLog
from app.utils.structlog_config import get_sync_logger
from app.utils import time_utils


class BaseSyncManager(ABC):
    """基础同步管理器抽象类"""

    def __init__(self):
        self.sync_logger = get_sync_logger()

    @abstractmethod
    def get_db_type(self) -> str:
        """获取数据库类型"""
        pass

    @abstractmethod
    def get_accounts(self, conn) -> List[Dict[str, Any]]:
        """获取账户信息"""
        pass

    @abstractmethod
    def get_user_permissions(self, conn, username: str) -> Dict[str, Any]:
        """获取用户权限信息"""
        pass

    @abstractmethod
    def create_account(self, instance_id: int, username: str, permissions_data: Dict[str, Any], 
                      is_superuser: bool, session_id: str = None) -> CurrentAccountSyncData:
        """创建新账户"""
        pass

    @abstractmethod
    def update_account(self, account: CurrentAccountSyncData, permissions_data: Dict[str, Any], 
                      is_superuser: bool) -> None:
        """更新账户权限"""
        pass

    @abstractmethod
    def detect_changes(self, account: CurrentAccountSyncData, new_permissions: Dict[str, Any]) -> Dict[str, Any]:
        """检测权限变更"""
        pass

    @abstractmethod
    def validate_permissions_data(self, permissions_data: Dict[str, Any], username: str) -> bool:
        """验证权限数据完整性"""
        pass

    def sync_accounts(self, instance, conn, session_id: str) -> Dict[str, Any]:
        """同步账户信息 - 通用流程"""
        try:
            db_type = self.get_db_type()
            self.sync_logger.info(f"开始同步{db_type}账户", instance_name=instance.name)

            # 获取账户信息
            accounts = self.get_accounts(conn)
            
            # 创建当前同步账户的用户名集合
            current_usernames = {account_data["username"] for account_data in accounts}
            
            synced_count = 0
            added_count = 0
            modified_count = 0

            # 处理现有账户
            for account_data in accounts:
                try:
                    # 验证权限数据
                    if not self.validate_permissions_data(
                        account_data["permissions"], 
                        account_data["username"]
                    ):
                        self.sync_logger.warning(
                            f"跳过权限数据无效的账户: {account_data['username']}"
                        )
                        continue

                    # 使用upsert_account方法
                    account = self.upsert_account(
                        instance_id=instance.id,
                        username=account_data["username"],
                        permissions_data=account_data["permissions"],
                        is_superuser=account_data.get("is_superuser", False),
                        session_id=session_id,
                    )
                    synced_count += 1
                    if account.last_change_type == "add":
                        added_count += 1
                    elif account.last_change_type == "modify_privilege":
                        modified_count += 1
                except Exception as e:
                    self.sync_logger.error(f"同步{db_type}账户失败: {account_data['username']}", error=str(e))

            # 处理软删除
            removed_count = self._mark_deleted_accounts(instance.id, current_usernames, session_id)

            # 统一提交所有更改（不在循环中提交）
            db.session.commit()

            return {
                "success": True,
                "synced_count": synced_count,
                "added_count": added_count,
                "modified_count": modified_count,
                "removed_count": removed_count,
            }
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(f"{self.get_db_type()}账户同步失败", error=str(e))
            return {"success": False, "error": str(e)}

    def upsert_account(self, instance_id: int, username: str, permissions_data: Dict[str, Any],
                      is_superuser: bool = False, session_id: str = None) -> CurrentAccountSyncData:
        """根据数据库类型更新或创建账户"""
        account = self.get_account_latest(instance_id, username, include_deleted=True)

        if account:
            # 重置删除状态
            if account.is_deleted:
                account.is_deleted = False
                account.last_change_type = "restore"
                account.last_change_time = time_utils.now()
                account.last_sync_time = time_utils.now()
            
            # 检查权限变更
            changes = self.detect_changes(account, permissions_data)
            if changes:
                self._log_changes(instance_id, username, changes, session_id)
                self.update_account(account, permissions_data, is_superuser)
            return account

        # 创建新账户
        account = self.create_account(instance_id, username, permissions_data, is_superuser, session_id)
        db.session.add(account)
        return account

    def get_account_latest(self, instance_id: int, username: str = None, 
                          include_deleted: bool = False) -> CurrentAccountSyncData | None:
        """获取账户最新状态"""
        query = CurrentAccountSyncData.query.filter_by(
            instance_id=instance_id, 
            db_type=self.get_db_type()
        )
        if username:
            query = query.filter_by(username=username)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        # 按同步时间降序排序，确保返回最新的记录
        return query.order_by(CurrentAccountSyncData.sync_time.desc()).first()

    def get_accounts_by_instance(self, instance_id: int, 
                                include_deleted: bool = False) -> List[CurrentAccountSyncData]:
        """获取实例的所有账户"""
        query = CurrentAccountSyncData.query.filter_by(
            instance_id=instance_id,
            db_type=self.get_db_type()
        )
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.order_by(CurrentAccountSyncData.username.asc()).all()

    def get_account_changes(self, instance_id: int, username: str) -> List[AccountChangeLog]:
        """获取账户变更历史"""
        return (
            AccountChangeLog.query.filter_by(
                instance_id=instance_id, 
                db_type=self.get_db_type(), 
                username=username
            )
            .order_by(AccountChangeLog.change_time.desc())
            .all()
        )

    def _mark_deleted_accounts(self, instance_id: int, current_usernames: Set[str], 
                              session_id: str) -> int:
        """标记已删除的账户"""
        # 获取当前数据库中存在的所有账户
        existing_accounts = CurrentAccountSyncData.query.filter_by(
            instance_id=instance_id,
            db_type=self.get_db_type(),
            is_deleted=False
        ).all()

        removed_count = 0
        for account in existing_accounts:
            if account.username not in current_usernames:
                # 标记为已删除
                account.is_deleted = True
                account.deleted_time = time_utils.now()
                account.last_change_type = "delete"
                account.last_change_time = time_utils.now()
                account.last_sync_time = time_utils.now()
                account.session_id = session_id
                removed_count += 1

                self.sync_logger.info(
                    f"标记账户为已删除: {account.username}",
                    instance_id=instance_id,
                    db_type=self.get_db_type()
                )

        return removed_count

    def _log_changes(self, instance_id: int, username: str, changes: Dict[str, Any], 
                    session_id: str = None) -> None:
        """记录权限变更日志"""
        try:
            change_log = AccountChangeLog(
                instance_id=instance_id,
                db_type=self.get_db_type(),
                username=username,
                change_type="modify_privilege",
                changes=changes,
                session_id=session_id,
            )
            db.session.add(change_log)
            
            self.sync_logger.info(
                f"记录权限变更: {username}",
                instance_id=instance_id,
                db_type=self.get_db_type(),
                changes=changes
            )
        except Exception as e:
            self.sync_logger.error(f"记录权限变更失败: {username}", error=str(e))
