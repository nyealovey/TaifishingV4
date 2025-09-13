"""
泰摸鱼吧 - 增强日志系统
提供统一的日志记录接口，确保所有错误、警告和信息都被正确记录
"""

import logging
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

from flask import current_app, has_request_context, request
from flask_login import current_user

# 延迟导入以避免循环导入
from app.utils.timezone import now


class EnhancedLogger:
    """增强的日志记录器"""

    def __init__(self, name: str = "taifish"):
        self.logger = logging.getLogger(name)
        self.name = name

    def _get_request_context(self) -> dict[str, Any]:
        """获取请求上下文信息"""
        context = {}

        if has_request_context():
            context.update(
                {
                    "ip_address": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent"),
                    "url": request.url,
                    "method": request.method,
                    "endpoint": request.endpoint,
                }
            )

            if current_user and hasattr(current_user, "id"):
                context["user_id"] = current_user.id

        return context

    def _log_to_database(
        self,
        level: str,
        log_type: str,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录日志到数据库"""
        try:
            # 检查是否在应用上下文中
            from flask import has_app_context

            if not has_app_context():
                # 如果不在应用上下文中，只记录到文件
                return

            context = self._get_request_context()

            # 如果有异常，添加堆栈跟踪信息
            if exception:
                details = details or ""
                details += f"\n异常类型: {type(exception).__name__}\n"
                details += f"异常信息: {str(exception)}\n"
                details += f"堆栈跟踪:\n{traceback.format_exc()}"

            # 记录到数据库
            from app.models.log import Log

            Log.log_operation(  # type: ignore
                level=level,
                log_type=log_type,
                message=message,
                module=module or self.name,
                details=details,
                user_id=context.get("user_id"),
                ip_address=context.get("ip_address"),
                user_agent=context.get("user_agent"),
                source=source,
            )

        except Exception as e:
            # 如果数据库记录失败，至少记录到文件
            self.logger.error(f"记录日志到数据库失败: {e}")

    def debug(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录DEBUG级别日志"""
        self.logger.debug(message)
        self._log_to_database("DEBUG", "system", message, module, details, exception, source)

    def info(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录INFO级别日志"""
        self.logger.info(message)
        self._log_to_database("INFO", "operation", message, module, details, exception, source)

    def warning(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录WARNING级别日志"""
        self.logger.warning(message)
        self._log_to_database("WARNING", "operation", message, module, details, exception, source)

    def error(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录ERROR级别日志"""
        self.logger.error(message)
        self._log_to_database("ERROR", "error", message, module, details, exception, source)

    def critical(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录CRITICAL级别日志"""
        self.logger.critical(message)
        self._log_to_database("CRITICAL", "error", message, module, details, exception, source)

    def security(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录安全相关日志"""
        self.logger.warning(f"SECURITY: {message}")
        self._log_to_database("WARNING", "security", message, module, details, exception, source)

    def database(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录数据库相关日志"""
        self.logger.error(f"DATABASE: {message}")
        self._log_to_database("ERROR", "database", message, module, details, exception, source)

    def sync(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录同步相关日志"""
        self.logger.info(f"SYNC: {message}")
        self._log_to_database("INFO", "sync", message, module, details, exception, source)

    def api(
        self,
        message: str,
        module: str | None = None,
        details: str | None = None,
        exception: Exception | None = None,
        source: str | None = None,
    ) -> None:
        """记录API相关日志"""
        self.logger.info(f"API: {message}")
        self._log_to_database("INFO", "api", message, module, details, exception, source)


# 创建全局日志记录器实例
enhanced_logger = EnhancedLogger()

# 创建专用日志记录器
auth_logger = EnhancedLogger("taifish.auth")
db_logger = EnhancedLogger("taifish.database")
sync_logger = EnhancedLogger("taifish.sync")
api_logger = EnhancedLogger("taifish.api")
security_logger = EnhancedLogger("taifish.security")
system_logger = EnhancedLogger("taifish.system")


def log_exception(
    exception: Exception, message: str | None = None, module: str | None = None, level: str = "ERROR"
) -> None:
    """记录异常的便捷函数"""
    if message is None:
        message = f"未处理的异常: {type(exception).__name__}"

    if level == "CRITICAL":
        enhanced_logger.critical(message, module, exception=exception)
    elif level == "WARNING":
        enhanced_logger.warning(message, module, exception=exception)
    else:
        enhanced_logger.error(message, module, exception=exception)


def log_database_error(
    operation: str, error: Exception, module: str | None = None, details: str | None = None
) -> None:
    """记录数据库错误的便捷函数"""
    message = f"数据库操作失败: {operation}"
    db_logger.database(message, module, details, error)


def log_sync_error(
    operation: str, error: Exception, module: str | None = None, details: str | None = None
) -> None:
    """记录同步错误的便捷函数"""
    message = f"同步操作失败: {operation}"
    sync_logger.error(message, module, details, error)


def log_api_error(endpoint: str, error: Exception, module: str | None = None, details: str | None = None) -> None:
    """记录API错误的便捷函数"""
    message = f"API调用失败: {endpoint}"
    api_logger.error(message, module, details, error)


def log_security_event(
    event: str, details: str | None = None, module: str | None = None, level: str = "WARNING"
) -> None:
    """记录安全事件的便捷函数"""
    if level == "ERROR":
        security_logger.error(f"安全事件: {event}", module, details)
    else:
        security_logger.security(f"安全事件: {event}", module, details)


# 应用日志记录器
def get_app_logger() -> logging.Logger:
    """
    获取应用日志记录器

    Returns:
        logging.Logger: 应用日志记录器
    """
    if current_app:
        return current_app.logger
    return logging.getLogger("taifish")


# 操作日志函数
def log_operation(operation_type: str, user_id: int | None = None, details: dict[str, Any] | None = None) -> None:
    """
    记录操作日志（安全版本）

    Args:
        operation_type: 操作类型
        user_id: 用户ID
        details: 操作详情
    """
    logger = get_app_logger()

    # 清理敏感信息
    safe_details = _sanitize_log_details(details) if details else {}

    log_data = {
        "operation_type": operation_type,
        "user_id": user_id,
        "timestamp": now().isoformat(),
        "details": safe_details,
    }

    logger.info(f"操作日志: {log_data}")

    # 同时保存到数据库
    try:
        from flask import request

        from app import db
        from app.models.log import Log

        log_entry = Log(  # type: ignore
            log_type="operation",
            level="INFO",
            module="system",
            message=f"操作: {operation_type}",
            details=str(safe_details) if safe_details else None,
            user_id=user_id,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
        )

        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        logger.error(f"保存操作日志到数据库失败: {e}")


def _sanitize_log_details(details: dict[str, Any]) -> dict[str, Any]:
    """
    清理日志中的敏感信息

    Args:
        details: 原始详情字典

    Returns:
        dict: 清理后的详情字典
    """
    if not isinstance(details, dict):
        return {}  # type: ignore

    sensitive_keys = ["password", "token", "secret", "key", "credential"]
    safe_details = {}

    for key, value in details.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            safe_details[key] = "[REDACTED]"
        else:
            safe_details[key] = value

    return safe_details


# 错误日志函数
def log_error(error: Exception, user_id: int | None = None, context: dict[str, Any] | None = None) -> None:
    """
    记录错误日志

    Args:
        error: 错误对象或错误信息
        user_id: 用户ID
        context: 错误上下文
    """
    logger = get_app_logger()

    error_data = {
        "error_type": (type(error).__name__ if hasattr(error, "__class__") else "Unknown"),
        "error_message": str(error),
        "user_id": user_id,
        "timestamp": now().isoformat(),
        "context": context or {},
    }

    logger.error(f"错误日志: {error_data}")


# API请求日志函数
def log_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    user_id: int | None = None,
    ip_address: str | None = None,
) -> None:
    """
    记录API请求日志

    Args:
        method: HTTP方法
        endpoint: API端点
        status_code: 状态码
        duration: 请求处理时间
        user_id: 用户ID
        ip_address: IP地址
    """
    logger = get_app_logger()

    api_data = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration": duration,
        "user_id": user_id,
        "ip_address": ip_address,
        "timestamp": now().isoformat(),
    }

    logger.info(f"API请求: {api_data}")


# 装饰器函数
def log_function_call(module: str | None = None, log_args: bool = False) -> Callable[[F], F]:
    """记录函数调用的装饰器"""

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            enhanced_logger.info(f"调用函数: {func_name}", module)

            if log_args:
                enhanced_logger.debug(f"函数参数: args={args}, kwargs={kwargs}", module)

            try:
                result = func(*args, **kwargs)
                enhanced_logger.info(f"函数执行成功: {func_name}", module)
                return result
            except Exception as e:
                enhanced_logger.error(f"函数执行失败: {func_name}", module, exception=e)
                raise

        return wrapper  # type: ignore

    return decorator


def log_database_operation(operation: str, module: str | None = None) -> Callable[[F], F]:
    """记录数据库操作的装饰器"""

    def decorator(func: F) -> F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                db_logger.info(f"数据库操作成功: {operation}", module)
                return result
            except Exception as e:
                db_logger.database(f"数据库操作失败: {operation}", module, exception=e)
                raise

        return wrapper  # type: ignore

    return decorator
