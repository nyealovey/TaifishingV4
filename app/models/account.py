"""
泰摸鱼吧 - 账户模型
"""

from datetime import datetime
from app import db

class Account(db.Model):
    """账户模型"""
    
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    db_type = db.Column(db.String(50), nullable=False)
    instance_id = db.Column(db.Integer, db.ForeignKey('instances.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, nullable=True)
    permissions = db.Column(db.JSON, nullable=True)
    category_id = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Account {self.username}>'
