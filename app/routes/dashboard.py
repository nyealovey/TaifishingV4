# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 系统仪表板路由
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.instance import Instance
from app.models.credential import Credential
from app.models.task import Task
from app.models.log import Log
from app.models.sync_data import SyncData
from app import db
import logging
from datetime import datetime, timedelta
import psutil
import os
from sqlalchemy import text
from app.utils.timezone import (
    get_china_time,
    utc_to_china,
    format_china_time,
    get_china_today,
    get_china_date,
    china_to_utc,
    CHINA_TZ,
)
from app.utils.cache_manager import (
    cached,
    cache_dashboard_data,
    get_cached_dashboard_data,
    invalidate_dashboard_cache,
)
from app.utils.enhanced_logger import log_operation, log_api_request

# 创建蓝图
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """系统仪表板首页"""
    import time

    start_time = time.time()

    # 获取系统概览数据
    overview_data = get_system_overview()

    # 获取图表数据
    chart_data = get_chart_data()

    # 获取最近活动
    recent_activities = get_recent_activities()

    # 获取系统状态
    system_status = get_system_status()

    # 记录操作日志
    duration = (time.time() - start_time) * 1000
    log_operation(
        "DASHBOARD_VIEW",
        current_user.id,
        {
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "duration_ms": duration,
        },
    )

    if request.is_json:
        return jsonify(
            {
                "overview": overview_data,
                "charts": chart_data,
                "activities": recent_activities,
                "status": system_status,
            }
        )

    return render_template(
        "dashboard/index.html",
        overview=overview_data,
        charts=chart_data,
        activities=recent_activities,
        status=system_status,
    )


@dashboard_bp.route("/api/overview")
@login_required
def api_overview():
    """获取系统概览API"""
    import time

    start_time = time.time()

    overview = get_system_overview()

    # 记录API调用
    duration = (time.time() - start_time) * 1000
    log_api_request(
        "GET",
        "/dashboard/api/overview",
        200,
        duration,
        current_user.id,
        request.remote_addr,
    )

    return jsonify(overview)


@dashboard_bp.route("/api/charts")
@login_required
def api_charts():
    """获取图表数据API"""
    import time

    start_time = time.time()

    chart_type = request.args.get("type", "all", type=str)
    charts = get_chart_data(chart_type)

    # 记录API调用
    duration = (time.time() - start_time) * 1000
    log_api_request(
        "GET",
        "/dashboard/api/charts",
        200,
        duration,
        current_user.id,
        request.remote_addr,
    )

    return jsonify(charts)


@dashboard_bp.route("/api/activities")
@login_required
def api_activities():
    """获取最近活动API"""
    import time

    start_time = time.time()

    limit = request.args.get("limit", 10, type=int)
    activities = get_recent_activities(limit)

    # 记录API调用
    duration = (time.time() - start_time) * 1000
    log_api_request(
        "GET",
        "/dashboard/api/activities",
        200,
        duration,
        current_user.id,
        request.remote_addr,
    )

    return jsonify(activities)


@dashboard_bp.route("/api/status")
@login_required
def api_status():
    """获取系统状态API"""
    import time

    start_time = time.time()

    status = get_system_status()

    # 记录API调用
    duration = (time.time() - start_time) * 1000
    log_api_request(
        "GET",
        "/dashboard/api/status",
        200,
        duration,
        current_user.id,
        request.remote_addr,
    )

    return jsonify(status)


