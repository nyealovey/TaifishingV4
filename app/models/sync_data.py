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
    instance_id = db.Column(db.Integer, db.ForeignKey("instances.id"), nullable=False)
    task_id = db.Column(
        db.Integer, db.ForeignKey("tasks.id"), nullable=True, index=True
    )  # 关联任务ID
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
        sync_type,
        instance_id,
        task_id=None,
        data=None,
        status="success",
        message=None,
        synced_count=0,
        added_count=0,
        removed_count=0,
        modified_count=0,
        error_message=None,
        records_count=0,
    ):
        """
        初始化同步数据

        Args:
            sync_type: 同步类型
            instance_id: 实例ID
            task_id: 任务ID（可选）
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
        self.data = data
        self.status = status
        self.message = message
        self.synced_count = synced_count
        self.added_count = added_count
        self.removed_count = removed_count
        self.modified_count = modified_count
        self.error_message = error_message
        self.records_count = records_count

    def to_dict(self):
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
    def get_latest_sync(instance_id, sync_type=None):
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


    def __repr__(self):
        return f"<SyncData {self.sync_type} for instance {self.instance_id}>"
