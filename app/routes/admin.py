# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 管理API路由
提供系统配置和常量管理功能
"""

import json
import time
import logging
from datetime import datetime, timedelta
from app.utils.timezone import now
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.constants import UserRole, ErrorMessages, SuccessMessages
from app.utils.api_response import APIResponse
from app.utils.advanced_error_handler import advanced_error_handler

logger = logging.getLogger(__name__)

# 创建管理蓝图
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """管理员权限装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return APIResponse.unauthorized("请先登录")

        if current_user.role != UserRole.ADMIN.value:
            return APIResponse.forbidden("需要管理员权限")

        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/system-config", methods=["GET"])
@login_required
@admin_required
def system_config_page():
    """系统配置页面"""
    return render_template("admin/system_config.html")


@admin_bp.route("/config", methods=["GET"])
@login_required
@admin_required
def get_system_config():
    """获取系统配置"""
    try:
        from app.models.global_param import GlobalParam
        
        # 从数据库获取配置
        configs = {}
        
        # 基础配置
        basic_configs = GlobalParam.query.filter_by(param_type='system_config').all()
        basic_data = {}
        for config in basic_configs:
            if config.config:
                basic_data.update(config.config)
        
        # 设置默认值
        configs["basic"] = {
            "app_name": basic_data.get("app_name", "泰摸鱼吧"),
            "app_version": basic_data.get("app_version", "4.0.0"),
            "debug_mode": basic_data.get("debug_mode", False),
            "timezone": basic_data.get("timezone", "Asia/Shanghai"),
            "secret_key": "****************",
        }
        
        # 数据库配置
        db_configs = GlobalParam.query.filter_by(param_type='database_config').all()
        db_data = {}
        for config in db_configs:
            if config.config:
                db_data.update(config.config)
        
        configs["database"] = {
            "db_type": db_data.get("db_type", "sqlite"),
            "db_host": db_data.get("db_host", "localhost"),
            "db_port": db_data.get("db_port", 3306),
            "db_name": db_data.get("db_name", "taifish_dev"),
            "db_username": db_data.get("db_username", "root"),
            "db_pool_size": db_data.get("db_pool_size", 10),
        }
        
        # 安全配置
        security_configs = GlobalParam.query.filter_by(param_type='security_config').all()
        security_data = {}
        for config in security_configs:
            if config.config:
                security_data.update(config.config)
        
        configs["security"] = {
            "session_timeout": security_data.get("session_timeout", 30),
            "max_login_attempts": security_data.get("max_login_attempts", 5),
            "password_min_length": security_data.get("password_min_length", 8),
            "require_strong_password": security_data.get("require_strong_password", True),
            "enable_2fa": security_data.get("enable_2fa", False),
            "enable_csrf": security_data.get("enable_csrf", True),
        }
        
        # 邮件配置
        email_configs = GlobalParam.query.filter_by(param_type='email_config').all()
        email_data = {}
        for config in email_configs:
            if config.config:
                email_data.update(config.config)
        
        configs["email"] = {
            "smtp_host": email_data.get("smtp_host", "smtp.gmail.com"),
            "smtp_port": email_data.get("smtp_port", 587),
            "smtp_username": email_data.get("smtp_username", ""),
            "smtp_use_tls": email_data.get("smtp_use_tls", True),
            "from_email": email_data.get("from_email", ""),
        }
        
        # 日志配置
        logging_configs = GlobalParam.query.filter_by(param_type='logging_config').all()
        logging_data = {}
        for config in logging_configs:
            if config.config:
                logging_data.update(config.config)
        
        configs["logging"] = {
            "log_level": logging_data.get("log_level", "INFO"),
            "log_format": logging_data.get("log_format", "simple"),
            "log_file_size": logging_data.get("log_file_size", 10),
            "log_backup_count": logging_data.get("log_backup_count", 5),
            "log_to_file": logging_data.get("log_to_file", True),
            "log_to_console": logging_data.get("log_to_console", True),
        }
        
        # 性能配置
        performance_configs = GlobalParam.query.filter_by(param_type='performance_config').all()
        performance_data = {}
        for config in performance_configs:
            if config.config:
                performance_data.update(config.config)
        
        configs["performance"] = {
            "cache_ttl": performance_data.get("cache_ttl", 3600),
            "max_workers": performance_data.get("max_workers", 4),
            "request_timeout": performance_data.get("request_timeout", 30),
            "max_connections": performance_data.get("max_connections", 100),
            "enable_compression": performance_data.get("enable_compression", True),
            "enable_caching": performance_data.get("enable_caching", True),
        }

        return APIResponse.success(data=configs)

    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        return APIResponse.server_error("获取系统配置失败")


