# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 主要路由
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
import psutil
from app.utils.timezone import get_china_time, format_china_time

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页 - 重定向到登录页面"""
    return redirect(url_for('auth.login'))

@main_bp.route('/api-status')
@login_required
def api_status_page():
    """API状态页面"""
    return render_template('api_status.html')

@main_bp.route('/admin')
@login_required
def admin():
    """系统管理页面"""
    return render_template('admin/index.html')

@main_bp.route('/api/status')
def api_status():
    """API状态检查"""
    return jsonify({
        'status': 'success',
        'message': '泰摸鱼吧API运行正常',
        'version': '1.0.0',
        'user': current_user.username if current_user.is_authenticated else None
    })

@main_bp.route('/api/health')
def api_health():
    """健康检查"""
    from datetime import datetime
    from app import db
    
    # 检查数据库状态
    db_status = 'connected'
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
    except Exception:
        db_status = 'error'
    
    # 检查Redis状态
    redis_status = 'connected'
    try:
        from flask import current_app
        redis_client = getattr(current_app, 'redis_client', None)
        if redis_client:
            redis_client.ping()
        else:
            redis_status = 'error'
    except Exception:
        redis_status = 'error'
    
    # 整体状态
    overall_status = 'healthy' if db_status == 'connected' and redis_status == 'connected' else 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'database': db_status,
        'redis': redis_status,
        'timestamp': get_china_time().isoformat(),
        'uptime': get_system_uptime()
    })

def get_system_uptime():
    """获取系统运行时间"""
    try:
        from datetime import datetime
        uptime_seconds = psutil.boot_time()
        uptime = get_china_time() - datetime.fromtimestamp(uptime_seconds)
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        return f"{days}天 {hours}小时 {minutes}分钟"
    except Exception:
        return "未知"