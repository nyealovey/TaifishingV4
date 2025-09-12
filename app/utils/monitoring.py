"""
泰摸鱼吧 - 监控指标收集工具
"""

import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import psutil
from flask import g, request

from app import db

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()

    def collect_system_metrics(self) -> dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # 内存指标
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            memory_total = memory.total

            # 磁盘指标
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            disk_free = disk.free
            disk_total = disk.total

            # 网络指标
            network = psutil.net_io_counters()

            # 进程指标
            process = psutil.Process()
            process_memory = process.memory_info().rss
            process_cpu = process.cpu_percent()

            return {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu": {"percent": cpu_percent, "count": cpu_count},
                    "memory": {
                        "percent": memory_percent,
                        "available": memory_available,
                        "total": memory_total,
                        "used": memory_total - memory_available,
                    },
                    "disk": {
                        "percent": disk_percent,
                        "free": disk_free,
                        "total": disk_total,
                        "used": disk_total - disk_free,
                    },
                    "network": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv,
                    },
                },
                "application": {
                    "process_memory": process_memory,
                    "process_cpu": process_cpu,
                    "uptime": time.time() - self.start_time,
                },
            }
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return {}

    def collect_database_metrics(self) -> dict[str, Any]:
        """收集数据库指标"""
        try:
            from app.models.credential import Credential
            from app.models.instance import Instance
            from app.models.log import Log
            from app.models.task import Task
            from app.models.user import User

            # 数据库连接测试
            start_time = time.time()
            db.session.execute("SELECT 1")
            db_response_time = (time.time() - start_time) * 1000  # 毫秒

            # 统计各表记录数
            counts = {
                "users": User.query.count(),
                "instances": Instance.query.count(),
                "credentials": Credential.query.count(),
                "tasks": Task.query.count(),
                "logs": Log.query.count(),
            }

            # 活跃用户数（最近7天登录）
            week_ago = datetime.now() - timedelta(days=7)
            active_users = User.query.filter(User.last_login >= week_ago).count()

            # 活跃任务数
            active_tasks = Task.query.filter_by(is_active=True).count()

            # 最近24小时日志数
            day_ago = datetime.now() - timedelta(days=1)
            recent_logs = Log.query.filter(Log.created_at >= day_ago).count()

            return {
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "response_time_ms": db_response_time,
                    "status": "connected",
                    "table_counts": counts,
                    "active_users": active_users,
                    "active_tasks": active_tasks,
                    "recent_logs": recent_logs,
                },
            }
        except Exception as e:
            logger.error(f"收集数据库指标失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "database": {"status": "error", "error": str(e)},
            }

    def collect_application_metrics(self) -> dict[str, Any]:
        """收集应用指标"""
        try:
            # 请求统计
            request_count = getattr(g, "request_count", 0)
            error_count = getattr(g, "error_count", 0)

            # 缓存统计
            cache_hits = getattr(g, "cache_hits", 0)
            cache_misses = getattr(g, "cache_misses", 0)

            # 任务执行统计
            task_executions = getattr(g, "task_executions", 0)
            task_failures = getattr(g, "task_failures", 0)

            return {
                "timestamp": datetime.now().isoformat(),
                "application": {
                    "requests": {
                        "total": request_count,
                        "errors": error_count,
                        "success_rate": (request_count - error_count) / max(request_count, 1) * 100,
                    },
                    "cache": {
                        "hits": cache_hits,
                        "misses": cache_misses,
                        "hit_rate": cache_hits / max(cache_hits + cache_misses, 1) * 100,
                    },
                    "tasks": {
                        "executions": task_executions,
                        "failures": task_failures,
                        "success_rate": (task_executions - task_failures) / max(task_executions, 1) * 100,
                    },
                },
            }
        except Exception as e:
            logger.error(f"收集应用指标失败: {e}")
            return {}

    def collect_all_metrics(self) -> dict[str, Any]:
        """收集所有指标"""
        return {
            "system": self.collect_system_metrics(),
            "database": self.collect_database_metrics(),
            "application": self.collect_application_metrics(),
        }


