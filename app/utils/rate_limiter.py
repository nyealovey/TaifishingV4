"""
泰摸鱼吧 - 速率限制工具
"""

import time
import redis
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, Optional

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化速率限制器
        
        Args:
            redis_client: Redis客户端实例
        """
        self.redis_client = redis_client
        self.memory_store = {}  # 内存存储（备用）
    
    def _get_key(self, identifier: str, endpoint: str) -> str:
        """
        生成Redis键
        
        Args:
            identifier: 标识符（IP地址或用户ID）
            endpoint: 端点名称
            
        Returns:
            str: Redis键
        """
        return f"rate_limit:{endpoint}:{identifier}"
    
    def _get_current_window(self) -> int:
        """
        获取当前时间窗口
        
        Returns:
            int: 时间窗口（秒）
        """
        return int(time.time() // 60)  # 1分钟窗口
    
    def is_allowed(self, identifier: str, endpoint: str, limit: int, window: int = 60) -> bool:
        """
        检查是否允许请求
        
        Args:
            identifier: 标识符（IP地址或用户ID）
            endpoint: 端点名称
            limit: 限制次数
            window: 时间窗口（秒）
            
        Returns:
            bool: 是否允许
        """
        if self.redis_client:
            return self._check_redis_limit(identifier, endpoint, limit, window)
        else:
            return self._check_memory_limit(identifier, endpoint, limit, window)
    
    def _check_redis_limit(self, identifier: str, endpoint: str, limit: int, window: int) -> bool:
        """
        使用Redis检查限制
        
        Args:
            identifier: 标识符
            endpoint: 端点名称
            limit: 限制次数
            window: 时间窗口
            
        Returns:
            bool: 是否允许
        """
        try:
            key = self._get_key(identifier, endpoint)
            current_time = time.time()
            
            # 使用滑动窗口算法
            pipe = self.redis_client.pipeline()
            
            # 移除过期的记录
            pipe.zremrangebyscore(key, 0, current_time - window)
            
            # 获取当前窗口内的请求数
            pipe.zcard(key)
            
            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})
            
            # 设置过期时间
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[1]
            
            return current_count < limit
            
        except Exception as e:
            current_app.logger.error(f"Redis速率限制检查失败: {e}")
            return True  # 失败时允许请求
    
    def _check_memory_limit(self, identifier: str, endpoint: str, limit: int, window: int) -> bool:
        """
        使用内存检查限制
        
        Args:
            identifier: 标识符
            endpoint: 端点名称
            limit: 限制次数
            window: 时间窗口
            
        Returns:
            bool: 是否允许
        """
        key = f"{identifier}:{endpoint}"
        current_time = time.time()
        
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # 清理过期记录
        self.memory_store[key] = [
            timestamp for timestamp in self.memory_store[key]
            if current_time - timestamp < window
        ]
        
        # 检查是否超过限制
        if len(self.memory_store[key]) >= limit:
            return False
        
        # 添加当前请求
        self.memory_store[key].append(current_time)
        return True

# 全局速率限制器实例
rate_limiter = None

def init_rate_limiter(redis_client: Optional[redis.Redis] = None):
    """
    初始化全局速率限制器
    
    Args:
        redis_client: Redis客户端实例
    """
    global rate_limiter
    rate_limiter = RateLimiter(redis_client)

def rate_limit(endpoint: str, limit: int, window: int = 60, per: str = 'ip'):
    """
    速率限制装饰器
    
    Args:
        endpoint: 端点名称
        limit: 限制次数
        window: 时间窗口（秒）
        per: 限制类型（'ip' 或 'user'）
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not rate_limiter:
                return f(*args, **kwargs)
            
            # 获取标识符
            if per == 'ip':
                identifier = request.remote_addr
            elif per == 'user':
                from flask_login import current_user
                if current_user.is_authenticated:
                    identifier = str(current_user.id)
                else:
                    identifier = request.remote_addr
            else:
                identifier = request.remote_addr
            
            # 检查速率限制
            if not rate_limiter.is_allowed(identifier, endpoint, limit, window):
                if request.is_json:
                    return jsonify({
                        'error': '请求过于频繁，请稍后再试',
                        'retry_after': window
                    }), 429
                else:
                    from flask import flash, redirect, url_for
                    flash('请求过于频繁，请稍后再试', 'error')
                    return redirect(request.url)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# 预定义的速率限制
def login_rate_limit(f):
    """登录速率限制：5次/分钟"""
    return rate_limit('login', 5, 60, 'ip')(f)

def api_rate_limit(f):
    """API速率限制：100次/分钟"""
    return rate_limit('api', 100, 60, 'user')(f)

def password_reset_rate_limit(f):
    """密码重置速率限制：3次/小时"""
    return rate_limit('password_reset', 3, 3600, 'ip')(f)

def registration_rate_limit(f):
    """注册速率限制：3次/小时"""
    return rate_limit('registration', 3, 3600, 'ip')(f)