@cached(timeout=300, key_prefix="dashboard")
def get_system_overview():
    """获取系统概览数据（缓存版本）"""
    try:
        # 基础统计
        total_users = User.query.count()
        total_instances = Instance.query.count()
        total_credentials = Credential.query.count()
        total_tasks = Task.query.count()
        total_logs = Log.query.count()

        # 活跃实例数
        active_instances = Instance.query.filter_by(is_active=True).count()

        # 活跃任务数
        active_tasks = Task.query.filter_by(is_active=True).count()

        # 今日日志数（东八区）
        today = get_china_today().date()
        today_logs = Log.query.filter(db.func.date(Log.created_at) == today).count()

        # 错误日志数
        error_logs = Log.query.filter(Log.level.in_(["ERROR", "CRITICAL"])).count()

        # 最近同步数据（东八区）
        recent_syncs = SyncData.query.filter(
            SyncData.sync_time >= get_china_today() - timedelta(days=7)
        ).count()

        return {
            "users": {"total": total_users, "active": total_users},  # 简化处理
            "instances": {"total": total_instances, "active": active_instances},
            "credentials": {
                "total": total_credentials,
                "active": total_credentials,  # 简化处理
            },
            "tasks": {"total": total_tasks, "active": active_tasks},
            "logs": {"total": total_logs, "today": today_logs, "errors": error_logs},
            "syncs": {"recent": recent_syncs},
        }
    except Exception as e:
        logging.error(f"获取系统概览失败: {e}")
        return {
            "users": {"total": 0, "active": 0},
            "instances": {"total": 0, "active": 0},
            "credentials": {"total": 0, "active": 0},
            "tasks": {"total": 0, "active": 0},
            "logs": {"total": 0, "today": 0, "errors": 0},
            "syncs": {"recent": 0},
        }


def get_chart_data(chart_type="all"):
    """获取图表数据"""
    try:
        charts = {}

        if chart_type in ["all", "logs"]:
            # 日志趋势图（最近7天）
            charts["log_trend"] = get_log_trend_data()

            # 日志级别分布
            charts["log_levels"] = get_log_level_distribution()

        if chart_type in ["all", "instances"]:
            # 实例类型分布
            charts["instance_types"] = get_instance_type_distribution()

        if chart_type in ["all", "tasks"]:
            # 任务状态分布
            charts["task_status"] = get_task_status_distribution()

        if chart_type in ["all", "syncs"]:
            # 同步趋势图
            charts["sync_trend"] = get_sync_trend_data()

        return charts
    except Exception as e:
        logging.error(f"获取图表数据失败: {e}")
        return {}


def get_log_trend_data():
    """获取日志趋势数据（分别显示错误和告警日志）"""
    try:
        # 最近7天的日志数据（东八区）
        china_today = get_china_date()
        start_date = china_today - timedelta(days=6)

        trend_data = []
        for i in range(7):
            date = start_date + timedelta(days=i)

            # 计算该日期的UTC时间范围（东八区转UTC）
            start_utc = china_to_utc(
                CHINA_TZ.localize(datetime.combine(date, datetime.min.time()))
            )
            end_utc = china_to_utc(
                CHINA_TZ.localize(datetime.combine(date, datetime.max.time()))
            )

            # 分别统计错误日志和告警日志
            error_count = Log.query.filter(
                Log.created_at >= start_utc, 
                Log.created_at <= end_utc,
                Log.level.in_(["ERROR", "CRITICAL"])
            ).count()
            
            warning_count = Log.query.filter(
                Log.created_at >= start_utc, 
                Log.created_at <= end_utc,
                Log.level == "WARNING"
            ).count()

            trend_data.append({
                "date": date.strftime("%Y-%m-%d"), 
                "error_count": error_count,
                "warning_count": warning_count
            })

        return trend_data
    except Exception as e:
        logging.error(f"获取日志趋势数据失败: {e}")
        return []


def get_log_level_distribution():
    """获取日志级别分布（只显示错误和告警日志）"""
    try:
        level_stats = (
            db.session.query(Log.level, db.func.count(Log.id).label("count"))
            .filter(Log.level.in_(["ERROR", "WARNING", "CRITICAL"]))
            .group_by(Log.level)
            .all()
        )

        return [{"level": stat.level, "count": stat.count} for stat in level_stats]
    except Exception as e:
        logging.error(f"获取日志级别分布失败: {e}")
        return []


def get_instance_type_distribution():
    """获取实例类型分布"""
    try:
        type_stats = (
            db.session.query(
                Instance.db_type, db.func.count(Instance.id).label("count")
            )
            .group_by(Instance.db_type)
            .all()
        )

        return [{"type": stat.db_type, "count": stat.count} for stat in type_stats]
    except Exception as e:
        logging.error(f"获取实例类型分布失败: {e}")
        return []


