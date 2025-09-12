"""
泰摸鱼吧 - 安全头设置工具
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from flask import Response, make_response, request

logger = logging.getLogger(__name__)


class SecurityHeaders:
    """安全头管理器"""

    def __init__(self) -> None:
        self.headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": self._get_csp_policy(),
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    def _get_csp_policy(self) -> str:
        """获取内容安全策略"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    def apply_headers(self, response: Response) -> Response:
        """应用安全头"""
        for header, value in self.headers.items():
            response.headers[header] = value
        return response

    def set_custom_csp(self, policy: str) -> None:
        """设置自定义CSP策略"""
        self.headers["Content-Security-Policy"] = policy

    def add_header(self, name: str, value: str) -> None:
        """添加自定义安全头"""
        self.headers[name] = value

    def remove_header(self, name: str) -> None:
        """移除安全头"""
        self.headers.pop(name, None)


# 全局安全头管理器
security_headers = SecurityHeaders()


def security_headers_middleware(f: Callable[..., Any]) -> Callable[..., Any]:
    """安全头中间件装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        response = f(*args, **kwargs)

        # 确保响应是Response对象
        if not hasattr(response, "headers"):
            response = make_response(response)

        # 应用安全头
        response = security_headers.apply_headers(response)

        return response

    return decorated_function


def csp_report_only(f: Callable[..., Any]) -> Callable[..., Any]:
    """CSP报告模式装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        response = f(*args, **kwargs)

        if not hasattr(response, "headers"):
            response = make_response(response)

        # 设置CSP报告模式
        response.headers["Content-Security-Policy-Report-Only"] = security_headers.headers["Content-Security-Policy"]
        response.headers.pop("Content-Security-Policy", None)

        return response

    return decorated_function


def hsts_header(
    max_age: int = 31536000, include_subdomains: bool = True, preload: bool = False
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """HSTS头装饰器"""

    def security_decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            response = f(*args, **kwargs)

            if not hasattr(response, "headers"):
                response = make_response(response)

            # 构建HSTS头
            hsts_value = f"max-age={max_age}"
            if include_subdomains:
                hsts_value += "; includeSubDomains"
            if preload:
                hsts_value += "; preload"

            response.headers["Strict-Transport-Security"] = hsts_value

            return response

        return decorated_function

    return security_decorator


def no_cache_headers(f: Callable[..., Any]) -> Callable[..., Any]:
    """禁用缓存头装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        response = f(*args, **kwargs)

        if not hasattr(response, "headers"):
            response = make_response(response)

        # 设置禁用缓存头
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    return decorated_function


def api_security_headers(f: Callable[..., Any]) -> Callable[..., Any]:
    """API安全头装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        response = f(*args, **kwargs)

        if not hasattr(response, "headers"):
            response = make_response(response)

        # API特定安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

        return response

    return decorated_function


def cors_security_headers(f: Callable[..., Any]) -> Callable[..., Any]:
    """CORS安全头装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        response = f(*args, **kwargs)

        if not hasattr(response, "headers"):
            response = make_response(response)

        # CORS安全头
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken"
            response.headers["Access-Control-Max-Age"] = "86400"

        return response

    return decorated_function


def rate_limit_headers(
    limit: int, remaining: int, reset_time: int
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """速率限制头装饰器"""

    def security_decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            response = f(*args, **kwargs)

            if not hasattr(response, "headers"):
                response = make_response(response)

            # 速率限制头
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)

            return response

        return decorated_function

    return security_decorator


def security_audit_log(f: Callable[..., Any]) -> Callable[..., Any]:
    """安全审计日志装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # 记录请求信息
        client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        user_agent = request.headers.get("User-Agent", "")
        referer = request.headers.get("Referer", "")

        logger.info(f"安全审计 - IP: {client_ip}, User-Agent: {user_agent}, Referer: {referer}")

        response = f(*args, **kwargs)

        # 记录响应信息
        status_code = getattr(response, "status_code", 200)
        logger.info(f"安全审计 - 响应状态: {status_code}")

        return response

    return decorated_function


def validate_origin(f: Callable[..., Any]) -> Callable[..., Any]:
    """验证来源装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")

        # 允许的来源列表
        allowed_origins = [
            "http://localhost:5001",
            "http://127.0.0.1:5001",
            "https://taifish.example.com",
        ]

        if origin and origin not in allowed_origins:
            logger.warning(f"拒绝来源: {origin}")
            return make_response("Forbidden", 403)

        if referer and not any(allowed in referer for allowed in allowed_origins):
            logger.warning(f"拒绝引用: {referer}")
            return make_response("Forbidden", 403)

        return f(*args, **kwargs)

    return decorated_function


def csrf_protection(f: Callable[..., Any]) -> Callable[..., Any]:
    """CSRF保护装饰器"""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # 检查CSRF令牌
            csrf_token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
            session_csrf_token = request.cookies.get("csrf_token")

            if not csrf_token or csrf_token != session_csrf_token:
                logger.warning("CSRF令牌验证失败")
                return make_response("CSRF token mismatch", 403)

        return f(*args, **kwargs)

    return decorated_function


def setup_security_headers(app: Any) -> None:
    """设置应用安全头"""

    @app.after_request  # type: ignore[misc]
    def after_request(response: Response) -> Response:
        return security_headers.apply_headers(response)

    logger.info("安全头中间件已设置")


def get_security_report() -> Dict[str, Any]:
    """获取安全报告"""
    return {
        "headers": security_headers.headers,
        "csp_violations": [],  # 这里可以集成CSP违规报告
        "security_events": [],  # 这里可以集成安全事件日志
    }
