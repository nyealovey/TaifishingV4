"""
装饰器工具模块
"""
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user


def admin_required(f):
    """
    管理员权限装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '请先登录',
                    'code': 'UNAUTHORIZED'
                }), 401
            else:
                from flask import redirect, url_for, flash
                flash('请先登录', 'warning')
                return redirect(url_for('auth.login'))
        
        if current_user.role != 'admin':
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '需要管理员权限',
                    'code': 'FORBIDDEN'
                }), 403
            else:
                from flask import redirect, url_for, flash
                flash('需要管理员权限', 'error')
                return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def login_required_json(f):
    """
    JSON API登录装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '请先登录',
                'code': 'UNAUTHORIZED'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(requests_per_minute=60):
    """
    速率限制装饰器
    
    Args:
        requests_per_minute: 每分钟请求次数限制
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里可以集成速率限制逻辑
            # 目前只是简单实现
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_json(required_fields=None):
    """
    JSON数据验证装饰器
    
    Args:
        required_fields: 必需字段列表
        
    Returns:
        装饰器函数
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': '请求必须是JSON格式',
                    'code': 'INVALID_CONTENT_TYPE'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空',
                    'code': 'EMPTY_DATA'
                }), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'message': f'缺少必需字段: {", ".join(missing_fields)}',
                        'code': 'MISSING_FIELDS'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
