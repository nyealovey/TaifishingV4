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
    # TODO: 实现服务状态检查逻辑
    return jsonify({
        'status': 'running',
        'database': 'connected',
        'redis': 'connected',
        'celery': 'running'
    })