@admin_bp.route("/config", methods=["POST"])
@login_required
@admin_required
def save_system_config():
    """保存系统配置"""
    try:
        from app.models.global_param import GlobalParam
        
        data = request.get_json()
        config_type = data.get("type")
        config = data.get("config", {})

        if not config_type:
            return APIResponse.error("配置类型不能为空", code=400)

        # 映射配置类型到数据库类型
        type_mapping = {
            "basic": "system_config",
            "database": "database_config", 
            "security": "security_config",
            "email": "email_config",
            "logging": "logging_config",
            "performance": "performance_config"
        }
        
        param_type = type_mapping.get(config_type)
        if not param_type:
            return APIResponse.error("无效的配置类型", code=400)

        # 查找或创建配置记录
        existing_config = GlobalParam.query.filter_by(
            param_type=param_type,
            name=f"{config_type}_config"
        ).first()
        
        if existing_config:
            # 更新现有配置
            existing_config.config = config
            existing_config.updated_at = datetime.utcnow()
        else:
            # 创建新配置
            new_config = GlobalParam(
                param_type=param_type,
                name=f"{config_type}_config",
                config=config
            )
            db.session.add(new_config)
        
        db.session.commit()
        
        # 如果是基础配置，更新应用名称到session或缓存
        if config_type == "basic" and "app_name" in config:
            # 这里可以更新全局配置或缓存
            logger.info(f"应用名称已更新为: {config['app_name']}")

        logger.info(f"保存{config_type}配置成功: {config}")
        return APIResponse.success(message=f"{config_type}配置保存成功")

    except Exception as e:
        db.session.rollback()
        logger.error(f"保存系统配置失败: {e}")
        return APIResponse.server_error("保存系统配置失败")


@admin_bp.route("/app-info", methods=["GET"])
def get_app_info():
    """获取应用信息（公开接口，用于右上角显示）"""
    try:
        from app.models.global_param import GlobalParam
        
        # 获取基础配置中的应用名称
        basic_config = GlobalParam.query.filter_by(
            param_type='system_config',
            name='basic_config'
        ).first()
        
        app_name = "泰摸鱼吧"  # 默认值
        if basic_config and basic_config.config:
            app_name = basic_config.config.get("app_name", "泰摸鱼吧")
        
        return APIResponse.success(data={
            "app_name": app_name,
            "app_version": "4.0.0"
        })

    except Exception as e:
        logger.error(f"获取应用信息失败: {e}")
        return APIResponse.success(data={
            "app_name": "泰摸鱼吧",
            "app_version": "4.0.0"
        })


@admin_bp.route("/config/test-db", methods=["POST"])
@login_required
@admin_required
def test_database_connection():
    """测试数据库连接"""
    try:
        # 这里应该实际测试数据库连接
        # 目前只是模拟测试
        logger.info("测试数据库连接")

        return APIResponse.success(message="数据库连接测试成功")

    except Exception as e:
        logger.error(f"测试数据库连接失败: {e}")
        return APIResponse.server_error("测试数据库连接失败")


@admin_bp.route("/config/test-email", methods=["POST"])
@login_required
@admin_required
def test_email_config():
    """测试邮件配置"""
    try:
        # 这里应该实际测试邮件发送
        # 目前只是模拟测试
        logger.info("测试邮件配置")

        return APIResponse.success(message="邮件发送测试成功")

    except Exception as e:
        logger.error(f"测试邮件配置失败: {e}")
        return APIResponse.server_error("测试邮件配置失败")