def get_task_status_distribution():
    """获取任务状态分布"""
    try:
        status_stats = (
            db.session.query(Task.last_status, db.func.count(Task.id).label("count"))
            .group_by(Task.last_status)
            .all()
        )

        return [
            {"status": stat.last_status or "unknown", "count": stat.count}
            for stat in status_stats
        ]
    except Exception as e:
        logging.error(f"获取任务状态分布失败: {e}")
        return []


def get_sync_trend_data():
    """获取同步趋势数据"""
    try:
        # 最近7天的同步数据（东八区）
        end_date = get_china_today().date()
        start_date = end_date - timedelta(days=6)

        trend_data = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            count = SyncData.query.filter(
                db.func.date(SyncData.sync_time) == date
            ).count()
            trend_data.append({"date": date.strftime("%Y-%m-%d"), "count": count})

        return trend_data
    except Exception as e:
        logging.error(f"获取同步趋势数据失败: {e}")
        return []


def get_recent_activities(limit=10):
    """获取最近活动（优化版本）"""
    try:
        # 使用join查询避免N+1问题
        recent_logs = (
            db.session.query(Log)
            .join(User, Log.user_id == User.id, isouter=True)
            .order_by(Log.created_at.desc())
            .limit(limit)
            .all()
        )

        activities = []
        for log in recent_logs:
            activities.append(
                {
                    "id": log.id,
                    "type": "log",
                    "level": log.level,
                    "message": log.message,
                    "module": log.module,
                    "user": log.user.username if log.user else "系统",
                    "time": log.created_at.isoformat() if log.created_at else None,
                    "icon": get_activity_icon(log.level, log.log_type),
                }
            )

        return activities
    except Exception as e:
        logging.error(f"获取最近活动失败: {e}")
        return []


def get_activity_icon(level, log_type):
    """获取活动图标"""
    if log_type == "security":
        return "fas fa-shield-alt"
    elif log_type == "error":
        return "fas fa-exclamation-triangle"
    elif log_type == "system":
        return "fas fa-cog"
    elif level == "ERROR":
        return "fas fa-times-circle"
    elif level == "WARNING":
        return "fas fa-exclamation-triangle"
    elif level == "INFO":
        return "fas fa-info-circle"
    else:
        return "fas fa-circle"


def get_system_status():
    """获取系统状态"""
    try:
        # 系统资源状态
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # 数据库状态
        db_status = "healthy"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            db_status = "error"

        # Redis状态
        redis_status = "healthy"
        try:
            from flask import current_app

            redis_client = getattr(current_app, "redis_client", None)
            if redis_client:
                redis_client.ping()
            else:
                redis_status = "error"
        except Exception as e:
            logging.warning(f"Redis连接检查失败: {e}")
            redis_status = "error"

        # 应用状态
        app_status = "running"

        return {
            "system": {
                "cpu": cpu_percent,
                "memory": {
                    "used": memory.used,
                    "total": memory.total,
                    "percent": memory.percent,
                },
                "disk": {
                    "used": disk.used,
                    "total": disk.total,
                    "percent": (disk.used / disk.total) * 100,
                },
            },
            "services": {
                "database": db_status,
                "redis": redis_status,
                "application": app_status,
            },
            "uptime": get_system_uptime(),
        }
    except Exception as e:
        logging.error(f"获取系统状态失败: {e}")
        return {
            "system": {
                "cpu": 0,
                "memory": {"used": 0, "total": 0, "percent": 0},
                "disk": {"used": 0, "total": 0, "percent": 0},
            },
            "services": {
                "database": "unknown",
                "redis": "unknown",
                "application": "unknown",
            },
            "uptime": "unknown",
        }


def get_system_uptime():
    """获取系统运行时间"""
    try:
        uptime_seconds = psutil.boot_time()
        uptime = get_china_time() - datetime.fromtimestamp(uptime_seconds)

        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return f"{days}天 {hours}小时 {minutes}分钟"
    except Exception:
        return "未知"
