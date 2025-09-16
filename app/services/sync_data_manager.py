"""
泰摸鱼吧 - 同步数据管理器（重构版本）

这是一个兼容性文件，重新导出新的同步管理器模块
原始功能已拆分到 app/services/sync/ 模块中
"""

# 重新导出所有同步管理器，保持向后兼容
from .sync import (
    BaseSyncManager,
    MySQLSyncManager,
    PostgreSQLSyncManager,
    SQLServerSyncManager,
    OracleSyncManager,
    SyncManagerFactory,
    SyncDataManager,
)

# 保持原有的导出接口
__all__ = [
    "SyncDataManager",
    "SyncManagerFactory",
    "BaseSyncManager",
    "MySQLSyncManager",
    "PostgreSQLSyncManager", 
    "SQLServerSyncManager",
    "OracleSyncManager",
]