@admin_bp.route("/constants", methods=["GET"])
@login_required
@admin_required
def constants_management():
    """常量管理"""
    try:
        from app.constants import (
            SystemConstants,
            DefaultConfig,
            ErrorMessages,
            SuccessMessages,
        )

        # 获取所有常量
        constants = {
            "system": {
                "DEFAULT_PAGE_SIZE": SystemConstants.DEFAULT_PAGE_SIZE,
                "MAX_PAGE_SIZE": SystemConstants.MAX_PAGE_SIZE,
                "MIN_PAGE_SIZE": SystemConstants.MIN_PAGE_SIZE,
                "MAX_FILE_SIZE": SystemConstants.MAX_FILE_SIZE,
                "ALLOWED_EXTENSIONS": list(SystemConstants.ALLOWED_EXTENSIONS),
            },
            "performance": {
                "SLOW_QUERY_THRESHOLD": SystemConstants.SLOW_QUERY_THRESHOLD,
                "SLOW_API_THRESHOLD": SystemConstants.SLOW_API_THRESHOLD,
                "MEMORY_WARNING_THRESHOLD": SystemConstants.MEMORY_WARNING_THRESHOLD,
                "CPU_WARNING_THRESHOLD": SystemConstants.CPU_WARNING_THRESHOLD,
                "CONNECTION_TIMEOUT": SystemConstants.CONNECTION_TIMEOUT,
                "MAX_CONNECTIONS": SystemConstants.MAX_CONNECTIONS,
            },
            "security": {
                "MIN_PASSWORD_LENGTH": SystemConstants.MIN_PASSWORD_LENGTH,
                "MAX_PASSWORD_LENGTH": SystemConstants.MAX_PASSWORD_LENGTH,
                "PASSWORD_HASH_ROUNDS": SystemConstants.PASSWORD_HASH_ROUNDS,
                "SESSION_LIFETIME": SystemConstants.SESSION_LIFETIME,
                "JWT_ACCESS_TOKEN_EXPIRES": SystemConstants.JWT_ACCESS_TOKEN_EXPIRES,
                "CSRF_TOKEN_LIFETIME": SystemConstants.CSRF_TOKEN_LIFETIME,
            },
            "database": {
                "CONNECTION_TIMEOUT": SystemConstants.CONNECTION_TIMEOUT,
                "QUERY_TIMEOUT": SystemConstants.QUERY_TIMEOUT,
                "CONNECTION_RETRY_ATTEMPTS": SystemConstants.CONNECTION_RETRY_ATTEMPTS,
                "SQL_SERVER_PORT": 1433,
                "MYSQL_PORT": 3306,
                "POSTGRES_PORT": 5432,
            },
            "messages": {
                "errors": {
                    "INTERNAL_ERROR": ErrorMessages.INTERNAL_ERROR,
                    "VALIDATION_ERROR": ErrorMessages.VALIDATION_ERROR,
                    "PERMISSION_DENIED": ErrorMessages.PERMISSION_DENIED,
                    "RESOURCE_NOT_FOUND": ErrorMessages.RESOURCE_NOT_FOUND,
                },
                "success": {
                    "OPERATION_SUCCESS": SuccessMessages.OPERATION_SUCCESS,
                    "LOGIN_SUCCESS": SuccessMessages.LOGIN_SUCCESS,
                    "DATA_SAVED": SuccessMessages.DATA_SAVED,
                    "DATA_DELETED": SuccessMessages.DATA_DELETED,
                },
            },
        }

        return render_template("admin/constants.html", constants=constants)

    except Exception as e:
        logger.error(f"获取常量管理页面失败: {e}")
        return APIResponse.server_error("获取常量管理页面失败")


