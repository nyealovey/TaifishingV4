#!/usr/bin/env python3

"""
数据库类型工具类
提供统一的数据库类型管理功能
"""

from typing import Any

from app.models.database_type_config import DatabaseTypeConfig
from app.services.database_type_service import DatabaseTypeService


class DatabaseTypeUtils:
    """数据库类型工具类"""

    @staticmethod
    def get_database_type_config(db_type: str) -> DatabaseTypeConfig | None:
        """
        获取数据库类型配置

        Args:
            db_type: 数据库类型名称

        Returns:
            数据库类型配置对象，如果不存在则返回None
        """
        try:
            return DatabaseTypeService.get_type_by_name(db_type)
        except Exception:
            return None

    @staticmethod
    def get_default_port(db_type: str) -> int | None:
        """
        获取数据库类型的默认端口

        Args:
            db_type: 数据库类型名称

        Returns:
            默认端口号，如果不存在则返回None
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        return config.default_port if config else None

    @staticmethod
    def get_display_name(db_type: str) -> str:
        """
        获取数据库类型的显示名称

        Args:
            db_type: 数据库类型名称

        Returns:
            显示名称，如果不存在则返回原始名称
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        return config.display_name if config else db_type

    @staticmethod
    def get_icon(db_type: str) -> str:
        """
        获取数据库类型的图标

        Args:
            db_type: 数据库类型名称

        Returns:
            图标类名，如果不存在则返回默认图标
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        return config.icon if config else "fa-database"

    @staticmethod
    def get_color(db_type: str) -> str:
        """
        获取数据库类型的颜色

        Args:
            db_type: 数据库类型名称

        Returns:
            颜色值，如果不存在则返回默认颜色
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        return config.color if config else "#6c757d"

    @staticmethod
    def get_features(db_type: str) -> list[str]:
        """
        获取数据库类型支持的功能特性

        Args:
            db_type: 数据库类型名称

        Returns:
            功能特性列表，如果不存在则返回空列表
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        return config.features_list if config else []

    @staticmethod
    def is_feature_supported(db_type: str, feature: str) -> bool:
        """
        检查数据库类型是否支持某个功能特性

        Args:
            db_type: 数据库类型名称
            feature: 功能特性名称

        Returns:
            是否支持该功能特性
        """
        features = DatabaseTypeUtils.get_features(db_type)
        return feature in features

    @staticmethod
    def get_all_active_types() -> list[DatabaseTypeConfig]:
        """
        获取所有激活的数据库类型

        Returns:
            激活的数据库类型配置列表
        """
        try:
            return DatabaseTypeService.get_active_types()
        except Exception:
            return []

    @staticmethod
    def get_database_type_info(db_type: str) -> dict[str, Any]:
        """
        获取数据库类型的完整信息

        Args:
            db_type: 数据库类型名称

        Returns:
            包含数据库类型信息的字典
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        if not config:
            return {
                "name": db_type,
                "display_name": db_type,
                "driver": "",
                "default_port": None,
                "default_schema": "",
                "description": "",
                "icon": "fa-database",
                "color": "#6c757d",
                "features": [],
                "is_active": False,
                "is_system": False,
            }

        return {
            "name": config.name,
            "display_name": config.display_name,
            "driver": config.driver,
            "default_port": config.default_port,
            "default_schema": config.default_schema,
            "description": config.description,
            "icon": config.icon,
            "color": config.color,
            "features": config.features_list,
            "is_active": config.is_active,
            "is_system": config.is_system,
        }

    @staticmethod
    def validate_database_type(db_type: str) -> bool:
        """
        验证数据库类型是否有效且激活

        Args:
            db_type: 数据库类型名称

        Returns:
            是否有效且激活
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        return config is not None and config.is_active

    @staticmethod
    def get_connection_info(db_type: str) -> dict[str, Any]:
        """
        获取数据库连接相关信息

        Args:
            db_type: 数据库类型名称

        Returns:
            连接信息字典
        """
        config = DatabaseTypeUtils.get_database_type_config(db_type)
        if not config:
            return {
                "driver": "",
                "default_port": None,
                "default_schema": "",
                "connection_string_template": "",
            }

        # 根据数据库类型生成连接字符串模板
        connection_templates = {
            "mysql": "mysql+pymysql://{username}:{password}@{host}:{port}/{database}",
            "postgresql": "postgresql+psycopg://{username}:{password}@{host}:{port}/{database}",
            "sqlserver": "mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server",
            "oracle": "oracle+oracledb://{username}:{password}@{host}:{port}/{database}",
        }

        return {
            "driver": config.driver,
            "default_port": config.default_port,
            "default_schema": config.default_schema,
            "connection_string_template": connection_templates.get(db_type, ""),
        }
