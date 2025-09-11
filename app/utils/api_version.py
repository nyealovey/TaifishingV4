# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - API版本控制工具
"""

from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class APIVersionManager:
    """API版本管理器"""

    def __init__(self):
        self.supported_versions = ["v1", "v2"]
        self.default_version = "v1"
        self.version_handlers = {}

    def register_version(self, version: str, handler_func):
        """注册版本处理器"""
        self.version_handlers[version] = handler_func
        logger.info(f"注册API版本处理器: {version}")

    def get_version_from_header(self) -> str:
        """从请求头获取版本"""
        version = request.headers.get("API-Version")
        if version and version in self.supported_versions:
            return version
        return self.default_version

    def get_version_from_url(self) -> str:
        """从URL获取版本"""
        path_parts = request.path.split("/")
        if len(path_parts) >= 3 and path_parts[1] == "api":
            version = path_parts[2]
            if version in self.supported_versions:
                return version
        return self.default_version

    def get_current_version(self) -> str:
        """获取当前API版本"""
        # 优先从URL获取
        version = self.get_version_from_url()
        if version != self.default_version:
            return version

        # 其次从请求头获取
        version = self.get_version_from_header()
        return version

    def is_version_supported(self, version: str) -> bool:
        """检查版本是否支持"""
        return version in self.supported_versions

    def get_version_info(self) -> Dict[str, Any]:
        """获取版本信息"""
        return {
            "supported_versions": self.supported_versions,
            "default_version": self.default_version,
            "current_version": self.get_current_version(),
        }


# 全局版本管理器
api_version_manager = APIVersionManager()


def api_version(version: str):
    """
    API版本装饰器

    Args:
        version: API版本
    """

    def version_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_version = api_version_manager.get_current_version()

            if current_version != version:
                return (
                    jsonify(
                        {
                            "error": "API版本不匹配",
                            "requested_version": version,
                            "current_version": current_version,
                            "supported_versions": api_version_manager.supported_versions,
                        }
                    ),
                    400,
                )

            return f(*args, **kwargs)

        return decorated_function

    return version_decorator


def versioned_api(versions: List[str]):
    """
    多版本API装饰器

    Args:
        versions: 支持的版本列表
    """

    def version_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_version = api_version_manager.get_current_version()

            if current_version not in versions:
                return (
                    jsonify(
                        {
                            "error": "API版本不支持",
                            "requested_version": current_version,
                            "supported_versions": versions,
                        }
                    ),
                    400,
                )

            # 将版本信息传递给处理函数
            kwargs["api_version"] = current_version
            return f(*args, **kwargs)

        return decorated_function

    return version_decorator


def deprecated_api(version: str, message: str = None):
    """
    废弃API装饰器

    Args:
        version: 废弃版本
        message: 废弃消息
    """

    def version_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_version = api_version_manager.get_current_version()

            if current_version == version:
                response = f(*args, **kwargs)
                if hasattr(response, "headers"):
                    response.headers["API-Deprecated"] = "true"
                    response.headers["API-Deprecated-Version"] = version
                    if message:
                        response.headers["API-Deprecated-Message"] = message
                return response

            return f(*args, **kwargs)

        return decorated_function

    return version_decorator


def api_version_info():
    """获取API版本信息"""
    return jsonify(api_version_manager.get_version_info())


# 版本兼容性处理
class VersionCompatibility:
    """版本兼容性处理"""

    @staticmethod
    def handle_request_data(
        data: Dict[str, Any], from_version: str, to_version: str
    ) -> Dict[str, Any]:
        """处理请求数据版本兼容性"""
        if from_version == to_version:
            return data

        # 版本转换逻辑
        if from_version == "v1" and to_version == "v2":
            return VersionCompatibility._v1_to_v2(data)
        elif from_version == "v2" and to_version == "v1":
            return VersionCompatibility._v2_to_v1(data)

        return data

    @staticmethod
    def handle_response_data(
        data: Dict[str, Any], from_version: str, to_version: str
    ) -> Dict[str, Any]:
        """处理响应数据版本兼容性"""
        if from_version == to_version:
            return data

        # 版本转换逻辑
        if from_version == "v2" and to_version == "v1":
            return VersionCompatibility._v2_to_v1(data)
        elif from_version == "v1" and to_version == "v2":
            return VersionCompatibility._v1_to_v2(data)

        return data

    @staticmethod
    def _v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
        """v1到v2的转换"""
        # 示例转换逻辑
        if "user_id" in data:
            data["user"] = {"id": data.pop("user_id")}

        return data

    @staticmethod
    def _v2_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
        """v2到v1的转换"""
        # 示例转换逻辑
        if "user" in data and isinstance(data["user"], dict):
            data["user_id"] = data["user"].get("id")
            data.pop("user")

        return data


# API版本路由注册
def register_version_routes(app):
    """注册版本路由"""

    @app.route("/api/version")
    def get_api_version():
        """获取API版本信息"""
        return api_version_info()

    @app.route("/api/v1/version")
    def get_v1_version():
        """获取v1版本信息"""
        return jsonify(
            {
                "version": "v1",
                "status": "supported",
                "endpoints": [
                    "/api/v1/users",
                    "/api/v1/instances",
                    "/api/v1/credentials",
                    "/api/v1/tasks",
                ],
            }
        )

    @app.route("/api/v2/version")
    def get_v2_version():
        """获取v2版本信息"""
        return jsonify(
            {
                "version": "v2",
                "status": "supported",
                "endpoints": [
                    "/api/v2/users",
                    "/api/v2/instances",
                    "/api/v2/credentials",
                    "/api/v2/tasks",
                    "/api/v2/accounts",
                    "/api/v2/logs",
                ],
                "features": [
                    "enhanced_user_management",
                    "advanced_task_scheduling",
                    "comprehensive_logging",
                    "account_synchronization",
                ],
            }
        )


# 版本中间件
def version_middleware():
    """版本中间件"""

    def middleware(response):
        current_version = api_version_manager.get_current_version()
        response.headers["API-Version"] = current_version
        response.headers["API-Supported-Versions"] = ", ".join(
            api_version_manager.supported_versions
        )
        return response

    return middleware
