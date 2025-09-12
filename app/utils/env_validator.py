"""
泰摸鱼吧 - 环境变量验证工具
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class EnvironmentValidator:
    """环境变量验证器"""

    REQUIRED_VARS = ["SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"]

    OPTIONAL_VARS = {
        "REDIS_URL": "redis://localhost:6379/0",
        "LOG_LEVEL": "INFO",
        "LOG_MAX_SIZE": "10485760",  # 10MB
        "LOG_BACKUP_COUNT": "5",
        "CORS_ORIGINS": "http://localhost:5001,http://127.0.0.1:5001",
        "RATE_LIMIT_ENABLED": "true",
        "CACHE_TYPE": "simple",
        "CACHE_DEFAULT_TIMEOUT": "300",
        "SCHEDULER_TIMEZONE": "Asia/Shanghai",
        "MAIL_SERVER": "localhost",
        "MAIL_PORT": "587",
        "MAIL_USE_TLS": "true",
        "MAIL_USERNAME": "",
        "MAIL_PASSWORD": "",
        "UPLOAD_FOLDER": "uploads",
        "MAX_CONTENT_LENGTH": "16777216",  # 16MB
        "SESSION_COOKIE_SECURE": "false",
        "SESSION_COOKIE_HTTPONLY": "true",
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": "3600",
        "WTF_CSRF_ENABLED": "true",
        "WTF_CSRF_TIME_LIMIT": "3600",
    }

    @classmethod
    def validate_environment(cls) -> dict[str, Any]:
        """
        验证环境变量

        Returns:
            dict: 验证结果
        """
        result: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing_required": [],
            "invalid_values": [],
            "suggestions": [],
        }

        # 检查必需变量
        for var in cls.REQUIRED_VARS:
            if not os.getenv(var):
                result["missing_required"].append(var)
                result["valid"] = False
                result["errors"].append(f"缺少必需环境变量: {var}")

        # 检查可选变量并设置默认值
        for var, default_value in cls.OPTIONAL_VARS.items():
            if not os.getenv(var):
                os.environ[var] = default_value
                result["warnings"].append(f"使用默认值: {var}={default_value}")

        # 验证特定变量
        cls._validate_specific_vars(result)

        # 生成建议
        cls._generate_suggestions(result)

        return result

    @classmethod
    def _validate_specific_vars(cls, result: dict[str, Any]) -> None:
        """验证特定变量"""
        # 验证SECRET_KEY
        secret_key = os.getenv("SECRET_KEY")
        if secret_key and len(secret_key) < 32:
            result["invalid_values"].append("SECRET_KEY")
            result["errors"].append("SECRET_KEY长度至少32位")
            result["valid"] = False

        # 验证JWT_SECRET_KEY
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if jwt_secret and len(jwt_secret) < 32:
            result["invalid_values"].append("JWT_SECRET_KEY")
            result["errors"].append("JWT_SECRET_KEY长度至少32位")
            result["valid"] = False

        # 验证数据库URL
        db_url = os.getenv("DATABASE_URL")
        if db_url and not cls._is_valid_database_url(db_url):
            result["invalid_values"].append("DATABASE_URL")
            result["errors"].append("DATABASE_URL格式无效")
            result["valid"] = False

        # 验证Redis URL
        redis_url = os.getenv("REDIS_URL")
        if redis_url and not cls._is_valid_redis_url(redis_url):
            result["invalid_values"].append("REDIS_URL")
            result["warnings"].append("REDIS_URL格式可能无效")

        # 验证日志级别
        log_level = os.getenv("LOG_LEVEL", "INFO")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_levels:
            result["invalid_values"].append("LOG_LEVEL")
            result["warnings"].append(f"LOG_LEVEL无效，应为: {', '.join(valid_levels)}")

        # 验证端口号
        mail_port = os.getenv("MAIL_PORT", "587")
        try:
            port = int(mail_port)
            if port < 1 or port > 65535:
                result["invalid_values"].append("MAIL_PORT")
                result["warnings"].append("MAIL_PORT应在1-65535范围内")
        except ValueError:
            result["invalid_values"].append("MAIL_PORT")
            result["warnings"].append("MAIL_PORT应为数字")

    @classmethod
    def _is_valid_database_url(cls, url: str) -> bool:
        """验证数据库URL格式"""
        valid_schemes = ["sqlite", "postgresql", "mysql", "oracle", "mssql"]
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.scheme in valid_schemes
        except:
            return False

    @classmethod
    def _is_valid_redis_url(cls, url: str) -> bool:
        """验证Redis URL格式"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.scheme == "redis"
        except:
            return False

    @classmethod
    def _generate_suggestions(cls, result: dict[str, Any]) -> None:
        """生成配置建议"""
        suggestions = []

        # 安全建议
        if os.getenv("SECRET_KEY") == "your-secret-key-here":
            suggestions.append("请更改默认的SECRET_KEY")

        if os.getenv("JWT_SECRET_KEY") == "your-jwt-secret-key-here":
            suggestions.append("请更改默认的JWT_SECRET_KEY")

        # 生产环境建议
        if os.getenv("FLASK_ENV") == "production":
            if os.getenv("SESSION_COOKIE_SECURE") != "true":
                suggestions.append("生产环境建议设置SESSION_COOKIE_SECURE=true")

            if os.getenv("WTF_CSRF_ENABLED") != "true":
                suggestions.append("生产环境建议启用CSRF保护")

        # 性能建议
        cache_type = os.getenv("CACHE_TYPE", "simple")
        if cache_type == "simple" and os.getenv("REDIS_URL"):
            suggestions.append("建议使用Redis缓存替代简单缓存")

        # 日志建议
        log_level = os.getenv("LOG_LEVEL", "INFO")
        if log_level == "DEBUG" and os.getenv("FLASK_ENV") == "production":
            suggestions.append("生产环境不建议使用DEBUG日志级别")

        result["suggestions"] = suggestions

    @classmethod
    def generate_env_file(cls, filename: str = ".env.example") -> bool:
        """生成环境变量示例文件"""
        content = "# 泰摸鱼吧环境变量配置\n\n"
        content += "# 必需变量\n"
        for var in cls.REQUIRED_VARS:
            content += f"{var}=your-{var.lower().replace('_', '-')}-here\n"

        content += "\n# 可选变量\n"
        for var, default in cls.OPTIONAL_VARS.items():
            content += f"# {var}={default}\n"

        content += "\n# 数据库配置\n"
        content += "# DATABASE_URL=sqlite:///taifish.db\n"
        content += "# DATABASE_URL=postgresql://user:password@localhost/taifish\n"
        content += "# DATABASE_URL=mysql://user:password@localhost/taifish\n\n"

        content += "# Redis配置\n"
        content += "# REDIS_URL=redis://localhost:6379/0\n\n"

        content += "# 安全配置\n"
        content += "# SECRET_KEY=your-32-character-secret-key-here\n"
        content += "# JWT_SECRET_KEY=your-32-character-jwt-secret-key-here\n\n"

        content += "# 日志配置\n"
        content += "# LOG_LEVEL=INFO\n"
        content += "# LOG_MAX_SIZE=10485760\n"
        content += "# LOG_BACKUP_COUNT=5\n\n"

        content += "# 邮件配置\n"
        content += "# MAIL_SERVER=smtp.gmail.com\n"
        content += "# MAIL_PORT=587\n"
        content += "# MAIL_USE_TLS=true\n"
        content += "# MAIL_USERNAME=your-email@gmail.com\n"
        content += "# MAIL_PASSWORD=your-app-password\n"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"环境变量示例文件已生成: {filename}")
            return True
        except Exception as e:
            logger.error(f"生成环境变量文件失败: {e}")
            return False


def validate_and_setup_environment() -> bool:
    """验证并设置环境变量"""
    validator = EnvironmentValidator()
    result = validator.validate_environment()

    if not result["valid"]:
        logger.error("环境变量验证失败:")
        for error in result["errors"]:
            logger.error(f"  - {error}")
        return False

    if result["warnings"]:
        logger.warning("环境变量警告:")
        for warning in result["warnings"]:
            logger.warning(f"  - {warning}")

    if result["suggestions"]:
        logger.info("配置建议:")
        for suggestion in result["suggestions"]:
            logger.info(f"  - {suggestion}")

    logger.info("环境变量验证通过")
    return True
