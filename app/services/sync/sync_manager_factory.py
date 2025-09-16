"""
泰摸鱼吧 - 同步管理器工厂
"""

from typing import Dict, Type

from .base_sync_manager import BaseSyncManager
from .mysql_sync_manager import MySQLSyncManager
from .postgresql_sync_manager import PostgreSQLSyncManager
from .sqlserver_sync_manager import SQLServerSyncManager
from .oracle_sync_manager import OracleSyncManager


class SyncManagerFactory:
    """同步管理器工厂"""

    _managers: Dict[str, Type[BaseSyncManager]] = {
        "mysql": MySQLSyncManager,
        "postgresql": PostgreSQLSyncManager,
        "sqlserver": SQLServerSyncManager,
        "oracle": OracleSyncManager,
    }

    @classmethod
    def get_manager(cls, db_type: str) -> BaseSyncManager:
        """
        根据数据库类型获取对应的同步管理器
        
        Args:
            db_type: 数据库类型 (mysql, postgresql, sqlserver, oracle)
            
        Returns:
            BaseSyncManager: 对应的同步管理器实例
            
        Raises:
            ValueError: 不支持的数据库类型
        """
        if db_type not in cls._managers:
            raise ValueError(f"不支持的数据库类型: {db_type}。支持的类型: {list(cls._managers.keys())}")
        
        manager_class = cls._managers[db_type]
        return manager_class()

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """获取支持的数据库类型列表"""
        return list(cls._managers.keys())

    @classmethod
    def register_manager(cls, db_type: str, manager_class: Type[BaseSyncManager]) -> None:
        """
        注册新的同步管理器
        
        Args:
            db_type: 数据库类型
            manager_class: 同步管理器类
        """
        cls._managers[db_type] = manager_class

    @classmethod
    def is_supported(cls, db_type: str) -> bool:
        """检查是否支持指定的数据库类型"""
        return db_type in cls._managers


# 主同步数据管理器（重构版本）
class SyncDataManager:
    """
    统一同步数据管理器（重构版本）
    
    使用工厂模式，根据数据库类型获取对应的同步管理器
    """

    def __init__(self):
        """初始化同步数据管理器"""
        pass

    def sync_accounts(self, instance, conn, session_id: str, db_type: str = None) -> Dict[str, any]:
        """
        同步账户信息 - 统一入口
        
        Args:
            instance: 数据库实例
            conn: 数据库连接
            session_id: 同步会话ID
            db_type: 数据库类型（可选，从instance.db_type获取）
            
        Returns:
            Dict: 同步结果
        """
        # 获取数据库类型
        if not db_type:
            db_type = instance.db_type
            
        # 获取对应的同步管理器
        try:
            sync_manager = SyncManagerFactory.get_manager(db_type)
            return sync_manager.sync_accounts(instance, conn, session_id)
        except ValueError as e:
            return {"success": False, "error": str(e)}

    # 兼容性方法，保持向后兼容
    def sync_mysql_accounts(self, instance, conn, session_id: str) -> Dict[str, any]:
        """同步MySQL账户（兼容性方法）"""
        return self.sync_accounts(instance, conn, session_id, "mysql")

    def sync_postgresql_accounts(self, instance, conn, session_id: str) -> Dict[str, any]:
        """同步PostgreSQL账户（兼容性方法）"""
        return self.sync_accounts(instance, conn, session_id, "postgresql")

    def sync_sqlserver_accounts(self, instance, conn, session_id: str) -> Dict[str, any]:
        """同步SQL Server账户（兼容性方法）"""
        return self.sync_accounts(instance, conn, session_id, "sqlserver")

    def sync_oracle_accounts(self, instance, conn, session_id: str) -> Dict[str, any]:
        """同步Oracle账户（兼容性方法）"""
        return self.sync_accounts(instance, conn, session_id, "oracle")

    # 静态方法，保持向后兼容
    @staticmethod
    def get_account_latest(db_type: str, instance_id: int, username: str = None, 
                          include_deleted: bool = False):
        """获取账户最新状态（静态方法）"""
        try:
            sync_manager = SyncManagerFactory.get_manager(db_type)
            return sync_manager.get_account_latest(instance_id, username, include_deleted)
        except ValueError:
            return None

    @staticmethod
    def get_accounts_by_instance(instance_id: int, include_deleted: bool = False):
        """获取实例的所有账户（静态方法）"""
        from app.models.current_account_sync_data import CurrentAccountSyncData
        
        query = CurrentAccountSyncData.query.filter_by(instance_id=instance_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.order_by(CurrentAccountSyncData.username.asc()).all()

    @staticmethod
    def get_accounts_by_instance_and_db_type(instance_id: int, db_type: str, 
                                           include_deleted: bool = False):
        """获取实例指定数据库类型的账户（静态方法）"""
        try:
            sync_manager = SyncManagerFactory.get_manager(db_type)
            return sync_manager.get_accounts_by_instance(instance_id, include_deleted)
        except ValueError:
            return []

    @staticmethod
    def get_account_changes(instance_id: int, db_type: str, username: str):
        """获取账户变更历史（静态方法）"""
        try:
            sync_manager = SyncManagerFactory.get_manager(db_type)
            return sync_manager.get_account_changes(instance_id, username)
        except ValueError:
            return []

    @staticmethod
    def upsert_account(instance_id: int, db_type: str, username: str, permissions_data: Dict[str, any],
                      is_superuser: bool = False, session_id: str = None):
        """更新或创建账户（静态方法）"""
        try:
            sync_manager = SyncManagerFactory.get_manager(db_type)
            return sync_manager.upsert_account(instance_id, username, permissions_data, is_superuser, session_id)
        except ValueError as e:
            raise ValueError(f"不支持的数据库类型: {db_type}") from e
