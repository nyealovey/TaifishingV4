"""
泰摸鱼吧 - API路由
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'message': '泰摸鱼吧服务正常运行',
        'version': '1.0.0'
    })

@api_bp.route('/status')
@jwt_required()
def status():
    """服务状态"""
    from app import db, cache
    from app.models.user import User
    from app.models.instance import Instance
    from app.models.task import Task
    import redis
    import psutil
    from datetime import datetime
    
    status_info = {
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime': 'unknown'
    }
    
    # 检查数据库连接
    try:
        db.session.execute('SELECT 1')
        status_info['database'] = 'connected'
    except Exception as e:
        status_info['database'] = f'error: {str(e)}'
    
    # 检查Redis连接
    try:
        cache.cache._write_client.ping()
        status_info['redis'] = 'connected'
    except Exception as e:
        status_info['redis'] = f'error: {str(e)}'
    
    # 检查Celery状态
    try:
        from app import celery
        inspect = celery.control.inspect()
        stats = inspect.stats()
        if stats:
            status_info['celery'] = 'running'
        else:
            status_info['celery'] = 'no workers'
    except Exception as e:
        status_info['celery'] = f'error: {str(e)}'
    
    # 系统资源状态
    try:
        status_info['system'] = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    except Exception as e:
        status_info['system'] = f'error: {str(e)}'
    
    # 数据库统计
    try:
        status_info['stats'] = {
            'users': User.query.count(),
            'instances': Instance.query.count(),
            'tasks': Task.query.count(),
            'active_tasks': Task.query.filter_by(is_active=True).count()
        }
    except Exception as e:
        status_info['stats'] = f'error: {str(e)}'
    
    return jsonify(status_info)
