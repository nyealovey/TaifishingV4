# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - API响应标准化工具
"""

import logging
from typing import Any, Dict, Optional, List
from flask import jsonify, request
from datetime import datetime
from app.utils.timezone import now
import traceback

logger = logging.getLogger(__name__)

class APIResponse:
    """API响应标准化类"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", 
                code: int = 200, meta: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            code: 状态码
            meta: 元数据
            
        Returns:
            dict: 标准化响应
        """
        response = {
            'success': True,
            'code': code,
            'message': message,
            'timestamp': now().isoformat(),
            'data': data
        }
        
        if meta:
            response['meta'] = meta
        
        return jsonify(response), code
    
    @staticmethod
    def error(message: str = "操作失败", code: int = 400, 
              error_code: str = None, details: Any = None) -> Dict[str, Any]:
        """
        错误响应
        
        Args:
            message: 错误消息
            code: 状态码
            error_code: 错误代码
            details: 错误详情
            
        Returns:
            dict: 标准化错误响应
        """
        response = {
            'success': False,
            'code': code,
            'message': message,
            'timestamp': now().isoformat()
        }
        
        if error_code:
            response['error_code'] = error_code
        
        if details:
            response['details'] = details
        
        return jsonify(response), code
    
    @staticmethod
    def paginated(data: List[Any], page: int, per_page: int, total: int, 
                  message: str = "获取数据成功") -> Dict[str, Any]:
        """
        分页响应
        
        Args:
            data: 数据列表
            page: 当前页码
            per_page: 每页数量
            total: 总数量
            message: 响应消息
            
        Returns:
            dict: 分页响应
        """
        total_pages = (total + per_page - 1) // per_page
        
        response = {
            'success': True,
            'code': 200,
            'message': message,
            'timestamp': now().isoformat(),
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
        
        return jsonify(response), 200
    
    @staticmethod
    def validation_error(errors: Dict[str, List[str]], 
                        message: str = "数据验证失败") -> Dict[str, Any]:
        """
        验证错误响应
        
        Args:
            errors: 验证错误详情
            message: 错误消息
            
        Returns:
            dict: 验证错误响应
        """
        return APIResponse.error(
            message=message,
            code=422,
            error_code='VALIDATION_ERROR',
            details={'validation_errors': errors}
        )
    
    @staticmethod
    def not_found(resource: str = "资源", 
                  message: str = None) -> Dict[str, Any]:
        """
        资源未找到响应
        
        Args:
            resource: 资源名称
            message: 错误消息
            
        Returns:
            dict: 404响应
        """
        if not message:
            message = f"{resource}不存在"
        
        return APIResponse.error(
            message=message,
            code=404,
            error_code='NOT_FOUND'
        )
    
    @staticmethod
    def unauthorized(message: str = "未授权访问") -> Dict[str, Any]:
        """
        未授权响应
        
        Args:
            message: 错误消息
            
        Returns:
            dict: 401响应
        """
        return APIResponse.error(
            message=message,
            code=401,
            error_code='UNAUTHORIZED'
        )
    
    @staticmethod
    def forbidden(message: str = "禁止访问") -> Dict[str, Any]:
        """
        禁止访问响应
        
        Args:
            message: 错误消息
            
        Returns:
            dict: 403响应
        """
        return APIResponse.error(
            message=message,
            code=403,
            error_code='FORBIDDEN'
        )
    
    @staticmethod
    def rate_limited(message: str = "请求过于频繁", 
                    retry_after: int = 60) -> Dict[str, Any]:
        """
        速率限制响应
        
        Args:
            message: 错误消息
            retry_after: 重试间隔（秒）
            
        Returns:
            dict: 429响应
        """
        response = {
            'success': False,
            'code': 429,
            'message': message,
            'timestamp': now().isoformat(),
            'error_code': 'RATE_LIMITED',
            'retry_after': retry_after
        }
        
        return jsonify(response), 429
    
    @staticmethod
    def server_error(message: str = "服务器内部错误", 
                    error_id: str = None) -> Dict[str, Any]:
        """
        服务器错误响应
        
        Args:
            message: 错误消息
            error_id: 错误ID
            
        Returns:
            dict: 500响应
        """
        response = {
            'success': False,
            'code': 500,
            'message': message,
            'timestamp': now().isoformat(),
            'error_code': 'INTERNAL_SERVER_ERROR'
        }
        
        if error_id:
            response['error_id'] = error_id
        
        return jsonify(response), 500

# 响应装饰器
def api_response(func):
    """API响应装饰器"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # 如果已经是标准响应格式，直接返回
            if isinstance(result, tuple) and len(result) == 2:
                response, status_code = result
                if isinstance(response, dict) and 'success' in response:
                    return response, status_code
            
            # 否则包装为标准响应
            return APIResponse.success(data=result)
            
        except ValueError as e:
            logger.warning(f"参数错误: {e}")
            return APIResponse.error(message=str(e), code=400)
            
        except PermissionError as e:
            logger.warning(f"权限错误: {e}")
            return APIResponse.forbidden(str(e))
            
        except FileNotFoundError as e:
            logger.warning(f"资源未找到: {e}")
            return APIResponse.not_found()
            
        except Exception as e:
            logger.error(f"未处理的错误: {e}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return APIResponse.server_error()
    
    return wrapper

# 分页装饰器
def paginated_response(page_param: str = 'page', 
                      per_page_param: str = 'per_page',
                      max_per_page: int = 100):
    """分页响应装饰器"""
    def api_decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # 获取分页参数
                page = int(request.args.get(page_param, 1))
                per_page = min(int(request.args.get(per_page_param, 10)), max_per_page)
                
                # 调用原函数
                result = func(*args, **kwargs)
                
                # 如果结果包含分页信息，直接返回
                if isinstance(result, dict) and 'pagination' in result:
                    return APIResponse.paginated(
                        data=result.get('data', []),
                        page=result['pagination']['page'],
                        per_page=result['pagination']['per_page'],
                        total=result['pagination']['total']
                    )
                
                # 否则假设result是数据列表，需要手动分页
                if isinstance(result, list):
                    total = len(result)
                    start = (page - 1) * per_page
                    end = start + per_page
                    paginated_data = result[start:end]
                    
                    return APIResponse.paginated(
                        data=paginated_data,
                        page=page,
                        per_page=per_page,
                        total=total
                    )
                
                return APIResponse.success(data=result)
                
            except ValueError as e:
                return APIResponse.error(message="分页参数无效", code=400)
            except Exception as e:
                logger.error(f"分页处理错误: {e}")
                return APIResponse.server_error()
        
        return wrapper
    return api_decorator

# 缓存响应装饰器
def cached_response(ttl: int = 300, key_func: callable = None):
    """缓存响应装饰器"""
    def api_decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 这里可以集成Redis缓存
            # cached_result = cache.get(cache_key)
            # if cached_result:
            #     return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            # cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return api_decorator

# 请求日志装饰器
def log_request(func):
    """请求日志装饰器"""
    def wrapper(*args, **kwargs):
        start_time = now()
        
        try:
            result = func(*args, **kwargs)
            
            # 记录成功请求
            duration = (now() - start_time).total_seconds()
            logger.info(f"API请求成功: {func.__name__}, 耗时: {duration:.3f}秒")
            
            return result
            
        except Exception as e:
            # 记录失败请求
            duration = (now() - start_time).total_seconds()
            logger.error(f"API请求失败: {func.__name__}, 耗时: {duration:.3f}秒, 错误: {e}")
            
            raise
    
    return wrapper

# 响应时间监控装饰器
def monitor_response_time(threshold: float = 1.0):
    """响应时间监控装饰器"""
    def api_decorator(func):
        def wrapper(*args, **kwargs):
            start_time = now()
            
            try:
                result = func(*args, **kwargs)
                
                duration = (now() - start_time).total_seconds()
                
                if duration > threshold:
                    logger.warning(f"慢API响应: {func.__name__}, 耗时: {duration:.3f}秒")
                else:
                    logger.debug(f"API响应: {func.__name__}, 耗时: {duration:.3f}秒")
                
                return result
                
            except Exception as e:
                duration = (now() - start_time).total_seconds()
                logger.error(f"API异常: {func.__name__}, 耗时: {duration:.3f}秒, 错误: {e}")
                raise
        
        return wrapper
    return api_decorator

# 错误处理装饰器
def handle_errors(func):
    """错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数执行错误: {func.__name__}, 错误: {e}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return APIResponse.server_error()
    
    return wrapper
