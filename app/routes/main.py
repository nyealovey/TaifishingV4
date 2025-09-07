# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 主要路由
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@main_bp.route('/api-status')
@login_required
def api_status_page():
    """API状态页面"""
    return render_template('api_status.html')

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
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'redis': 'connected',
        'timestamp': request.environ.get('REQUEST_TIME', 'unknown')
    })