# 全局指标收集器
metrics_collector = MetricsCollector()


def track_request_metrics(f):
    """请求指标跟踪装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        # 初始化请求指标
        if not hasattr(g, "request_count"):
            g.request_count = 0
        if not hasattr(g, "error_count"):
            g.error_count = 0

        g.request_count += 1

        try:
            result = f(*args, **kwargs)
            return result
        except Exception:
            g.error_count += 1
            raise
        finally:
            # 记录请求时间
            request_time = (time.time() - start_time) * 1000
            logger.debug(f"请求 {request.endpoint} 耗时: {request_time:.2f}ms")

    return decorated_function


def track_cache_metrics(cache_hit: bool):
    """缓存指标跟踪"""
    if not hasattr(g, "cache_hits"):
        g.cache_hits = 0
    if not hasattr(g, "cache_misses"):
        g.cache_misses = 0

    if cache_hit:
        g.cache_hits += 1
    else:
        g.cache_misses += 1


def track_task_metrics(success: bool):
    """任务指标跟踪"""
    if not hasattr(g, "task_executions"):
        g.task_executions = 0
    if not hasattr(g, "task_failures"):
        g.task_failures = 0

    g.task_executions += 1
    if not success:
        g.task_failures += 1


class HealthChecker:
    """健康检查器"""

    @staticmethod
    def check_database_health() -> dict[str, Any]:
        """检查数据库健康状态"""
        try:
            start_time = time.time()
            db.session.execute("SELECT 1")
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @staticmethod
    def check_redis_health() -> dict[str, Any]:
        """检查Redis健康状态"""
        try:
            from app import cache

            start_time = time.time()
            cache.cache._write_client.ping()
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @staticmethod
    def check_scheduler_health() -> dict[str, Any]:
        """检查APScheduler健康状态"""
        try:
            from app import scheduler

            start_time = time.time()
            is_running = scheduler.running
            response_time = (time.time() - start_time) * 1000

            if is_running:
                jobs = scheduler.get_jobs()
                return {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "jobs_count": len(jobs),
                    "timestamp": datetime.now().isoformat(),
                }
            return {
                "status": "unhealthy",
                "error": "Scheduler not running",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @staticmethod
    def check_overall_health() -> dict[str, Any]:
        """检查整体健康状态"""
        checks = {
            "database": HealthChecker.check_database_health(),
            "redis": HealthChecker.check_redis_health(),
            "scheduler": HealthChecker.check_scheduler_health(),
        }

        # 判断整体状态
        all_healthy = all(check["status"] == "healthy" for check in checks.values())

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }


# 监控数据存储
class MetricsStorage:
    """指标存储"""

    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.metrics_history = []

    def store_metrics(self, metrics: dict[str, Any]):
        """存储指标数据"""
        self.metrics_history.append(metrics)

        # 保持记录数量限制
        if len(self.metrics_history) > self.max_records:
            self.metrics_history = self.metrics_history[-self.max_records :]

    def get_metrics_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """获取历史指标数据"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            metrics
            for metrics in self.metrics_history
            if datetime.fromisoformat(metrics.get("timestamp", "1970-01-01T00:00:00")) >= cutoff_time
        ]

    def get_latest_metrics(self) -> dict[str, Any] | None:
        """获取最新指标数据"""
        return self.metrics_history[-1] if self.metrics_history else None


# 全局指标存储
metrics_storage = MetricsStorage()


def collect_and_store_metrics():
    """收集并存储指标"""
    try:
        metrics = metrics_collector.collect_all_metrics()
        metrics_storage.store_metrics(metrics)
        return True
    except Exception as e:
        logger.error(f"收集和存储指标失败: {e}")
        return False
