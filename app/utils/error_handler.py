"""
泰摸鱼吧 - 错误处理工具
"""

import logging
from flask import current_app, request, jsonify, render_template
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import traceback

def register_error_handlers(app):
    """
    注册全局错误处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """400错误处理"""
        return _handle_error(error, 400, "请求参数错误")
    
    @app.errorhandler(401)
    def unauthorized(error):
        """401错误处理"""
        return _handle_error(error, 401, "未授权访问")
    
    @app.errorhandler(403)
    def forbidden(error):
        """403错误处理"""
        return _handle_error(error, 403, "禁止访问")
    
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return _handle_error(error, 404, "页面不存在")
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """429错误处理"""
        return _handle_error(error, 429, "请求过于频繁")
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """500错误处理"""
        return _handle_error(error, 500, "服务器内部错误")
    
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """SQLAlchemy错误处理"""
        logging.error(f"数据库错误: {error}")
        return _handle_error(error, 500, "数据库操作失败")
    
    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """通用错误处理"""
        logging.error(f"未处理的错误: {error}")
        logging.error(f"错误堆栈: {traceback.format_exc()}")
        return _handle_error(error, 500, "系统错误")

def _handle_error(error, status_code, message):
    """
    统一错误处理
    
    Args:
        error: 错误对象
        status_code: HTTP状态码
        message: 错误消息
        
    Returns:
        Response: 错误响应
    """
    # 记录错误日志
    _log_error(error, status_code)
    
    # 根据请求类型返回不同格式
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'error': message,
            'status_code': status_code,
            'timestamp': _get_timestamp()
        }), status_code
    else:
        return render_template('errors/error.html', 
                             error_code=status_code,
                             error_message=message), status_code

def _log_error(error, status_code):
    """
    记录错误日志
    
    Args:
        error: 错误对象
        status_code: HTTP状态码
    """
    try:
        # 获取错误详情
        error_details = {
            'status_code': status_code,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'request_url': request.url,
            'request_method': request.method,
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr
        }
        
        # 记录到日志
        if status_code >= 500:
            logging.error(f"服务器错误: {error_details}")
        else:
            logging.warning(f"客户端错误: {error_details}")
            
    except Exception as e:
        logging.error(f"记录错误日志失败: {e}")

def _get_timestamp():
    """
    获取当前时间戳
    
    Returns:
        str: ISO格式时间戳
    """
    from datetime import datetime
    return datetime.utcnow().isoformat()

def safe_error_message(error):
    """
    获取安全的错误消息
    
    Args:
        error: 错误对象
        
    Returns:
        str: 安全的错误消息
    """
    # 生产环境只返回通用错误消息
    if not current_app.debug:
        return "操作失败，请稍后重试"
    
    # 开发环境返回详细错误信息
    return str(error)

def validate_error_response(response_data):
    """
    验证错误响应数据
    
    Args:
        response_data: 响应数据
        
    Returns:
        bool: 是否有效
    """
    required_fields = ['error', 'status_code', 'timestamp']
    return all(field in response_data for field in required_fields)

class SecurityError(Exception):
    """安全相关错误"""
    pass

class ValidationError(Exception):
    """验证错误"""
    pass

class BusinessLogicError(Exception):
    """业务逻辑错误"""
    pass

def handle_security_error(error):
    """
    处理安全错误
    
    Args:
        error: 安全错误对象
        
    Returns:
        Response: 错误响应
    """
    logging.warning(f"安全错误: {error}")
    return _handle_error(error, 403, "安全验证失败")

def handle_validation_error(error):
    """
    处理验证错误
    
    Args:
        error: 验证错误对象
        
    Returns:
        Response: 错误响应
    """
    logging.info(f"验证错误: {error}")
    return _handle_error(error, 400, str(error))

def handle_business_logic_error(error):
    """
    处理业务逻辑错误
    
    Args:
        error: 业务逻辑错误对象
        
    Returns:
        Response: 错误响应
    """
    logging.info(f"业务逻辑错误: {error}")
    return _handle_error(error, 422, str(error))
