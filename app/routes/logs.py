# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 操作日志管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.log import Log
from app.models.user import User
from app import db
import logging
from datetime import datetime, timedelta

# 创建蓝图
logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/')
@login_required
def index():
    """日志管理首页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    log_level = request.args.get('log_level', '', type=str)
    log_type = request.args.get('log_type', '', type=str)
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    search = request.args.get('search', '', type=str)
    
    # 构建查询
    query = Log.query
    
    if log_level:
        query = query.filter(Log.level == log_level)
    
    if log_type:
        query = query.filter(Log.log_type == log_type)
    
    if user_id:
        query = query.filter(Log.user_id == user_id)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Log.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Log.created_at < end_dt)
        except ValueError:
            pass
    
    if search:
        # 安全的搜索查询，防止SQL注入
        search_term = search.strip()
        if search_term:
            query = query.filter(
                db.or_(
                    Log.message.contains(search_term),
                    Log.details.contains(search_term),
                    Log.module.contains(search_term)
                )
            )
    
    # 分页查询 - 使用join避免N+1查询
    logs = query.options(
        db.joinedload(Log.user)
    ).order_by(Log.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取用户列表用于筛选 - 只获取必要字段
    users = User.query.with_entities(User.id, User.username).all()
    
    # 获取日志级别和类型
    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    log_types = db.session.query(Log.log_type).distinct().all()
    log_types = [lt[0] for lt in log_types if lt[0]]
    
    if request.is_json:
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'pagination': {
                'page': logs.page,
                'pages': logs.pages,
                'per_page': logs.per_page,
                'total': logs.total,
                'has_next': logs.has_next,
                'has_prev': logs.has_prev
            },
            'users': [user.to_dict() for user in users],
            'log_levels': log_levels,
            'log_types': log_types
        })
    
    return render_template('logs/index.html', 
                         logs=logs,
                         users=users,
                         log_levels=log_levels,
                         log_types=log_types,
                         log_level=log_level,
                         log_type=log_type,
                         user_id=user_id,
                         start_date=start_date,
                         end_date=end_date,
                         search=search)

@logs_bp.route('/<int:log_id>')
@login_required
def detail(log_id):
    """日志详情"""
    log = Log.query.get_or_404(log_id)
    
    if request.is_json:
        return jsonify(log.to_dict())
    
    return render_template('logs/detail.html', log=log)

@logs_bp.route('/export')
@login_required
def export():
    """导出日志"""
    format_type = request.args.get('format', 'json', type=str)
    log_level = request.args.get('log_level', '', type=str)
    log_type = request.args.get('log_type', '', type=str)
    start_date = request.args.get('start_date', '', type=str)
    end_date = request.args.get('end_date', '', type=str)
    
    # 构建查询
    query = Log.query
    
    if log_level:
        query = query.filter(Log.level == log_level)
    
    if log_type:
        query = query.filter(Log.log_type == log_type)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Log.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Log.created_at < end_dt)
        except ValueError:
            pass
    
    logs = query.order_by(Log.created_at.desc()).all()
    
    if format_type == 'csv':
        # 生成CSV格式
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['时间', '级别', '类型', '模块', '用户', '消息', '详情'])
        
        # 写入数据
        for log in logs:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
                log.level,
                log.log_type,
                log.module,
                log.user.username if log.user else '系统',
                log.message,
                log.details or ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=operation_logs.csv'}
        )
    
    else:
        # 默认JSON格式
        data = {
            'export_time': datetime.utcnow().isoformat(),
            'total_logs': len(logs),
            'filters': {
                'log_level': log_level,
                'log_type': log_type,
                'start_date': start_date,
                'end_date': end_date
            },
            'logs': [log.to_dict() for log in logs]
        }
        
        return jsonify(data)

@logs_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup():
    """清理旧日志"""
    days = request.args.get('days', 30, type=int)
    
    try:
        # 删除指定天数前的日志
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = Log.query.filter(Log.created_at < cutoff_date).delete()
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'message': f'已清理 {deleted_count} 条 {days} 天前的日志',
                'deleted_count': deleted_count
            })
        
        flash(f'已清理 {deleted_count} 条 {days} 天前的日志', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"清理日志失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '清理日志失败，请重试'}), 500
        
        flash('清理日志失败，请重试', 'error')
    
    return redirect(url_for('logs.index'))

@logs_bp.route('/statistics')
@login_required
def statistics():
    """日志统计"""
    # 获取统计信息
    stats = get_log_statistics()
    
    if request.is_json:
        return jsonify(stats)
    
    return render_template('logs/statistics.html', stats=stats)

def get_log_statistics():
    """获取日志统计信息"""
    try:
        # 总日志数
        total_logs = Log.query.count()
        
        # 各级别日志数量
        level_stats = db.session.query(
            Log.level,
            db.func.count(Log.id).label('count')
        ).group_by(Log.level).all()
        
        # 各类型日志数量
        type_stats = db.session.query(
            Log.log_type,
            db.func.count(Log.id).label('count')
        ).group_by(Log.log_type).all()
        
        # 今日日志数
        today = datetime.utcnow().date()
        today_logs = Log.query.filter(
            db.func.date(Log.created_at) == today
        ).count()
        
        # 最近7天日志趋势
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_logs = Log.query.filter(
            Log.created_at >= week_ago
        ).count()
        
        # 错误日志数
        error_logs = Log.query.filter(
            Log.level.in_(['ERROR', 'CRITICAL'])
        ).count()
        
        # 用户操作统计
        user_stats = db.session.query(
            User.username,
            db.func.count(Log.id).label('log_count')
        ).outerjoin(Log).group_by(User.id, User.username).all()
        
        return {
            'total_logs': total_logs,
            'today_logs': today_logs,
            'week_logs': week_logs,
            'error_logs': error_logs,
            'level_stats': [
                {'level': stat.level, 'count': stat.count}
                for stat in level_stats
            ],
            'type_stats': [
                {'type': stat.log_type, 'count': stat.count}
                for stat in type_stats
            ],
            'user_stats': [
                {'username': stat.username, 'count': stat.log_count or 0}
                for stat in user_stats
            ]
        }
    except Exception as e:
        logging.error(f"获取日志统计失败: {e}")
        return {
            'total_logs': 0,
            'today_logs': 0,
            'week_logs': 0,
            'error_logs': 0,
            'level_stats': [],
            'type_stats': [],
            'user_stats': []
        }

# API路由
@logs_bp.route('/api/logs')
@jwt_required()
def api_list():
    """获取日志列表API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    logs = Log.query.order_by(Log.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'pagination': {
            'page': logs.page,
            'pages': logs.pages,
            'per_page': logs.per_page,
            'total': logs.total,
            'has_next': logs.has_next,
            'has_prev': logs.has_prev
        }
    })

@logs_bp.route('/api/logs/<int:log_id>')
@jwt_required()
def api_detail(log_id):
    """获取日志详情API"""
    log = Log.query.get_or_404(log_id)
    return jsonify(log.to_dict())

@logs_bp.route('/api/logs/statistics')
@jwt_required()
def api_statistics():
    """获取日志统计API"""
    stats = get_log_statistics()
    return jsonify(stats)