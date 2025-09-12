"""
泰摸鱼吧 - 装饰器工具
"""

from functools import wraps
from flask import abort, current_app
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
            return abort(401)
        if not current_user.is_admin():
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    """
    登录权限装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(401)
        return f(*args, **kwargs)
    return decorated_function
