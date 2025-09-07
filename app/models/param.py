"""
泰摸鱼吧 - 系统参数模型
"""

from datetime import datetime
from app import db

class Param(db.Model):
    """系统参数模型"""
    
    __tablename__ = 'params'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    value = db.Column(db.Text, nullable=False)
    default_value = db.Column(db.Text, nullable=True)
    param_type = db.Column(db.String(50), nullable=False, default='string')  # string, int, float, bool, json
    category = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, value, param_type='string', category='general', description=None, is_system=False, default_value=None):
        """
        初始化参数
        
        Args:
            name: 参数名称
            value: 参数值
            param_type: 参数类型
            category: 分类
            description: 描述
            is_system: 是否系统参数
            default_value: 默认值
        """
        self.name = name
        self.value = value
        self.param_type = param_type
        self.category = category
        self.description = description
        self.is_system = is_system
        self.default_value = default_value or value
    
    def get_typed_value(self):
        """
        获取类型转换后的值
        
        Returns:
            Any: 转换后的值
        """
        try:
            if self.param_type == 'int':
                return int(self.value)
            elif self.param_type == 'float':
                return float(self.value)
            elif self.param_type == 'bool':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.param_type == 'json':
                import json
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, TypeError):
            return self.value
    
    def set_typed_value(self, value):
        """
        设置类型化的值
        
        Args:
            value: 要设置的值
        """
        if self.param_type == 'json':
            import json
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            Dict: 参数信息字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'default_value': self.default_value,
            'param_type': self.param_type,
            'category': self.category,
            'description': self.description,
            'is_system': self.is_system,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_by_name(name):
        """根据名称获取参数"""
        return Param.query.filter_by(name=name).first()
    
    @staticmethod
    def get_by_category(category):
        """根据分类获取参数"""
        return Param.query.filter_by(category=category).all()
    
    @staticmethod
    def get_system_params():
        """获取系统参数"""
        return Param.query.filter_by(is_system=True).all()
    
    @staticmethod
    def get_user_params():
        """获取用户参数"""
        return Param.query.filter_by(is_system=False).all()
    
    @staticmethod
    def create_system_param(name, value, param_type='string', category='system', description=None, default_value=None):
        """创建系统参数"""
        param = Param(
            name=name,
            value=value,
            param_type=param_type,
            category=category,
            description=description,
            is_system=True,
            default_value=default_value or value
        )
        db.session.add(param)
        return param
    
    def __repr__(self):
        return f'<Param {self.name}>'
