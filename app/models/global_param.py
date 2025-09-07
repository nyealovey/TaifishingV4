"""
泰摸鱼吧 - 全局参数模型
"""

from datetime import datetime
from app import db

class GlobalParam(db.Model):
    """全局参数模型"""
    
    __tablename__ = 'global_params'
    
    id = db.Column(db.Integer, primary_key=True)
    param_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    config = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<GlobalParam {self.name}>'
