# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 重试管理工具
"""

import time
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"           # 固定间隔
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"         # 线性增长

class RetryManager:
    """重试管理器"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.strategy = strategy
    
    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        if self.strategy == RetryStrategy.FIXED:
            return self.base_delay
        elif self.strategy == RetryStrategy.LINEAR:
            return min(self.base_delay * attempt, self.max_delay)
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
            return min(delay, self.max_delay)
        else:
            return self.base_delay
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行带重试的函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.debug(f"执行函数 {func.__name__}, 尝试 {attempt}/{self.max_attempts}")
                result = func(*args, **kwargs)
                logger.debug(f"函数 {func.__name__} 执行成功")
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"函数 {func.__name__} 执行失败 (尝试 {attempt}/{self.max_attempts}): {e}")
                
                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.debug(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    logger.error(f"函数 {func.__name__} 重试次数已达上限")
        
        # 所有重试都失败了
        raise last_exception

def retry(max_attempts: int = 3, base_delay: float = 1.0, 
          max_delay: float = 60.0, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
          exceptions: tuple = (Exception,)):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        strategy: 重试策略
        exceptions: 需要重试的异常类型
    """
    def retry_decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = RetryManager(max_attempts, base_delay, max_delay, strategy)
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"执行函数 {func.__name__}, 尝试 {attempt}/{max_attempts}")
                    result = func(*args, **kwargs)
                    logger.debug(f"函数 {func.__name__} 执行成功")
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"函数 {func.__name__} 执行失败 (尝试 {attempt}/{max_attempts}): {e}")
                    
                    if attempt < max_attempts:
                        delay = retry_manager.calculate_delay(attempt)
                        logger.debug(f"等待 {delay} 秒后重试...")
                        time.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 重试次数已达上限")
                
                except Exception as e:
                    # 不在重试范围内的异常，直接抛出
                    logger.error(f"函数 {func.__name__} 发生不可重试的异常: {e}")
                    raise
            
            # 所有重试都失败了
            raise last_exception
        
        return wrapper
    return retry_decorator

# 预定义的重试配置
class RetryConfigs:
    """重试配置预设"""
    
    # 数据库操作重试
    DATABASE = RetryManager(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
    
    # 网络请求重试
    NETWORK = RetryManager(
        max_attempts=5,
        base_delay=2.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
    
    # 文件操作重试
    FILE = RetryManager(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5.0,
        strategy=RetryStrategy.LINEAR
    )
    
    # 任务执行重试
    TASK = RetryManager(
        max_attempts=2,
        base_delay=5.0,
        max_delay=30.0,
        strategy=RetryStrategy.FIXED
    )

# 便捷装饰器
def retry_database(max_attempts: int = 3):
    """数据库操作重试装饰器"""
    return retry(
        max_attempts=max_attempts,
        base_delay=1.0,
        max_delay=10.0,
        strategy=RetryStrategy.EXPONENTIAL,
        exceptions=(Exception,)
    )

def retry_network(max_attempts: int = 5):
    """网络请求重试装饰器"""
    return retry(
        max_attempts=max_attempts,
        base_delay=2.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL,
        exceptions=(ConnectionError, TimeoutError, OSError)
    )

def retry_file(max_attempts: int = 3):
    """文件操作重试装饰器"""
    return retry(
        max_attempts=max_attempts,
        base_delay=0.5,
        max_delay=5.0,
        strategy=RetryStrategy.LINEAR,
        exceptions=(OSError, IOError)
    )

def retry_task(max_attempts: int = 2):
    """任务执行重试装饰器"""
    return retry(
        max_attempts=max_attempts,
        base_delay=5.0,
        max_delay=30.0,
        strategy=RetryStrategy.FIXED,
        exceptions=(Exception,)
    )

# 智能重试：根据异常类型选择重试策略
def smart_retry(max_attempts: int = 3):
    """智能重试装饰器"""
    def retry_decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except (ConnectionError, TimeoutError) as e:
                    # 网络相关异常，使用网络重试策略
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(2.0 * (2 ** (attempt - 1)), 30.0)
                        time.sleep(delay)
                    
                except (OSError, IOError) as e:
                    # 文件相关异常，使用文件重试策略
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(0.5 * attempt, 5.0)
                        time.sleep(delay)
                    
                except Exception as e:
                    # 其他异常，使用固定重试策略
                    last_exception = e
                    if attempt < max_attempts:
                        delay = 1.0
                        time.sleep(delay)
                    else:
                        raise
            
            raise last_exception
        
        return wrapper
    return retry_decorator

# 重试统计
class RetryStats:
    """重试统计"""
    
    def __init__(self):
        self.stats = {}
    
    def record_retry(self, func_name: str, attempt: int, success: bool, error: str = None):
        """记录重试统计"""
        if func_name not in self.stats:
            self.stats[func_name] = {
                'total_attempts': 0,
                'successful_attempts': 0,
                'failed_attempts': 0,
                'retry_count': 0,
                'errors': []
            }
        
        stats = self.stats[func_name]
        stats['total_attempts'] += 1
        
        if success:
            stats['successful_attempts'] += 1
        else:
            stats['failed_attempts'] += 1
            if attempt > 1:
                stats['retry_count'] += 1
            if error:
                stats['errors'].append(error)
    
    def get_stats(self, func_name: str = None) -> Dict[str, Any]:
        """获取重试统计"""
        if func_name:
            return self.stats.get(func_name, {})
        return self.stats
    
    def get_success_rate(self, func_name: str) -> float:
        """获取成功率"""
        stats = self.stats.get(func_name, {})
        total = stats.get('total_attempts', 0)
        if total == 0:
            return 0.0
        return stats.get('successful_attempts', 0) / total

# 全局重试统计
retry_stats = RetryStats()
