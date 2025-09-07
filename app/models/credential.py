"""
泰摸鱼吧 - 凭据模型
"""

from datetime import datetime
from app import db, bcrypt
from app.utils.logger import log_operation

class Credential(db.Model):
    """凭据模型"""
    
    __tablename__ = 'credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    credential_type = db.Column(db.String(50), nullable=False, index=True)
    db_type = db.Column(db.String(50), nullable=True, index=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instance_ids = db.Column(db.JSON, nullable=True)
    category_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, name, credential_type, username, password, db_type=None, instance_ids=None, category_id=None, description=None):
        """
        初始化凭据
        
        Args:
            name: 凭据名称
            credential_type: 凭据类型
            username: 用户名
            password: 密码
            db_type: 数据库类型
            instance_ids: 关联实例ID列表
            category_id: 分类ID
            description: 描述
        """
        self.name = name
        self.credential_type = credential_type
        self.username = username
        self.set_password(password)
        self.db_type = db_type
        self.instance_ids = instance_ids or []
        self.category_id = category_id
        self.description = description
    
    def set_password(self, password):
        """
        设置密码（加密）
        
        Args:
            password: 原始密码
        """
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """
        验证密码
        
        Args:
            password: 原始密码
            
        Returns:
            bool: 密码是否正确
        """
        return bcrypt.check_password_hash(self.password, password)
    
    def get_password_masked(self):
        """
        获取掩码密码
        
        Returns:
            str: 掩码后的密码
        """
        if len(self.password) > 8:
            return '*' * (len(self.password) - 4) + self.password[-4:]
        return '*' * len(self.password)
    
    def to_dict(self, include_password=False):
        """
        转换为字典
        
        Args:
            include_password: 是否包含密码
            
        Returns:
            dict: 凭据信息字典
        """
        data = {
            'id': self.id,
            'name': self.name,
            'credential_type': self.credential_type,
            'db_type': self.db_type,
            'username': self.username,
            'instance_ids': self.instance_ids,
            'category_id': self.category_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_password:
            data['password'] = self.password
        else:
            data['password'] = self.get_password_masked()
        
        return data
    
    def soft_delete(self):
        """软删除凭据"""
        self.deleted_at = datetime.utcnow()
        db.session.commit()
        log_operation('credential_delete', details={'credential_id': self.id, 'name': self.name})
    
    def restore(self):
        """恢复凭据"""
        self.deleted_at = None
        db.session.commit()
        log_operation('credential_restore', details={'credential_id': self.id, 'name': self.name})
    
    @staticmethod
    def get_active_credentials():
        """获取所有活跃凭据"""
        return Credential.query.filter_by(deleted_at=None).all()
    
    @staticmethod
    def get_by_type(credential_type):
        """根据类型获取凭据"""
        return Credential.query.filter_by(credential_type=credential_type, deleted_at=None).all()
    
    @staticmethod
    def get_by_db_type(db_type):
        """根据数据库类型获取凭据"""
        return Credential.query.filter_by(db_type=db_type, deleted_at=None).all()
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            Dict: 凭据信息字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'credential_type': self.credential_type,
            'db_type': self.db_type,
            'username': self.username,
            'instance_ids': self.instance_ids,
            'category_id': self.category_id,
            'is_active': getattr(self, 'is_active', True),
            'description': getattr(self, 'description', ''),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Credential {self.name}>'
