"""
泰摸鱼吧 - 缓存管理工具
"""

import time
import json
import hashlib
from functools import wraps
from typing import Any, Optional, Callable
from flask import current_app, request
from flask_caching import Cache

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache: Cache):
        """
        初始化缓存管理器
        
        Args:
            cache: Flask-Caching实例
        """
        self.cache = cache
        self.default_timeout = 300  # 5分钟默认超时
    
    def get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            str: 缓存键
        """
        # 创建键的字符串表示
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        # 生成哈希值
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值
        """
        try:
            return self.cache.get(key)
        except Exception as e:
            current_app.logger.error(f"获取缓存失败: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            if timeout is None:
                timeout = self.default_timeout
            
            self.cache.set(key, value, timeout=timeout)
            return True
        except Exception as e:
            current_app.logger.error(f"设置缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功
        """
        try:
            self.cache.delete(key)
            return True
        except Exception as e:
            current_app.logger.error(f"删除缓存失败: {e}")
            return False
    
    def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            bool: 是否成功
        """
        try:
            self.cache.clear()
            return True
        except Exception as e:
            current_app.logger.error(f"清空缓存失败: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> bool:
        """
        删除匹配模式的缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            bool: 是否成功
        """
        try:
            # 注意：这个功能需要Redis支持
            if hasattr(self.cache, 'cache') and hasattr(self.cache.cache, 'delete_pattern'):
                self.cache.cache.delete_pattern(pattern)
                return True
            else:
                current_app.logger.warning("当前缓存后端不支持模式删除")
                return False
        except Exception as e:
            current_app.logger.error(f"删除模式缓存失败: {e}")
            return False
    
    def get_or_set(self, key: str, func: Callable, timeout: Optional[int] = None) -> Any:
        """
        获取缓存值，如果不存在则设置
        
        Args:
            key: 缓存键
            func: 生成值的函数
            timeout: 超时时间
            
        Returns:
            Any: 缓存值
        """
        value = self.get(key)
        if value is None:
            value = func()
            self.set(key, value, timeout)
        return value

# 全局缓存管理器实例
cache_manager = None

def init_cache_manager(cache: Cache):
    """
    初始化全局缓存管理器
    
    Args:
        cache: Flask-Caching实例
    """
    global cache_manager
    cache_manager = CacheManager(cache)

def cached(timeout: int = 300, key_prefix: str = 'default'):
    """
    缓存装饰器
    
    Args:
        timeout: 超时时间（秒）
        key_prefix: 键前缀
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_manager:
                return func(*args, **kwargs)
            
            # 生成缓存键
            cache_key = cache_manager.get_cache_key(
                key_prefix, 
                func.__name__, 
                *args, 
                **kwargs
            )
            
            # 尝试获取缓存
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """
    使缓存失效
    
    Args:
        pattern: 匹配模式
    """
    if cache_manager:
        cache_manager.delete_pattern(pattern)

def cache_user_data(user_id: int, data: Any, timeout: int = 1800):
    """
    缓存用户数据
    
    Args:
        user_id: 用户ID
        data: 数据
        timeout: 超时时间（秒）
    """
    if cache_manager:
        key = f"user:{user_id}:data"
        cache_manager.set(key, data, timeout)

def get_cached_user_data(user_id: int) -> Optional[Any]:
    """
    获取缓存的用户数据
    
    Args:
        user_id: 用户ID
        
    Returns:
        Any: 缓存的数据
    """
    if cache_manager:
        key = f"user:{user_id}:data"
        return cache_manager.get(key)
    return None

def invalidate_user_cache(user_id: int):
    """
    使用户缓存失效
    
    Args:
        user_id: 用户ID
    """
    if cache_manager:
        pattern = f"user:{user_id}:*"
        cache_manager.delete_pattern(pattern)

def cache_instance_data(instance_id: int, data: Any, timeout: int = 3600):
    """
    缓存实例数据
    
    Args:
        instance_id: 实例ID
        data: 数据
        timeout: 超时时间（秒）
    """
    if cache_manager:
        key = f"instance:{instance_id}:data"
        cache_manager.set(key, data, timeout)

def get_cached_instance_data(instance_id: int) -> Optional[Any]:
    """
    获取缓存的实例数据
    
    Args:
        instance_id: 实例ID
        
    Returns:
        Any: 缓存的数据
    """
    if cache_manager:
        key = f"instance:{instance_id}:data"
        return cache_manager.get(key)
    return None

def invalidate_instance_cache(instance_id: int):
    """
    使实例缓存失效
    
    Args:
        instance_id: 实例ID
    """
    if cache_manager:
        pattern = f"instance:{instance_id}:*"
        cache_manager.delete_pattern(pattern)

def cache_dashboard_data(data: Any, timeout: int = 300):
    """
    缓存仪表盘数据
    
    Args:
        data: 数据
        timeout: 超时时间（秒）
    """
    if cache_manager:
        key = "dashboard:overview"
        cache_manager.set(key, data, timeout)

def get_cached_dashboard_data() -> Optional[Any]:
    """
    获取缓存的仪表盘数据
    
    Returns:
        Any: 缓存的数据
    """
    if cache_manager:
        key = "dashboard:overview"
        return cache_manager.get(key)
    return None

def invalidate_dashboard_cache():
    """
    使仪表盘缓存失效
    """
    if cache_manager:
        pattern = "dashboard:*"
        cache_manager.delete_pattern(pattern)

# 缓存统计
class CacheStats:
    """缓存统计"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
    
    def hit(self):
        """缓存命中"""
        self.hits += 1
    
    def miss(self):
        """缓存未命中"""
        self.misses += 1
    
    def set(self):
        """缓存设置"""
        self.sets += 1
    
    def delete(self):
        """缓存删除"""
        self.deletes += 1
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'hit_rate': self.get_hit_rate()
        }

# 全局缓存统计
cache_stats = CacheStats()
