"""
泰摸鱼吧 - 优化版同步会话服务
解决数据库锁定和死锁问题
"""

from datetime import datetime, timedelta
from typing import Any

from app import db
from app.models.instance import Instance
from app.models.sync_instance_record import SyncInstanceRecord
from app.models.sync_session import SyncSession
from app.utils.structlog_config import get_sync_logger, get_system_logger


class OptimizedSyncSessionService:
    """优化版同步会话服务 - 解决并发和锁定问题"""

    def __init__(self):
        self.system_logger = get_system_logger()
        self.sync_logger = get_sync_logger()
        self.lock_timeout = 300  # 5分钟锁超时

    def create_session(self, sync_type: str, sync_category: str = "account", created_by: int = None) -> SyncSession:
        """
        创建同步会话（优化版）

        Args:
            sync_type: 同步类型 ('scheduled' 或 'manual_batch')
            sync_category: 同步分类 ('account', 'capacity', 'config', 'other')
            created_by: 创建用户ID

        Returns:
            SyncSession: 创建的同步会话
        """
        try:
            # 使用短事务创建会话
            session = SyncSession(sync_type=sync_type, sync_category=sync_category, created_by=created_by)
            db.session.add(session)
            db.session.commit()

            self.sync_logger.info(
                "创建同步会话",
                module="sync_session_optimized",
                session_id=session.session_id,
                sync_type=sync_type,
                sync_category=sync_category,
                created_by=created_by,
            )

            return session
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(
                "创建同步会话失败",
                module="sync_session_optimized",
                sync_type=sync_type,
                sync_category=sync_category,
                error=str(e),
            )
            raise

    def acquire_instance_lock(self, instance_id: int, session_id: str) -> bool:
        """
        获取实例同步锁

        Args:
            instance_id: 实例ID
            session_id: 会话ID

        Returns:
            bool: 是否成功获取锁
        """
        try:
            # 清理过期锁
            self._cleanup_expired_locks()

            # 检查是否已有锁
            existing_lock = db.session.execute(
                "SELECT id FROM sync_locks WHERE instance_id = :instance_id AND expires_at > :now",
                {"instance_id": instance_id, "now": datetime.utcnow()},
            ).fetchone()

            if existing_lock:
                self.sync_logger.warning(
                    "实例已被锁定",
                    module="sync_session_optimized",
                    instance_id=instance_id,
                    session_id=session_id,
                )
                return False

            # 创建新锁
            expires_at = datetime.utcnow() + timedelta(seconds=self.lock_timeout)
            db.session.execute(
                "INSERT INTO sync_locks (instance_id, session_id, expires_at) VALUES (:instance_id, :session_id, :expires_at)",
                {"instance_id": instance_id, "session_id": session_id, "expires_at": expires_at},
            )
            db.session.commit()

            self.sync_logger.info(
                "获取实例锁成功",
                module="sync_session_optimized",
                instance_id=instance_id,
                session_id=session_id,
                expires_at=expires_at.isoformat(),
            )

            return True
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(
                "获取实例锁失败",
                module="sync_session_optimized",
                instance_id=instance_id,
                session_id=session_id,
                error=str(e),
            )
            return False

    def release_instance_lock(self, instance_id: int, session_id: str) -> bool:
        """
        释放实例同步锁

        Args:
            instance_id: 实例ID
            session_id: 会话ID

        Returns:
            bool: 是否成功释放锁
        """
        try:
            result = db.session.execute(
                "DELETE FROM sync_locks WHERE instance_id = :instance_id AND session_id = :session_id",
                {"instance_id": instance_id, "session_id": session_id},
            )
            db.session.commit()

            if result.rowcount > 0:
                self.sync_logger.info(
                    "释放实例锁成功",
                    module="sync_session_optimized",
                    instance_id=instance_id,
                    session_id=session_id,
                )
                return True
            self.sync_logger.warning(
                "实例锁不存在",
                module="sync_session_optimized",
                instance_id=instance_id,
                session_id=session_id,
            )
            return False
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(
                "释放实例锁失败",
                module="sync_session_optimized",
                instance_id=instance_id,
                session_id=session_id,
                error=str(e),
            )
            return False

    def add_instance_records_batch(self, session_id: str, instance_ids: list[int]) -> list[SyncInstanceRecord]:
        """
        批量添加实例记录（优化版）

        Args:
            session_id: 会话ID
            instance_ids: 实例ID列表

        Returns:
            List[SyncInstanceRecord]: 创建的实例记录列表
        """
        try:
            # 分批处理，避免长时间锁定
            batch_size = 10
            all_records = []

            for i in range(0, len(instance_ids), batch_size):
                batch_instance_ids = instance_ids[i : i + batch_size]
                records = self._add_instance_records_batch(session_id, batch_instance_ids)
                all_records.extend(records)

            self.sync_logger.info(
                "批量添加实例记录完成",
                module="sync_session_optimized",
                session_id=session_id,
                total_count=len(all_records),
            )

            return all_records
        except Exception as e:
            self.sync_logger.error(
                "批量添加实例记录失败",
                module="sync_session_optimized",
                session_id=session_id,
                error=str(e),
            )
            raise

    def _add_instance_records_batch(self, session_id: str, instance_ids: list[int]) -> list[SyncInstanceRecord]:
        """添加一批实例记录"""
        try:
            records = []
            instances = Instance.query.filter(Instance.id.in_(instance_ids)).all()
            instance_dict = {inst.id: inst for inst in instances}

            for instance_id in instance_ids:
                instance = instance_dict.get(instance_id)
                if instance:
                    record = SyncInstanceRecord(
                        session_id=session_id,
                        instance_id=instance_id,
                        instance_name=instance.name,
                        sync_category="account",
                    )
                    db.session.add(record)
                    records.append(record)

            db.session.commit()
            return records
        except Exception:
            db.session.rollback()
            raise

    def start_instance_sync_with_lock(self, record_id: int) -> bool:
        """
        开始实例同步（带锁控制）

        Args:
            record_id: 实例记录ID

        Returns:
            bool: 是否成功开始
        """
        try:
            record = SyncInstanceRecord.query.get(record_id)
            if not record:
                return False

            # 获取实例锁
            if not self.acquire_instance_lock(record.instance_id, record.session_id):
                self.sync_logger.warning(
                    "无法获取实例锁，跳过同步",
                    module="sync_session_optimized",
                    record_id=record_id,
                    instance_id=record.instance_id,
                    session_id=record.session_id,
                )
                return False

            # 开始同步
            record.start_sync()
            db.session.commit()

            self.sync_logger.info(
                "开始实例同步",
                module="sync_session_optimized",
                session_id=record.session_id,
                instance_id=record.instance_id,
                instance_name=record.instance_name,
            )

            return True
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(
                "开始实例同步失败",
                module="sync_session_optimized",
                record_id=record_id,
                error=str(e),
            )
            return False

    def complete_instance_sync_with_lock(
        self,
        record_id: int,
        accounts_synced: int = 0,
        accounts_created: int = 0,
        accounts_updated: int = 0,
        accounts_deleted: int = 0,
        sync_details: dict[str, Any] = None,
    ) -> bool:
        """
        完成实例同步（带锁控制）

        Args:
            record_id: 实例记录ID
            accounts_synced: 同步的账户总数
            accounts_created: 新增的账户数量
            accounts_updated: 更新的账户数量
            accounts_deleted: 删除的账户数量
            sync_details: 同步详情

        Returns:
            bool: 是否成功完成
        """
        try:
            record = SyncInstanceRecord.query.get(record_id)
            if not record:
                return False

            # 完成同步
            record.complete_sync(
                accounts_synced=accounts_synced,
                accounts_created=accounts_created,
                accounts_updated=accounts_updated,
                accounts_deleted=accounts_deleted,
                sync_details=sync_details,
            )
            db.session.commit()

            # 释放实例锁
            self.release_instance_lock(record.instance_id, record.session_id)

            # 异步更新会话统计（避免长时间锁定）
            self._update_session_statistics_async(record.session_id)

            self.sync_logger.info(
                "完成实例同步",
                module="sync_session_optimized",
                session_id=record.session_id,
                instance_id=record.instance_id,
                instance_name=record.instance_name,
                accounts_synced=accounts_synced,
                accounts_created=accounts_created,
                accounts_updated=accounts_updated,
                accounts_deleted=accounts_deleted,
            )

            return True
        except Exception as e:
            db.session.rollback()
            # 确保释放锁
            if record:
                self.release_instance_lock(record.instance_id, record.session_id)
            self.sync_logger.error(
                "完成实例同步失败",
                module="sync_session_optimized",
                record_id=record_id,
                error=str(e),
            )
            return False

    def fail_instance_sync_with_lock(
        self, record_id: int, error_message: str, sync_details: dict[str, Any] = None
    ) -> bool:
        """
        标记实例同步失败（带锁控制）

        Args:
            record_id: 实例记录ID
            error_message: 错误信息
            sync_details: 同步详情

        Returns:
            bool: 是否成功标记
        """
        try:
            record = SyncInstanceRecord.query.get(record_id)
            if not record:
                return False

            # 标记失败
            record.fail_sync(error_message=error_message, sync_details=sync_details)
            db.session.commit()

            # 释放实例锁
            self.release_instance_lock(record.instance_id, record.session_id)

            # 异步更新会话统计
            self._update_session_statistics_async(record.session_id)

            self.sync_logger.error(
                "实例同步失败",
                module="sync_session_optimized",
                session_id=record.session_id,
                instance_id=record.instance_id,
                instance_name=record.instance_name,
                error_message=error_message,
            )

            return True
        except Exception as e:
            db.session.rollback()
            # 确保释放锁
            if record:
                self.release_instance_lock(record.instance_id, record.session_id)
            self.sync_logger.error(
                "标记实例同步失败时出错",
                module="sync_session_optimized",
                record_id=record_id,
                error=str(e),
            )
            return False

    def _cleanup_expired_locks(self):
        """清理过期的锁"""
        try:
            result = db.session.execute("DELETE FROM sync_locks WHERE expires_at < :now", {"now": datetime.utcnow()})
            if result.rowcount > 0:
                db.session.commit()
                self.sync_logger.info(
                    "清理过期锁",
                    module="sync_session_optimized",
                    cleaned_count=result.rowcount,
                )
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(
                "清理过期锁失败",
                module="sync_session_optimized",
                error=str(e),
            )

    def _update_session_statistics_async(self, session_id: str):
        """异步更新会话统计信息（避免长时间锁定）"""
        try:
            # 使用短事务更新统计
            session = SyncSession.query.filter_by(session_id=session_id).first()
            if session:
                # 使用原生SQL避免ORM锁定
                db.session.execute(
                    """
                    UPDATE sync_sessions
                    SET total_instances = (
                        SELECT COUNT(*) FROM sync_instance_records
                        WHERE session_id = :session_id
                    ),
                    successful_instances = (
                        SELECT COUNT(*) FROM sync_instance_records
                        WHERE session_id = :session_id AND status = 'completed'
                    ),
                    failed_instances = (
                        SELECT COUNT(*) FROM sync_instance_records
                        WHERE session_id = :session_id AND status = 'failed'
                    ),
                    updated_at = :now
                    WHERE session_id = :session_id
                    """,
                    {"session_id": session_id, "now": datetime.utcnow()},
                )
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(
                "异步更新会话统计失败",
                module="sync_session_optimized",
                session_id=session_id,
                error=str(e),
            )

    def get_session_performance(self, session_id: str) -> dict[str, Any]:
        """
        获取会话性能统计

        Args:
            session_id: 会话ID

        Returns:
            Dict: 性能统计信息
        """
        try:
            result = db.session.execute(
                """
                SELECT * FROM sync_performance_view
                WHERE session_id = :session_id
                """,
                {"session_id": session_id},
            ).fetchone()

            if result:
                return {
                    "session_id": result[0],
                    "sync_type": result[1],
                    "status": result[2],
                    "started_at": result[3],
                    "completed_at": result[4],
                    "total_instances": result[5],
                    "successful_instances": result[6],
                    "failed_instances": result[7],
                    "duration_seconds": result[8],
                    "total_records": result[9],
                    "completed_records": result[10],
                    "failed_records": result[11],
                    "running_records": result[12],
                }
            return {}
        except Exception as e:
            self.sync_logger.error(
                "获取会话性能统计失败",
                module="sync_session_optimized",
                session_id=session_id,
                error=str(e),
            )
            return {}

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        清理旧的同步会话

        Args:
            days: 保留天数

        Returns:
            int: 清理的会话数量
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 清理旧的会话记录
            result = db.session.execute(
                "DELETE FROM sync_sessions WHERE created_at < :cutoff_date AND status != 'running'",
                {"cutoff_date": cutoff_date},
            )

            cleaned_count = result.rowcount
            db.session.commit()

            if cleaned_count > 0:
                self.sync_logger.info(
                    "清理旧会话记录",
                    module="sync_session_optimized",
                    cleaned_count=cleaned_count,
                    cutoff_date=cutoff_date.isoformat(),
                )

            return cleaned_count
        except Exception as e:
            db.session.rollback()
            self.sync_logger.error(
                "清理旧会话记录失败",
                module="sync_session_optimized",
                error=str(e),
            )
            return 0


# 创建全局服务实例
optimized_sync_session_service = OptimizedSyncSessionService()
