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
from app.utils.api_response import APIResponse
import logging
from datetime import datetime, timedelta
from app.utils.timezone import now
import pytz

# 创建蓝图
logs_bp = Blueprint("logs", __name__)


def get_merged_request_logs(query, page=1, per_page=20):
    """
    获取日志列表（区分HTTP请求和其他日志）
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码
        per_page: 每页数量
        
    Returns:
        Pagination: 分页对象
    """
    try:
        # 直接查询所有日志，按ID排序
        logs = query.order_by(Log.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 为每个日志添加类型标识
        for log in logs.items:
            # 判断是否为HTTP请求日志
            if (log.log_type == 'request' and 
                '请求:' in log.message and 
                log.module == 'request_handler'):
                log.is_merged = True  # HTTP请求日志（已合并）
                log.log_category = 'http_request'
            else:
                log.is_merged = False  # 其他类型日志
                log.log_category = 'other'
        
        return logs
    except Exception as e:
        logging.error(f"获取日志列表失败: {e}")
        return None


@logs_bp.route("/")
@login_required
def index():
    """日志管理首页"""
    try:
        # 获取查询参数
        level = request.args.get('level', '')
        module = request.args.get('module', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        
        # 构建查询
        query = Log.query
        
        # 按级别过滤
        if level:
            query = query.filter(Log.level == level)
        
        # 按模块过滤
        if module:
            query = query.filter(Log.module == module)
        
        # 按时间范围过滤
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Log.created_at >= start_datetime)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Log.created_at < end_datetime)
            except ValueError:
                pass
        
        # 按消息内容搜索
        if search:
            query = query.filter(Log.message.like(f'%{search}%'))
        
        # 获取合并后的日志
        merged_logs = get_merged_request_logs(query, page, 20)
        
        if not merged_logs:
            flash("获取日志列表失败", "error")
            return render_template("logs/system_logs.html", 
                                 merged_logs=None, 
                                 level=level, 
                                 module=module, 
                                 start_date=start_date, 
                                 end_date=end_date, 
                                 search=search)
        
        # 获取统计信息
        total_logs = Log.query.count()
        error_logs = Log.query.filter(Log.level == 'ERROR').count()
        warning_logs = Log.query.filter(Log.level == 'WARNING').count()
        info_logs = Log.query.filter(Log.level == 'INFO').count()
        
        return render_template("logs/system_logs.html", 
                             merged_logs=merged_logs, 
                             level=level, 
                             module=module, 
                             start_date=start_date, 
                             end_date=end_date, 
                             search=search,
                             total_logs=total_logs,
                             error_logs=error_logs,
                             warning_logs=warning_logs,
                             info_logs=info_logs)
    except Exception as e:
        logging.error(f"日志管理首页加载失败: {e}")
        flash("页面加载失败", "error")
        return render_template("logs/system_logs.html", 
                             merged_logs=None, 
                             level='', 
                             module='', 
                             start_date='', 
                             end_date='', 
                             search='')


@logs_bp.route("/api/export")
@login_required
def export_logs():
    """导出日志为CSV"""
    try:
        import csv
        import io
        from flask import make_response
        
        # 获取查询参数
        level = request.args.get('level', '')
        module = request.args.get('module', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        search = request.args.get('search', '')
        
        # 构建查询
        query = Log.query
        
        # 按级别过滤
        if level:
            query = query.filter(Log.level == level)
        
        # 按模块过滤
        if module:
            query = query.filter(Log.module == module)
        
        # 按时间范围过滤
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Log.created_at >= start_datetime)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Log.created_at < end_datetime)
            except ValueError:
                pass
        
        # 按消息内容搜索
        if search:
            query = query.filter(Log.message.like(f'%{search}%'))
        
        # 获取所有日志
        logs = query.order_by(Log.id.desc()).all()
        
        # 创建CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['ID', '时间', '级别', '模块', '消息', '用户', 'IP地址'])
        
        # 写入数据行
        for log in logs:
            writer.writerow([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.level,
                log.module,
                log.message,
                log.user_id or '未知',
                log.ip_address or '未知'
            ])
        
        # 创建响应
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=logs.csv'
        
        return response
    except Exception as e:
        logging.error(f"导出日志失败: {e}")
        flash("导出失败", "error")
        return redirect(url_for('logs.index'))


@logs_bp.route("/api/log/<int:log_id>")
@login_required
def get_log_detail(log_id):
    """获取日志详情"""
    try:
        log = Log.query.get_or_404(log_id)
        
        return jsonify({
            'success': True,
            'log': {
                'id': log.id,
                'level': log.level,
                'log_type': log.log_type,
                'module': log.module,
                'message': log.message,
                'details': log.details,
                'user_id': log.user_id,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'created_at': log.created_at.isoformat()
            }
        })
    except Exception as e:
        logging.error(f"获取日志详情失败: {e}")
        return jsonify({'success': False, 'message': '获取日志详情失败'})


