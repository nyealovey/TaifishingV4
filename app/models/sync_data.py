"""
泰摸鱼吧 - 同步数据模型
"""

from datetime import datetime

from app import db


class SyncData(db.Model):
    """同步数据模型"""

    __tablename__ = "sync_data"

    id = db.Column(db.Integer, primary_key=True)
    sync_type = db.Column(db.String(50), nullable=False, index=True)
    instance_id = db.Column(db.Integer, db.ForeignKey("instances.id"), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=True, index=True)  # 关联任务ID
    session_id = db.Column(db.String(36), nullable=True, index=True)  # 关联同步会话ID
    sync_category = db.Column(db.String(20), nullable=True, index=True)  # 同步分类
    data = db.Column(db.JSON, nullable=True)
    sync_time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(20), default="success", index=True)
    message = db.Column(db.Text, nullable=True)
    synced_count = db.Column(db.Integer, default=0)
    added_count = db.Column(db.Integer, default=0)  # 新增账户数量
    removed_count = db.Column(db.Integer, default=0)  # 删除账户数量
    modified_count = db.Column(db.Integer, default=0)  # 修改账户数量
    error_message = db.Column(db.Text, nullable=True)
    records_count = db.Column(db.Integer, default=0)

    def __init__(
        self,
        sync_type: str,
        instance_id: int,
        task_id: str | None = None,
        session_id: str | None = None,
        sync_category: str | None = None,
        data: str | None = None,
        status: str = "success",
        message: str | None = None,
        synced_count: int = 0,
        added_count: int = 0,
        removed_count: int = 0,
        modified_count: int = 0,
        error_message: str | None = None,
        records_count: int = 0,
    ) -> None:
        """
        初始化同步数据

        Args:
            sync_type: 同步类型
            instance_id: 实例ID
            task_id: 任务ID（可选）
            session_id: 同步会话ID（可选）
            sync_category: 同步分类（可选）
            data: 同步数据
            status: 同步状态
            message: 同步消息
            synced_count: 同步数量
            added_count: 新增账户数量
            removed_count: 删除账户数量
            modified_count: 修改账户数量
            error_message: 错误信息
            records_count: 记录数量
        """
        self.sync_type = sync_type
        self.instance_id = instance_id
        self.task_id = task_id
        self.session_id = session_id
        self.sync_category = sync_category
        self.data = data
        self.status = status
        self.message = message
        self.synced_count = synced_count
        self.added_count = added_count
        self.removed_count = removed_count
        self.modified_count = modified_count
        self.error_message = error_message
        self.records_count = records_count

    def get_record_ids(self) -> list:
        """
        获取记录ID列表（兼容聚合记录接口）

        Returns:
            list: 记录ID列表
        """
        return [self.id]

    def to_dict(self) -> dict:
        """
        转换为字典

        Returns:
            dict: 同步数据字典
        """
        return {
            "id": self.id,
            "sync_type": self.sync_type,
            "instance_id": self.instance_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "sync_category": self.sync_category,
            "data": self.data,
            "sync_time": self.sync_time.isoformat() if self.sync_time else None,
            "status": self.status,
            "message": self.message,
            "synced_count": self.synced_count,
            "added_count": self.added_count,
            "removed_count": self.removed_count,
            "modified_count": self.modified_count,
            "error_message": self.error_message,
            "records_count": self.records_count,
            "instance_name": self.instance.name if self.instance else "未知实例",
        }

    @staticmethod
    def get_latest_sync(instance_id: int, sync_type: str | None = None) -> "SyncData | None":
        """
        获取最新同步数据

        Args:
            instance_id: 实例ID
            sync_type: 同步类型

        Returns:
            SyncData: 最新同步数据
        """
        query = SyncData.query.filter_by(instance_id=instance_id)
        if sync_type:
            query = query.filter_by(sync_type=sync_type)
        return query.order_by(SyncData.sync_time.desc()).first()

    def __repr__(self) -> str:
        return f"<SyncData {self.sync_type} for instance {self.instance_id}>"
