"""
泰摸鱼吧 - 账户同步服务
委托给统一同步服务处理
"""

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
from app.utils.structlog_config import get_sync_logger
from app.utils.timezone import now


class AccountSyncService:
    """账户同步服务 - 委托给统一同步服务"""

    def __init__(self) -> None:
        self.sync_logger = get_sync_logger()

    def sync_accounts(self, instance: Instance, sync_type: str = "batch", session_id: str = None) -> dict[str, Any]:
        """
        同步账户信息 - 委托给统一同步服务

        Args:
            instance: 数据库实例
            sync_type: 同步类型 ('manual_single', 'manual_batch', 'manual_task', 'scheduled_task')
            session_id: 同步会话ID（可选）

        Returns:
            Dict: 同步结果
        """
        from app.services.unified_sync_service import unified_sync_service
        
        return unified_sync_service.sync_accounts(
            instance=instance,
            sync_type=sync_type,
            session_id=session_id,
            create_sync_report=True  # 批量同步创建报告
        )


# 创建全局实例，便于其他模块使用
account_sync_service = AccountSyncService()