"""
泰摸鱼吧 - 实例模型
"""

from datetime import datetime
from app.utils.timezone import now
from app import db
from app.utils.enhanced_logger import log_operation


class Instance(db.Model):
    """数据库实例模型"""

    __tablename__ = "instances"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    db_type = db.Column(db.String(50), nullable=False, index=True)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    database_name = db.Column(db.String(255), nullable=True)
    database_version = db.Column(db.String(100), nullable=True)
    environment = db.Column(
        db.String(20), default="production", nullable=False, index=True
    )  # 环境：production, development, testing
    sync_count = db.Column(db.Integer, default=0, nullable=False)
    credential_id = db.Column(
        db.Integer, db.ForeignKey("credentials.id"), nullable=True
    )
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), default="active", index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_connected = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    # 关系
    credential = db.relationship("Credential", backref="instances")
    accounts = db.relationship("Account", backref="instance", lazy="dynamic")
    sync_data = db.relationship("SyncData", backref="instance", lazy="dynamic")

    def __init__(
        self,
        name,
        db_type,
        host,
        port,
        credential_id=None,
        description=None,
        tags=None,
        environment="production",
    ):
        """
        初始化实例

        Args:
            name: 实例名称
            db_type: 数据库类型
            host: 主机地址
            port: 端口号
            credential_id: 凭据ID
            description: 描述
            tags: 标签
            environment: 环境类型（production, development, testing）
        """
        self.name = name
        self.db_type = db_type
        self.host = host
        self.port = port
        self.credential_id = credential_id
        self.description = description
        self.tags = tags or []
        self.environment = environment

    def test_connection(self):
        """
        测试数据库连接

        Returns:
            dict: 连接测试结果
        """
        try:
            if self.db_type == "SQL Server":
                return self._test_sql_server_connection()
            elif self.db_type == "MySQL":
                return self._test_mysql_connection()
            elif self.db_type == "Oracle":
                return self._test_oracle_connection()
            else:
                return {
                    "status": "error",
                    "message": f"不支持的数据库类型: {self.db_type}",
                }
        except Exception as e:
            return {"status": "error", "message": f"连接测试失败: {str(e)}"}

    def _test_sql_server_connection(self):
        """测试SQL Server连接"""
        import pymssql

        try:
            conn = pymssql.connect(
                server=self.host,
                port=self.port,
                user=self.credential.username if self.credential else "",
                password=self.credential.password if self.credential else "",
                database="master",
            )
            conn.close()
            return {"status": "success", "message": "SQL Server连接成功"}
        except Exception as e:
            return {"status": "error", "message": f"SQL Server连接失败: {str(e)}"}

    def _test_mysql_connection(self):
        """测试MySQL连接"""
        import pymysql

        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.credential.username if self.credential else "",
                password=self.credential.password if self.credential else "",
                database="mysql",
            )
            conn.close()
            return {"status": "success", "message": "MySQL连接成功"}
        except Exception as e:
            return {"status": "error", "message": f"MySQL连接失败: {str(e)}"}

    def _test_oracle_connection(self):
        """测试Oracle连接"""
        import oracledb

        try:
            dsn = f"{self.host}:{self.port}/ORCL"

            # 优先使用Thick模式连接（适用于所有Oracle版本，包括11g）
            try:
                # 初始化Thick模式（需要Oracle Instant Client）
                oracledb.init_oracle_client()
                conn = oracledb.connect(
                    user=self.credential.username if self.credential else "",
                    password=self.credential.password if self.credential else "",
                    dsn=dsn,
                )
                conn.close()
                return {"status": "success", "message": "Oracle连接成功 (Thick模式)"}
            except oracledb.DatabaseError as e:
                # 如果Thick模式失败，尝试Thin模式（适用于Oracle 12c+）
                if "DPI-1047" in str(e) or "Oracle Client library" in str(e):
                    # Thick模式失败，尝试Thin模式
                    try:
                        conn = oracledb.connect(
                            user=self.credential.username if self.credential else "",
                            password=(
                                self.credential.password if self.credential else ""
                            ),
                            dsn=dsn,
                        )
                        conn.close()
                        return {
                            "status": "success",
                            "message": "Oracle连接成功 (Thin模式)",
                        }
                    except oracledb.DatabaseError as thin_error:
                        # 如果Thin模式也失败，抛出原始错误
                        raise e
                else:
                    raise
        except Exception as e:
            return {"status": "error", "message": f"Oracle连接失败: {str(e)}"}

    def to_dict(self, include_password=False):
        """
        转换为字典格式

        Args:
            include_password: 是否包含密码（默认False，安全考虑）

        Returns:
            dict: 实例信息字典
        """
        data = {
            "id": self.id,
            "name": self.name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "environment": self.environment,
            "credential_id": self.credential_id,
            "description": self.description,
            "tags": self.tags,
            "status": self.status,
            "is_active": self.is_active,
            "last_connected": (
                self.last_connected.isoformat() if self.last_connected else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.credential:
            if include_password:
                data["credential"] = {
                    "id": self.credential.id,
                    "name": self.credential.name,
                    "username": self.credential.username,
                    "password": self.credential.password,
                    "credential_type": self.credential.credential_type,
                }
            else:
                data["credential"] = {
                    "id": self.credential.id,
                    "name": self.credential.name,
                    "username": self.credential.username,
                    "password": self.credential.get_password_masked(),
                    "credential_type": self.credential.credential_type,
                }

        return data

    def soft_delete(self):
        """软删除实例"""
        self.deleted_at = now()
        self.status = "deleted"
        db.session.commit()
        log_operation(
            "instance_delete", details={"instance_id": self.id, "name": self.name}
        )

    def restore(self):
        """恢复实例"""
        self.deleted_at = None
        self.status = "active"
        db.session.commit()
        log_operation(
            "instance_restore", details={"instance_id": self.id, "name": self.name}
        )

    @staticmethod
    def get_active_instances():
        """获取所有活跃实例"""
        return Instance.query.filter_by(deleted_at=None, status="active").all()

    @staticmethod
    def get_by_db_type(db_type):
        """根据数据库类型获取实例"""
        return Instance.query.filter_by(db_type=db_type, deleted_at=None).all()

    @staticmethod
    def get_by_environment(environment):
        """根据环境类型获取实例"""
        return Instance.query.filter_by(environment=environment, deleted_at=None).all()

    @staticmethod
    def get_by_db_type_and_environment(db_type, environment):
        """根据数据库类型和环境类型获取实例"""
        return Instance.query.filter_by(
            db_type=db_type, environment=environment, deleted_at=None
        ).all()

    @staticmethod
    def get_environment_choices():
        """获取环境类型选项"""
        return [
            ("production", "生产环境"),
            ("development", "开发环境"),
            ("testing", "测试环境"),
        ]

    def __repr__(self):
        return f"<Instance {self.name}>"
