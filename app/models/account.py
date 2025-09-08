# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户数据模型
"""

from app import db
from datetime import datetime

class Account(db.Model):
    """账户数据模型"""
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('instances.id'), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    host = db.Column(db.String(255), nullable=True)  # 主机模式，如 %, localhost, 10.10.%
    database_name = db.Column(db.String(255), nullable=True)
    account_type = db.Column(db.String(50), nullable=True)  # user, role, group等
    plugin = db.Column(db.String(100), nullable=True)  # 认证插件，如 caching_sha2_password
    password_expired = db.Column(db.Boolean, default=False)  # 密码是否过期
    password_last_changed = db.Column(db.DateTime, nullable=True)  # 密码最后修改时间
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系 - 注意：backref在Instance模型中定义
    
    def __repr__(self):
        return f'<Account {self.username}@{self.instance.name if self.instance else "Unknown"}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'username': self.username,
            'host': self.host,
            'database_name': self.database_name,
            'account_type': self.account_type,
            'plugin': self.plugin,
            'password_expired': self.password_expired,
            'password_last_changed': self.password_last_changed.isoformat() if self.password_last_changed else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'instance_name': self.instance.name if self.instance else None,
            'instance_type': self.instance.db_type if self.instance else None
        }