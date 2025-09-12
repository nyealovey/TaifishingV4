"""
泰摸鱼吧 - 用户模型
"""

from datetime import datetime

from flask_login import UserMixin

from app import bcrypt, db
from app.utils.timezone import now


class User(UserMixin, db.Model):
    """用户模型"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # 关系
    # logs关系在Log模型中定义

    def __init__(self, username, password, role="user"):
        """
        初始化用户

        Args:
            username: 用户名
            password: 密码
            role: 角色
        """
        self.username = username
        self.set_password(password)
        self.role = role

    def set_password(self, password):
        """
        设置密码（加密）

        Args:
            password: 原始密码
        """
        # 增加密码强度验证
        if len(password) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isupper() for c in password):
            raise ValueError("密码必须包含大写字母")
        if not any(c.islower() for c in password):
            raise ValueError("密码必须包含小写字母")
        if not any(c.isdigit() for c in password):
            raise ValueError("密码必须包含数字")

        self.password = bcrypt.generate_password_hash(password, rounds=12).decode("utf-8")

    def check_password(self, password):
        """
        验证密码

        Args:
            password: 原始密码

        Returns:
            bool: 密码是否正确
        """
        return bcrypt.check_password_hash(self.password, password)

    def is_admin(self):
        """
        检查是否为管理员

        Returns:
            bool: 是否为管理员
        """
        return self.role == "admin"

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = now()
        db.session.commit()

    def to_dict(self):
        """
        转换为字典

        Returns:
            dict: 用户信息字典
        """
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active,
        }

    @staticmethod
    def create_admin():
        """创建默认管理员用户"""
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", password="Admin123", role="admin")
            db.session.add(admin)
            db.session.commit()
            print("✅ 默认管理员用户已创建: admin/Admin123")
        return admin

    def __repr__(self):
        return f"<User {self.username}>"
