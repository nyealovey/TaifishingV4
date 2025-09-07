"""
泰摸鱼吧 - 日志系统工具
"""

import os
import logging
import logging.handlers
from datetime import datetime
from flask import current_app
from functools import wraps

def setup_logger(name, log_file, level=logging.INFO):
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志目录
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_app_logger():
    """
    获取应用日志记录器
    
    Returns:
        logging.Logger: 应用日志记录器
    """
    if current_app:
        return current_app.logger
    else:
        return setup_logger('taifish', 'userdata/logs/app.log')

def log_operation(operation_type, user_id=None, details=None):
    """
    记录操作日志
    
    Args:
        operation_type: 操作类型
        user_id: 用户ID
        details: 操作详情
    """
    logger = get_app_logger()
    
    log_data = {
        'operation_type': operation_type,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat(),
        'details': details or {}
    }
    
    logger.info(f"操作日志: {log_data}")

def log_error(error, user_id=None, context=None):
    """
    记录错误日志
    
    Args:
        error: 错误对象或错误信息
        user_id: 用户ID
        context: 错误上下文
    """
    logger = get_app_logger()
    
    error_data = {
        'error_type': type(error).__name__ if hasattr(error, '__class__') else 'Unknown',
        'error_message': str(error),
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat(),
        'context': context or {}
    }
    
    logger.error(f"错误日志: {error_data}")

def log_performance(operation, duration, user_id=None):
    """
    记录性能日志
    
    Args:
        operation: 操作名称
        duration: 执行时间（秒）
        user_id: 用户ID
    """
    logger = get_app_logger()
    
    perf_data = {
        'operation': operation,
        'duration': duration,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"性能日志: {perf_data}")

def log_database_operation(operation, table, record_id=None, user_id=None):
    """
    记录数据库操作日志
    
    Args:
        operation: 操作类型（CREATE, READ, UPDATE, DELETE）
        table: 表名
        record_id: 记录ID
        user_id: 用户ID
    """
    logger = get_app_logger()
    
    db_data = {
        'operation': operation,
        'table': table,
        'record_id': record_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"数据库操作: {db_data}")

def log_cache_operation(operation, key, hit=None, user_id=None):
    """
    记录缓存操作日志
    
    Args:
        operation: 操作类型（GET, SET, DELETE）
        key: 缓存键
        hit: 是否命中
        user_id: 用户ID
    """
    logger = get_app_logger()
    
    cache_data = {
        'operation': operation,
        'key': key,
        'hit': hit,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"缓存操作: {cache_data}")

def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """
    记录安全事件日志
    
    Args:
        event_type: 事件类型
        user_id: 用户ID
        ip_address: IP地址
        details: 事件详情
    """
    logger = get_app_logger()
    
    security_data = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.warning(f"安全事件: {security_data}")

def log_sync_operation(instance_id, sync_type, status, records_count=None, error=None):
    """
    记录同步操作日志
    
    Args:
        instance_id: 实例ID
        sync_type: 同步类型
        status: 同步状态
        records_count: 同步记录数
        error: 错误信息
    """
    logger = get_app_logger()
    
    sync_data = {
        'instance_id': instance_id,
        'sync_type': sync_type,
        'status': status,
        'records_count': records_count,
        'error': str(error) if error else None,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"同步操作: {sync_data}")

def log_api_request(method, endpoint, status_code, duration, user_id=None, ip_address=None):
    """
    记录API请求日志
    
    Args:
        method: HTTP方法
        endpoint: API端点
        status_code: 状态码
        duration: 请求处理时间
        user_id: 用户ID
        ip_address: IP地址
    """
    logger = get_app_logger()
    
    api_data = {
        'method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'duration': duration,
        'user_id': user_id,
        'ip_address': ip_address,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"API请求: {api_data}")

def log_decorator(operation_type):
    """
    日志装饰器
    
    Args:
        operation_type: 操作类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_app_logger()
            start_time = datetime.utcnow()
            
            try:
                logger.info(f"开始执行: {operation_type}")
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"完成执行: {operation_type}, 耗时: {duration:.2f}秒")
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(f"执行失败: {operation_type}, 耗时: {duration:.2f}秒, 错误: {str(e)}")
                raise
        return wrapper
    return decorator

# 创建各种专用日志记录器
app_logger = setup_logger('taifish.app', 'userdata/logs/app.log')
auth_logger = setup_logger('taifish.auth', 'userdata/logs/auth.log')
db_logger = setup_logger('taifish.database', 'userdata/logs/database.log')
cache_logger = setup_logger('taifish.cache', 'userdata/logs/cache.log')
sync_logger = setup_logger('taifish.sync', 'userdata/logs/sync.log')
security_logger = setup_logger('taifish.security', 'userdata/logs/security.log')
api_logger = setup_logger('taifish.api', 'userdata/logs/api.log')
