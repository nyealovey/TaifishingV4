"""
泰摸鱼吧 - 统一同步服务
合并 DatabaseService 和 AccountSyncService 的同步功能
"""

import uuid
from typing import Any, Dict, Optional

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

from app import db
from app.models import Instance
from app.services.sync_data_manager import SyncDataManager
from app.services.database_service import DatabaseService
from app.utils.structlog_config import get_sync_logger, get_db_logger
from app.utils.timezone import now


class UnifiedSyncService:
    """统一同步服务 - 处理单一实例和批量同步"""

    def __init__(self):
        self.sync_logger = get_sync_logger()
        self.db_logger = get_db_logger()
        self.database_service = DatabaseService()

    def sync_accounts(
        self, 
        instance: Instance, 
        sync_type: str = "manual_single", 
        session_id: Optional[str] = None,
        create_sync_report: bool = None
    ) -> Dict[str, Any]:
        """
        统一账户同步接口
        
        Args:
            instance: 数据库实例
            sync_type: 同步类型
                - 'manual_single': 手动单一实例同步（不创建会话记录）
                - 'manual_batch': 手动批量同步（创建会话记录）
                - 'manual_task': 手动任务同步（创建会话记录）
                - 'scheduled_task': 定时任务同步（创建会话记录）
            session_id: 同步会话ID（可选，如果不提供则自动生成）
            create_sync_report: 是否创建同步报告（可选，根据sync_type自动判断）
            
        Returns:
            Dict: 同步结果
        """
        try:
            # 根据同步类型决定是否创建同步报告
            if create_sync_report is None:
                create_sync_report = sync_type in ["manual_batch", "manual_task", "scheduled_task"]

            self.sync_logger.info(
                "开始账户同步",
                module="unified_sync",
                instance_name=instance.name,
                db_type=instance.db_type,
                sync_type=sync_type,
                session_id=session_id,
                create_sync_report=create_sync_report,
            )

            # 获取数据库连接
            conn = self._get_connection(instance)
            if not conn:
                error_msg = "无法获取数据库连接"
                self.sync_logger.error(
                    "无法获取数据库连接",
                    module="unified_sync",
                    instance_name=instance.name,
                    db_type=instance.db_type,
                )
                return {"success": False, "error": error_msg}

            # 更新数据库版本信息
            self._update_database_version(instance, conn)

            # 生成会话ID（如果未提供）
            if not session_id:
                session_id = str(uuid.uuid4())

            # 记录同步前的账户数量
            before_count = self._get_account_count(instance) if create_sync_report else 0

            # 执行同步
            sync_manager = SyncDataManager()
            result = self._execute_sync_by_db_type(sync_manager, instance, conn, session_id)

            if not result.get("success"):
                return result

            # 更新实例的最后连接时间
            instance.last_connected_at = now()
            
            # 单一实例同步时增加同步次数
            if sync_type == "manual_single":
                instance.sync_count = (instance.sync_count or 0) + 1
            
            db.session.commit()

            # 关闭连接
            self.database_service.close_connection(instance)

            # 创建同步报告（仅批量同步）
            if create_sync_report:
                self._create_sync_report(
                    instance, session_id, sync_type, 
                    before_count, result
                )

            # 记录同步完成日志
            self._log_sync_completion(instance, result)

            return {
                "success": True,
                "message": f"成功同步 {result.get('synced_count', 0)} 个账户",
                "synced_count": result.get("synced_count", 0),
                "added_count": result.get("added_count", 0),
                "removed_count": result.get("removed_count", 0),
                "modified_count": result.get("modified_count", 0),
                "session_id": session_id,
            }

        except Exception as e:
            error_msg = f"账户同步失败: {str(e)}"
            self.sync_logger.error(
                "账户同步异常",
                module="unified_sync",
                instance_name=instance.name,
                error=str(e),
                session_id=session_id,
            )
            return {"success": False, "error": error_msg}

    def _get_connection(self, instance: Instance):
        """获取数据库连接"""
        return self.database_service.get_connection(instance)

    def _update_database_version(self, instance: Instance, conn):
        """更新数据库版本信息"""
        try:
            version_info = self.database_service.get_database_version(instance, conn)
            if version_info and version_info != instance.database_version:
                from app.utils.version_parser import DatabaseVersionParser

                # 解析版本信息
                parsed = DatabaseVersionParser.parse_version(instance.db_type.lower(), version_info)
                
                # 更新实例的版本信息
                instance.database_version = parsed['original']
                instance.main_version = parsed['main_version']
                instance.detailed_version = parsed['detailed_version']
                
                self.sync_logger.info(
                    "更新数据库版本",
                    module="unified_sync",
                    instance_name=instance.name,
                    old_version=instance.database_version,
                    new_version=version_info,
                )
        except Exception as e:
            self.sync_logger.warning(
                "版本信息更新失败",
                module="unified_sync",
                instance_name=instance.name,
                error=str(e),
            )

    def _execute_sync_by_db_type(self, sync_manager: SyncDataManager, instance: Instance, conn, session_id: str):
        """根据数据库类型执行同步"""
        db_type_methods = {
            "mysql": sync_manager.sync_mysql_accounts,
            "postgresql": sync_manager.sync_postgresql_accounts,
            "sqlserver": sync_manager.sync_sqlserver_accounts,
            "oracle": sync_manager.sync_oracle_accounts,
        }

        method = db_type_methods.get(instance.db_type)
        if not method:
            return {
                "success": False,
                "error": f"不支持的数据库类型: {instance.db_type}",
            }

        self.sync_logger.info(
            "开始数据库账户同步",
            module="unified_sync",
            instance_name=instance.name,
            db_type=instance.db_type,
        )

        result = method(instance, conn, session_id)

        self.sync_logger.info(
            "数据库同步完成",
            module="unified_sync",
            instance_name=instance.name,
            db_type=instance.db_type,
            synced_count=result.get("synced_count", 0),
        )

        return result

    def _get_account_count(self, instance: Instance) -> int:
        """获取同步前的账户数量"""
        try:
            from app.models.current_account_sync_data import CurrentAccountSyncData
            return CurrentAccountSyncData.query.filter_by(
                instance_id=instance.id, 
                db_type=instance.db_type,
                is_deleted=False
            ).count()
        except Exception:
            return 0

    def _create_sync_report(self, instance: Instance, session_id: str, sync_type: str, before_count: int, result: Dict):
        """创建同步报告记录"""
        try:
            from app.models.current_account_sync_data import CurrentAccountSyncData

            # 计算同步后数量
            after_count = CurrentAccountSyncData.query.filter_by(
                instance_id=instance.id, 
                db_type=instance.db_type,
                is_deleted=False
            ).count()

            net_change = after_count - before_count

            # 创建同步报告记录
            from app.models.sync_instance_record import SyncInstanceRecord

            sync_record = SyncInstanceRecord(
                session_id=session_id,
                instance_id=instance.id,
                sync_type=sync_type,
                sync_category="account",
                before_count=before_count,
                after_count=after_count,
                synced_count=result.get("synced_count", 0),
                added_count=result.get("added_count", 0),
                removed_count=result.get("removed_count", 0),
                modified_count=result.get("modified_count", 0),
                net_change=net_change,
                has_changes=net_change != 0,
                sync_status="completed",
                created_at=now(),
                updated_at=now(),
            )

            db.session.add(sync_record)
            db.session.commit()

            self.sync_logger.info(
                "创建同步报告记录",
                module="unified_sync",
                session_id=session_id,
                instance_name=instance.name,
                before_count=before_count,
                after_count=after_count,
                net_change=net_change,
            )

        except Exception as e:
            self.sync_logger.error(
                "创建同步报告失败",
                module="unified_sync",
                session_id=session_id,
                instance_name=instance.name,
                error=str(e),
            )

    def _log_sync_completion(self, instance: Instance, result: Dict):
        """记录同步完成日志"""
        # 使用 db_logger 记录数据库操作完成
        self.db_logger.info(
            "账户同步完成",
            instance_name=instance.name,
            synced_count=result.get("synced_count", 0),
            added_count=result.get("added_count", 0),
            removed_count=result.get("removed_count", 0),
            modified_count=result.get("modified_count", 0),
        )

        # 使用 sync_logger 记录同步流程完成
        self.sync_logger.info(
            "账户同步流程完成",
            module="unified_sync",
            instance_name=instance.name,
            db_type=instance.db_type,
            synced_count=result.get("synced_count", 0),
            added_count=result.get("added_count", 0),
            removed_count=result.get("removed_count", 0),
            modified_count=result.get("modified_count", 0),
        )


# 创建全局实例，便于其他模块使用
unified_sync_service = UnifiedSyncService()