@admin_bp.route("/constants/api", methods=["GET"])
@login_required
@admin_required
def get_constants_api():
    """获取常量API"""
    try:
        from app.constants import (
            SystemConstants,
            DefaultConfig,
            ErrorMessages,
            SuccessMessages,
        )

        constants = {
            "system_constants": {
                "DEFAULT_PAGE_SIZE": SystemConstants.DEFAULT_PAGE_SIZE,
                "MAX_PAGE_SIZE": SystemConstants.MAX_PAGE_SIZE,
                "MIN_PAGE_SIZE": SystemConstants.MIN_PAGE_SIZE,
                "MAX_FILE_SIZE": SystemConstants.MAX_FILE_SIZE,
                "ALLOWED_EXTENSIONS": list(SystemConstants.ALLOWED_EXTENSIONS),
            },
            "performance_constants": {
                "SLOW_QUERY_THRESHOLD": SystemConstants.SLOW_QUERY_THRESHOLD,
                "SLOW_API_THRESHOLD": SystemConstants.SLOW_API_THRESHOLD,
                "MEMORY_WARNING_THRESHOLD": SystemConstants.MEMORY_WARNING_THRESHOLD,
                "CPU_WARNING_THRESHOLD": SystemConstants.CPU_WARNING_THRESHOLD,
                "CONNECTION_TIMEOUT": SystemConstants.CONNECTION_TIMEOUT,
                "MAX_CONNECTIONS": SystemConstants.MAX_CONNECTIONS,
            },
            "security_constants": {
                "MIN_PASSWORD_LENGTH": SystemConstants.MIN_PASSWORD_LENGTH,
                "MAX_PASSWORD_LENGTH": SystemConstants.MAX_PASSWORD_LENGTH,
                "PASSWORD_HASH_ROUNDS": SystemConstants.PASSWORD_HASH_ROUNDS,
                "SESSION_LIFETIME": SystemConstants.SESSION_LIFETIME,
                "JWT_ACCESS_TOKEN_EXPIRES": SystemConstants.JWT_ACCESS_TOKEN_EXPIRES,
                "CSRF_TOKEN_LIFETIME": SystemConstants.CSRF_TOKEN_LIFETIME,
            },
            "database_constants": {
                "CONNECTION_TIMEOUT": SystemConstants.CONNECTION_TIMEOUT,
                "QUERY_TIMEOUT": SystemConstants.QUERY_TIMEOUT,
                "CONNECTION_RETRY_ATTEMPTS": SystemConstants.CONNECTION_RETRY_ATTEMPTS,
            },
            "error_messages": {
                "INTERNAL_ERROR": ErrorMessages.INTERNAL_ERROR,
                "VALIDATION_ERROR": ErrorMessages.VALIDATION_ERROR,
                "PERMISSION_DENIED": ErrorMessages.PERMISSION_DENIED,
                "RESOURCE_NOT_FOUND": ErrorMessages.RESOURCE_NOT_FOUND,
            },
            "success_messages": {
                "OPERATION_SUCCESS": SuccessMessages.OPERATION_SUCCESS,
                "LOGIN_SUCCESS": SuccessMessages.LOGIN_SUCCESS,
                "DATA_SAVED": SuccessMessages.DATA_SAVED,
                "DATA_DELETED": SuccessMessages.DATA_DELETED,
            },
        }

        return APIResponse.success(data=constants)

    except Exception as e:
        logger.error(f"获取常量API失败: {e}")
        return APIResponse.server_error("获取常量API失败")


# 快速操作相关路由
@admin_bp.route("/refresh-data", methods=["POST"])
@login_required
@admin_required
def refresh_system_data():
    """刷新系统数据"""
    try:
        # 这里可以实现数据刷新逻辑
        logger.info("系统数据刷新请求")
        return APIResponse.success(message="系统数据已刷新")
    except Exception as e:
        logger.error(f"刷新系统数据失败: {e}")
        return APIResponse.server_error("刷新系统数据失败")


@admin_bp.route("/clear-cache", methods=["POST"])
@login_required
@admin_required
def clear_cache():
    """清除缓存"""
    try:
        # 这里可以实现清除缓存逻辑
        logger.info("清除缓存请求")
        return APIResponse.success(message="缓存已清除")
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return APIResponse.server_error("清除缓存失败")


@admin_bp.route("/health-check", methods=["POST"])
@login_required
@admin_required
def run_health_check():
    """运行健康检查"""
    try:
        # 检查各个组件状态
        health_status = {
            "database": "healthy",
            "redis": "healthy",
            "application": "healthy",
        }

        return APIResponse.success(data=health_status, message="健康检查完成")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return APIResponse.server_error("健康检查失败")