"""
泰摸鱼吧 - 环境变量管理工具
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class EnvManager:
    """环境变量管理器"""

    def __init__(self, env_file: str = ".env"):
        """
        初始化环境变量管理器

        Args:
            env_file: 环境变量文件路径
        """
        self.env_file = env_file
        self._load_env()

    def _load_env(self):
        """加载环境变量"""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)

    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        获取环境变量

        Args:
            key: 环境变量键
            default: 默认值
            required: 是否必需

        Returns:
            Any: 环境变量值

        Raises:
            ValueError: 当必需的环境变量不存在时
        """
        value = os.getenv(key, default)

        if required and value is None:
            raise ValueError(f"必需的环境变量 {key} 未设置")

        return value

    def get_int(self, key: str, default: int = 0, required: bool = False) -> int:
        """
        获取整数类型环境变量

        Args:
            key: 环境变量键
            default: 默认值
            required: 是否必需

        Returns:
            int: 环境变量值
        """
        value = self.get(key, default, required)

        if value is None:
            return default

        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"环境变量 {key} 的值 '{value}' 不是有效的整数")

    def get_float(
        self, key: str, default: float = 0.0, required: bool = False
    ) -> float:
        """
        获取浮点数类型环境变量

        Args:
            key: 环境变量键
            default: 默认值
            required: 是否必需

        Returns:
            float: 环境变量值
        """
        value = self.get(key, default, required)

        if value is None:
            return default

        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"环境变量 {key} 的值 '{value}' 不是有效的浮点数")

    def get_bool(self, key: str, default: bool = False, required: bool = False) -> bool:
        """
        获取布尔类型环境变量

        Args:
            key: 环境变量键
            default: 默认值
            required: 是否必需

        Returns:
            bool: 环境变量值
        """
        value = self.get(key, default, required)

        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on", "enabled")

        return bool(value)

    def get_list(
        self,
        key: str,
        default: list = None,
        separator: str = ",",
        required: bool = False,
    ) -> list:
        """
        获取列表类型环境变量

        Args:
            key: 环境变量键
            default: 默认值
            separator: 分隔符
            required: 是否必需

        Returns:
            list: 环境变量值列表
        """
        value = self.get(key, default, required)

        if value is None:
            return default or []

        if isinstance(value, list):
            return value

        if isinstance(value, str):
            return [item.strip() for item in value.split(separator) if item.strip()]

        return [value]

    def get_dict(self, key: str, default: dict = None, required: bool = False) -> dict:
        """
        获取字典类型环境变量（JSON格式）

        Args:
            key: 环境变量键
            default: 默认值
            required: 是否必需

        Returns:
            dict: 环境变量值字典
        """
        value = self.get(key, default, required)

        if value is None:
            return default or {}

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"环境变量 {key} 的值不是有效的JSON格式")

        return {}

    def set(self, key: str, value: Any, save_to_file: bool = False):
        """
        设置环境变量

        Args:
            key: 环境变量键
            value: 环境变量值
            save_to_file: 是否保存到文件
        """
        os.environ[key] = str(value)

        if save_to_file:
            self._save_to_file(key, value)

    def _save_to_file(self, key: str, value: Any):
        """
        保存环境变量到文件

        Args:
            key: 环境变量键
            value: 环境变量值
        """
        # 读取现有文件内容
        env_vars = {}
        if os.path.exists(self.env_file):
            with open(self.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip()

        # 更新环境变量
        env_vars[key] = str(value)

        # 写入文件
        with open(self.env_file, "w", encoding="utf-8") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")

    def validate_required(self, required_vars: list):
        """
        验证必需的环境变量

        Args:
            required_vars: 必需的环境变量列表

        Raises:
            ValueError: 当必需的环境变量不存在时
        """
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(f"以下必需的环境变量未设置: {', '.join(missing_vars)}")

    def get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库配置

        Returns:
            Dict[str, Any]: 数据库配置字典
        """
        return {
            "url": self.get("DATABASE_URL", required=True),
            "host": self.get("POSTGRES_HOST", "localhost"),
            "port": self.get_int("POSTGRES_PORT", 5432),
            "database": self.get("POSTGRES_DB", "taifish_dev"),
            "username": self.get("POSTGRES_USER", "taifish_user"),
            "password": self.get("POSTGRES_PASSWORD", "taifish_pass"),
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """
        获取Redis配置

        Returns:
            Dict[str, Any]: Redis配置字典
        """
        return {
            "url": self.get("REDIS_URL", required=True),
            "host": self.get("REDIS_HOST", "localhost"),
            "port": self.get_int("REDIS_PORT", 6379),
            "password": self.get("REDIS_PASSWORD", ""),
            "db": self.get_int("REDIS_DB", 0),
        }

    def get_external_db_config(self) -> Dict[str, Dict[str, Any]]:
        """
        获取外部数据库配置

        Returns:
            Dict[str, Dict[str, Any]]: 外部数据库配置字典
        """
        return {
            "sql_server": {
                "host": self.get("SQL_SERVER_HOST", "localhost"),
                "port": self.get_int("SQL_SERVER_PORT", 1433),
                "username": self.get("SQL_SERVER_USERNAME", "sa"),
                "password": self.get("SQL_SERVER_PASSWORD", ""),
            },
            "mysql": {
                "host": self.get("MYSQL_HOST", "localhost"),
                "port": self.get_int("MYSQL_PORT", 3306),
                "username": self.get("MYSQL_USERNAME", "root"),
                "password": self.get("MYSQL_PASSWORD", ""),
            },
            "oracle": {
                "host": self.get("ORACLE_HOST", "localhost"),
                "port": self.get_int("ORACLE_PORT", 1521),
                "service_name": self.get("ORACLE_SERVICE_NAME", "ORCL"),
                "username": self.get("ORACLE_USERNAME", "system"),
                "password": self.get("ORACLE_PASSWORD", ""),
            },
        }

    def get_security_config(self) -> Dict[str, Any]:
        """
        获取安全配置

        Returns:
            Dict[str, Any]: 安全配置字典
        """
        return {
            "secret_key": self.get("SECRET_KEY", required=True),
            "jwt_secret_key": self.get("JWT_SECRET_KEY", required=True),
            "bcrypt_rounds": self.get_int("BCRYPT_LOG_ROUNDS", 12),
            "jwt_access_expires": self.get_int("JWT_ACCESS_TOKEN_EXPIRES", 3600),
            "jwt_refresh_expires": self.get_int("JWT_REFRESH_TOKEN_EXPIRES", 2592000),
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """
        获取日志配置

        Returns:
            Dict[str, Any]: 日志配置字典
        """
        return {
            "level": self.get("LOG_LEVEL", "INFO"),
            "file": self.get("LOG_FILE", "userdata/logs/app.log"),
            "max_size": self.get_int("LOG_MAX_SIZE", 10485760),
            "backup_count": self.get_int("LOG_BACKUP_COUNT", 5),
        }

    def get_app_config(self) -> Dict[str, Any]:
        """
        获取应用配置

        Returns:
            Dict[str, Any]: 应用配置字典
        """
        return {
            "name": self.get("APP_NAME", "泰摸鱼吧"),
            "version": self.get("APP_VERSION", "1.0.0"),
            "debug": self.get_bool("DEBUG", False),
            "testing": self.get_bool("TESTING", False),
            "upload_folder": self.get("UPLOAD_FOLDER", "userdata/uploads"),
            "max_content_length": self.get_int("MAX_CONTENT_LENGTH", 16777216),
        }


# 创建全局环境变量管理器实例
env_manager = EnvManager()

# 验证必需的环境变量
try:
    env_manager.validate_required(
        ["SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
    )
except ValueError as e:
    print(f"环境变量配置错误: {e}")
    print("请检查 .env 文件或环境变量设置")
