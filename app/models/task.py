"""
泰摸鱼吧 - 任务模型
"""

from datetime import datetime
from app import db

class Task(db.Model):
    """任务模型"""
    
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    task_type = db.Column(db.String(50), nullable=False, index=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('instances.id'), nullable=True)
    schedule = db.Column(db.String(100), nullable=True)  # cron表达式
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_run = db.Column(db.DateTime, nullable=True)
    last_status = db.Column(db.String(20), nullable=True)
    last_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    instance = db.relationship('Instance', backref='tasks')
    
    def __init__(self, name, task_type, instance_id=None, schedule=None, description=None, is_active=True):
        """
        初始化任务
        
        Args:
            name: 任务名称
            task_type: 任务类型
            instance_id: 实例ID
            schedule: 调度表达式
            description: 描述
            is_active: 是否启用
        """
        self.name = name
        self.task_type = task_type
        self.instance_id = instance_id
        self.schedule = schedule
        self.description = description
        self.is_active = is_active
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            Dict: 任务信息字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'task_type': self.task_type,
            'instance_id': self.instance_id,
            'instance_name': self.instance.name if self.instance else None,
            'schedule': self.schedule,
            'description': self.description,
            'is_active': self.is_active,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_status': self.last_status,
            'last_message': self.last_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_active_tasks():
        """获取所有活跃任务"""
        return Task.query.filter_by(is_active=True).all()
    
    @staticmethod
    def get_by_type(task_type):
        """根据任务类型获取任务"""
        return Task.query.filter_by(task_type=task_type, is_active=True).all()
    
    def __repr__(self):
        return f'<Task {self.name}>'