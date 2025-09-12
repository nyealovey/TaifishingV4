"""
泰摸鱼吧 - 装饰器工具
"""

from functools import wraps
from flask import abort, current_app, request, jsonify
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
        
        if not current_user.is_admin():
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


def permission_required(permission):
    """
    权限验证装饰器
    
    Args:
        permission: 需要的权限 (view, create, update, delete)
        
    Returns:
        装饰器函数
    """
    def decorator(f):
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
            
            # 检查权限
            if not has_permission(current_user, permission):
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': f'需要{permission}权限',
                        'code': 'FORBIDDEN'
                    }), 403
                else:
                    from flask import redirect, url_for, flash
                    flash(f'需要{permission}权限', 'error')
                    return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def has_permission(user, permission):
    """
    检查用户是否有指定权限
    
    Args:
        user: 用户对象
        permission: 权限名称
        
    Returns:
        bool: 是否有权限
    """
    # 权限级别定义
    PERMISSIONS = {
        'view': 1,
        'create': 2,
        'update': 3,
        'delete': 4
    }
    
    # 角色权限映射
    ROLE_PERMISSIONS = {
        'admin': ['view', 'create', 'update', 'delete'],
        'user': ['view']  # 普通用户只能查看
    }
    
    if not user or not user.is_authenticated:
        return False
    
    # 管理员拥有所有权限
    if user.role == 'admin':
        return True
    
    # 检查用户角色是否有该权限
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def view_required(f):
    """查看权限装饰器"""
    return permission_required('view')(f)


def create_required(f):
    """创建权限装饰器"""
    return permission_required('create')(f)


def update_required(f):
    """更新权限装饰器"""
    return permission_required('update')(f)


def delete_required(f):
    """删除权限装饰器"""
    return permission_required('delete')(f)