@logs_bp.route("/api/merged-info/<int:log_id>")
@login_required
def get_merged_info(log_id):
    """获取合并日志的详细信息"""
    try:
        log = Log.query.get_or_404(log_id)
        
        # 解析日志详情
        merged_info = {
            'path': None,
            'status_code': None,
            'duration': None,
            'start_time': None,
            'end_time': None,
            'request_method': None,
            'user_info': None,
            'ip_info': None,
            'log_level': log.level,  # 使用合并后的日志级别
            'response_size': None,
            'response_headers': None,
            'response_body': None,
            'request_headers': None,
            'request_body': None
        }
        
        # 如果是请求日志，解析消息
        if log.log_type == 'request' and '请求:' in log.message:
            # 解析路径和状态码
            import re
            match = re.search(r'请求:\s+(\w+)\s+(.+?)\s+-\s+(\d+)\s+\((.+?)\)', log.message)
            if match:
                merged_info['request_method'] = match.group(1)
                merged_info['path'] = match.group(2)
                merged_info['status_code'] = int(match.group(3))
                merged_info['duration'] = float(match.group(4).replace('ms', ''))
        
        # 解析详情信息
        if log.details:
            import re
            import json
            from datetime import datetime
            
            # 解析时间信息
            start_match = re.search(r'开始时间:\s+([^,]+)', log.details)
            end_match = re.search(r'结束时间:\s+([^,]+)', log.details)
            duration_match = re.search(r'持续时间:\s+([^,]+)', log.details)
            
            if start_match:
                try:
                    # 解析开始时间
                    start_time_str = start_match.group(1).strip()
                    # 处理格式: 2025-09-11 06:32:19.401751
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S.%f')
                    merged_info['start_time'] = start_time.isoformat()
                except:
                    try:
                        # 尝试不带微秒的格式
                        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                        merged_info['start_time'] = start_time.isoformat()
                    except:
                        merged_info['start_time'] = start_time_str
                    
            if end_match:
                try:
                    # 解析结束时间
                    end_time_str = end_match.group(1).strip()
                    # 处理格式: 2025-09-11 06:32:20.413840
                    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S.%f')
                    merged_info['end_time'] = end_time.isoformat()
                except:
                    try:
                        # 尝试不带微秒的格式
                        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                        merged_info['end_time'] = end_time.isoformat()
                    except:
                        merged_info['end_time'] = end_time_str
                    
            if duration_match:
                merged_info['duration'] = float(duration_match.group(1).replace('ms', ''))
            
            # 解析响应信息
            response_size_match = re.search(r'响应大小:\s+([^,]+)', log.details)
            if response_size_match:
                try:
                    merged_info['response_size'] = int(response_size_match.group(1).strip())
                except:
                    merged_info['response_size'] = response_size_match.group(1).strip()
            
            # 解析请求头
            request_headers_match = re.search(r'请求头:\s+({[^}]+})', log.details)
            if request_headers_match:
                try:
                    headers_str = request_headers_match.group(1)
                    merged_info['request_headers'] = json.loads(headers_str)
                except:
                    merged_info['request_headers'] = request_headers_match.group(1)
            
            # 解析响应头
            response_headers_match = re.search(r'响应头:\s+({[^}]+})', log.details)
            if response_headers_match:
                try:
                    headers_str = response_headers_match.group(1)
                    merged_info['response_headers'] = json.loads(headers_str)
                except:
                    merged_info['response_headers'] = response_headers_match.group(1)
            
            # 解析响应内容
            response_body_match = re.search(r'响应内容:\s+(.+)', log.details)
            if response_body_match:
                merged_info['response_body'] = response_body_match.group(1).strip()
        
        # 用户信息
        if log.user_id:
            user = User.query.get(log.user_id)
            if user:
                merged_info['user_info'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': getattr(user, 'email', 'N/A')
                }
        
        # IP信息
        if log.ip_address:
            merged_info['ip_info'] = {
                'address': log.ip_address,
                'user_agent': log.user_agent
            }
        
        # 添加调试信息
        merged_info['debug'] = {
            'log_id': log.id,
            'log_type': log.log_type,
            'message': log.message,
            'details': log.details,
            'parsed_successfully': any([
                merged_info['path'],
                merged_info['status_code'],
                merged_info['duration']
            ])
        }
        
        return jsonify({'success': True, 'merged_info': merged_info})
    except Exception as e:
        logging.error(f"获取合并日志信息失败: {e}")
        return jsonify({
            'success': False, 
            'message': f'获取合并日志信息失败: {str(e)}',
            'debug': {
                'log_id': log_id,
                'error': str(e)
            }
        })


@logs_bp.route("/api/stats")
@login_required
def get_log_stats():
    """获取日志统计信息"""
    try:
        # 获取最近24小时的日志统计
        now_time = now()
        yesterday = now_time - timedelta(days=1)
        
        # 按级别统计
        level_stats = {}
        for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
            count = Log.query.filter(
                Log.level == level,
                Log.created_at >= yesterday
            ).count()
            level_stats[level] = count
        
        # 按模块统计
        module_stats = {}
        modules = db.session.query(Log.module).distinct().all()
        for module in modules:
            if module[0]:
                count = Log.query.filter(
                    Log.module == module[0],
                    Log.created_at >= yesterday
                ).count()
                module_stats[module[0]] = count
        
        return jsonify({
            'success': True,
            'stats': {
                'level_stats': level_stats,
                'module_stats': module_stats,
                'total_logs': Log.query.filter(Log.created_at >= yesterday).count()
            }
        })
    except Exception as e:
        logging.error(f"获取日志统计失败: {e}")
        return jsonify({'success': False, 'message': '获取日志统计失败'})


@logs_bp.route("/api/clear")
@login_required
def clear_logs():
    """清空日志"""
    try:
        # 只允许管理员清空日志
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': '权限不足'})
        
        # 清空所有日志
        Log.query.delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': '日志已清空'})
    except Exception as e:
        logging.error(f"清空日志失败: {e}")
        return jsonify({'success': False, 'message': '清空日志失败'})


@logs_bp.route("/api/delete/<int:log_id>")
@login_required
def delete_log(log_id):
    """删除单个日志"""
    try:
        # 只允许管理员删除日志
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': '权限不足'})
        
        log = Log.query.get_or_404(log_id)
        db.session.delete(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '日志已删除'})
    except Exception as e:
        logging.error(f"删除日志失败: {e}")
        return jsonify({'success': False, 'message': '删除日志失败'})