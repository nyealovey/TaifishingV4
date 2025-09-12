"""
泰摸鱼吧 - 数据库查询优化工具
"""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from sqlalchemy import or_

from app import db
from app.constants import SystemConstants

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """查询优化器"""

    def __init__(self):
        self.query_cache = {}
        self.slow_query_threshold = SystemConstants.SLOW_QUERY_THRESHOLD  # 慢查询阈值（秒）
        self.query_stats = {}

    def optimize_query(self, query_func: Callable) -> Callable:
        """查询优化装饰器"""

        @wraps(query_func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = query_func(*args, **kwargs)

                # 记录查询时间
                execution_time = time.time() - start_time
                self._record_query_stats(query_func.__name__, execution_time, True)

                # 检查是否为慢查询
                if execution_time > self.slow_query_threshold:
                    logger.warning(f"慢查询检测: {query_func.__name__} 耗时 {execution_time:.2f}秒")

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                self._record_query_stats(query_func.__name__, execution_time, False)
                logger.error(f"查询失败: {query_func.__name__}, 耗时: {execution_time:.2f}秒, 错误: {e}")
                raise

        return wrapper

    def _record_query_stats(self, query_name: str, execution_time: float, success: bool):
        """记录查询统计"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                "count": 0,
                "total_time": 0.0,
                "success_count": 0,
                "failure_count": 0,
                "avg_time": 0.0,
                "max_time": 0.0,
                "min_time": float("inf"),
            }

        stats = self.query_stats[query_name]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["min_time"] = min(stats["min_time"], execution_time)

        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1

        stats["avg_time"] = stats["total_time"] / stats["count"]

    def get_query_stats(self) -> dict[str, Any]:
        """获取查询统计"""
        return self.query_stats

    def get_slow_queries(self) -> list[dict[str, Any]]:
        """获取慢查询列表"""
        slow_queries = []
        for query_name, stats in self.query_stats.items():
            if stats["avg_time"] > self.slow_query_threshold:
                slow_queries.append(
                    {
                        "query_name": query_name,
                        "avg_time": stats["avg_time"],
                        "max_time": stats["max_time"],
                        "count": stats["count"],
                        "success_rate": (stats["success_count"] / stats["count"] if stats["count"] > 0 else 0),
                    }
                )

        return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)


# 全局查询优化器
query_optimizer = QueryOptimizer()


def optimize_query(func: Callable) -> Callable:
    """查询优化装饰器"""
    return query_optimizer.optimize_query(func)


# 查询构建器
class QueryBuilder:
    """查询构建器"""

    @staticmethod
    def build_user_query(
        filters: dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
    ):
        """构建用户查询"""
        from app.models.user import User

        query = User.query

        if filters:
            if "role" in filters:
                query = query.filter(User.role == filters["role"])
            if "is_active" in filters:
                query = query.filter(User.is_active == filters["is_active"])
            if "search" in filters and filters["search"]:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(User.username.like(search_term), User.email.like(search_term)))

        if order_by:
            if order_by == "username":
                query = query.order_by(User.username)
            elif order_by == "created_at":
                query = query.order_by(User.created_at.desc())
            elif order_by == "last_login":
                query = query.order_by(User.last_login.desc().nullslast())

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query

    @staticmethod
    def build_instance_query(
        filters: dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
    ):
        """构建实例查询"""
        from app.models.instance import Instance

        query = Instance.query

        if filters:
            if "db_type" in filters:
                query = query.filter(Instance.db_type == filters["db_type"])
            if "is_active" in filters:
                query = query.filter(Instance.is_active == filters["is_active"])
            if "search" in filters and filters["search"]:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(Instance.name.like(search_term), Instance.host.like(search_term)))

        if order_by:
            if order_by == "name":
                query = query.order_by(Instance.name)
            elif order_by == "created_at":
                query = query.order_by(Instance.created_at.desc())
            elif order_by == "last_connected":
                query = query.order_by(Instance.last_connected.desc().nullslast())

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query

    @staticmethod
    def build_log_query(
        filters: dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
    ):
        """构建日志查询"""
        from app.models.log import Log
        from app.models.user import User

        # 使用join避免N+1查询
        query = db.session.query(Log).join(User, Log.user_id == User.id, isouter=True)

        if filters:
            if "level" in filters:
                query = query.filter(Log.level == filters["level"])
            if "user_id" in filters:
                query = query.filter(Log.user_id == filters["user_id"])
            if "date_from" in filters:
                query = query.filter(Log.created_at >= filters["date_from"])
            if "date_to" in filters:
                query = query.filter(Log.created_at <= filters["date_to"])
            if "search" in filters and filters["search"]:
                search_term = f"%{filters['search']}%"
                query = query.filter(Log.message.like(search_term))

        if order_by:
            if order_by == "created_at":
                query = query.order_by(Log.created_at.desc())
            elif order_by == "level":
                query = query.order_by(Log.level)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query


# 批量操作优化
class BatchOperations:
    """批量操作优化"""

    @staticmethod
    def bulk_insert(model_class, data_list: list[dict[str, Any]], batch_size: int = 1000):
        """批量插入数据"""
        try:
            total_inserted = 0
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i : i + batch_size]
                db.session.bulk_insert_mappings(model_class, batch)
                total_inserted += len(batch)

            db.session.commit()
            logger.info(f"批量插入完成: {total_inserted} 条记录")
            return total_inserted

        except Exception as e:
            db.session.rollback()
            logger.error(f"批量插入失败: {e}")
            raise

    @staticmethod
    def bulk_update(
        model_class,
        data_list: list[dict[str, Any]],
        update_fields: list[str],
        batch_size: int = 1000,
    ):
        """批量更新数据"""
        try:
            total_updated = 0
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i : i + batch_size]
                db.session.bulk_update_mappings(model_class, batch)
                total_updated += len(batch)

            db.session.commit()
            logger.info(f"批量更新完成: {total_updated} 条记录")
            return total_updated

        except Exception as e:
            db.session.rollback()
            logger.error(f"批量更新失败: {e}")
            raise

    @staticmethod
    def bulk_delete(model_class, ids: list[int], batch_size: int = 1000):
        """批量删除数据"""
        try:
            total_deleted = 0
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i : i + batch_size]
                model_class.query.filter(model_class.id.in_(batch_ids)).delete(synchronize_session=False)
                total_deleted += len(batch_ids)

            db.session.commit()
            logger.info(f"批量删除完成: {total_deleted} 条记录")
            return total_deleted

        except Exception as e:
            db.session.rollback()
            logger.error(f"批量删除失败: {e}")
            raise


# 查询缓存
class QueryCache:
    """查询缓存"""

    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.default_ttl:
                return data
            del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        ttl = ttl or self.default_ttl
        self.cache[key] = (value, time.time() + ttl)

    def clear(self, pattern: str = None):
        """清理缓存"""
        if pattern:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {"cache_size": len(self.cache), "keys": list(self.cache.keys())}


# 全局查询缓存
query_cache = QueryCache()


def cached_query(ttl: int = 300):
    """查询缓存装饰器"""

    def query_decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 尝试从缓存获取
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"查询缓存命中: {func.__name__}")
                return cached_result

            # 执行查询
            result = func(*args, **kwargs)

            # 缓存结果
            query_cache.set(cache_key, result, ttl)
            logger.debug(f"查询结果已缓存: {func.__name__}")

            return result

        return wrapper

    return query_decorator


# 数据库连接池监控
class ConnectionPoolMonitor:
    """连接池监控"""

    @staticmethod
    def get_pool_status():
        """获取连接池状态"""
        try:
            # 获取SQLAlchemy引擎信息
            engine = db.engine
            pool = engine.pool

            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "status": "healthy" if pool.checkedout() < pool.size() else "busy",
            }
        except Exception as e:
            logger.error(f"获取连接池状态失败: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def optimize_pool_settings():
        """优化连接池设置"""
        try:
            engine = db.engine
            pool = engine.pool

            # 根据当前使用情况调整池大小
            current_usage = pool.checkedout() / pool.size()

            if current_usage > 0.8:
                # 使用率过高，建议增加池大小
                recommended_size = int(pool.size() * 1.5)
                logger.info(f"连接池使用率过高 ({current_usage:.1%})，建议增加池大小到 {recommended_size}")
            elif current_usage < 0.3:
                # 使用率过低，建议减少池大小
                recommended_size = int(pool.size() * 0.7)
                logger.info(f"连接池使用率过低 ({current_usage:.1%})，建议减少池大小到 {recommended_size}")
            else:
                logger.info(f"连接池使用率正常 ({current_usage:.1%})")

            return {
                "current_usage": current_usage,
                "recommended_size": (recommended_size if "recommended_size" in locals() else pool.size()),
            }

        except Exception as e:
            logger.error(f"优化连接池设置失败: {e}")
            return {"error": str(e)}
