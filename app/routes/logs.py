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
    获取合并后的请求日志数据
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码
        per_page: 每页数量
        
    Returns:
        dict: 包含合并后日志和分页信息的字典
    """
    try:
        from app.models.log import Log
        import re
        from collections import defaultdict
        
        # 获取所有日志
        all_logs = query.order_by(Log.created_at.desc()).all()
        
        # 分离请求日志和其他日志
        request_logs = []
        other_logs = []
        
        for log in all_logs:
            if "请求开始:" in log.message or "请求结束:" in log.message:
                request_logs.append(log)
            else:
                other_logs.append(log)
        
        # 合并请求日志
        merged_requests = {}
        
        for log in request_logs:
            # 提取请求路径
            if "请求开始:" in log.message:
                # 提取路径，如 "请求开始: GET /dashboard/api/status" -> "/dashboard/api/status"
                match = re.search(r'请求开始:\s+\w+\s+(.+)', log.message)
                if match:
                    path = match.group(1)
                    if path not in merged_requests:
                        merged_requests[path] = {
                            'start_log': log,
                            'end_log': None,
                            'start_time': log.created_at,
                            'end_time': None,
                            'status_code': None,
                            'duration': None
                        }
            elif "请求结束:" in log.message:
                # 提取路径和状态码，如 "请求结束: GET /dashboard/api/status - 200" -> ("/dashboard/api/status", "200")
                match = re.search(r'请求结束:\s+\w+\s+(.+?)\s+-\s+(\d+)', log.message)
                if match:
                    path = match.group(1)
                    status_code = match.group(2)
                    if path in merged_requests:
                        merged_requests[path]['end_log'] = log
                        merged_requests[path]['end_time'] = log.created_at
                        merged_requests[path]['status_code'] = status_code
                        # 计算持续时间
                        if merged_requests[path]['start_time']:
                            duration = (log.created_at - merged_requests[path]['start_time']).total_seconds() * 1000
                            merged_requests[path]['duration'] = round(duration, 2)
                    else:
                        # 如果没有找到对应的开始日志，创建一个
                        merged_requests[path] = {
                            'start_log': None,
                            'end_log': log,
                            'start_time': None,
                            'end_time': log.created_at,
                            'status_code': status_code,
                            'duration': None
                        }
        
        # 创建合并后的日志列表
        merged_logs_list = []
        
        # 添加合并的请求日志
        for path, request_data in merged_requests.items():
            # 确定最严重的级别
            levels = []
            if request_data['start_log']:
                levels.append(request_data['start_log'].level)
            if request_data['end_log']:
                levels.append(request_data['end_log'].level)
            
            # 级别优先级：CRITICAL > ERROR > WARNING > INFO > DEBUG
            level_priority = {'CRITICAL': 5, 'ERROR': 4, 'WARNING': 3, 'INFO': 2, 'DEBUG': 1}
            max_level = max(levels, key=lambda x: level_priority.get(x, 0)) if levels else 'INFO'
            
            # 确定显示的消息
            if request_data['end_log']:
                message = f"请求: {path} - {request_data['status_code']}"
                if request_data['duration']:
                    message += f" ({request_data['duration']}ms)"
            else:
                message = f"请求: {path} (进行中)"
            
            # 创建合并后的日志对象
            merged_log = {
                'id': request_data['end_log'].id if request_data['end_log'] else request_data['start_log'].id,
                'level': max_level,
                'log_type': 'request',
                'module': 'request_handler',
                'message': message,
                'details': f"开始时间: {request_data['start_time'] if request_data['start_time'] else '未知'}, 结束时间: {request_data['end_time'] if request_data['end_time'] else '进行中'}",
                'user_id': request_data['end_log'].user_id if request_data['end_log'] else (request_data['start_log'].user_id if request_data['start_log'] else None),
                'ip_address': request_data['end_log'].ip_address if request_data['end_log'] else (request_data['start_log'].ip_address if request_data['start_log'] else None),
                'user_agent': request_data['end_log'].user_agent if request_data['end_log'] else (request_data['start_log'].user_agent if request_data['start_log'] else None),
                'created_at': request_data['end_time'] if request_data['end_time'] else request_data['start_time'],
                'is_merged': True,
                'original_logs': [request_data['start_log'], request_data['end_log']],
                # 添加合并日志的详细信息
                'merged_info': {
                    'path': str(path) if path else None,
                    'status_code': int(request_data['status_code']) if request_data['status_code'] else None,
                    'duration': float(request_data['duration']) if request_data['duration'] is not None else None,
                    'start_time': request_data['start_time'].isoformat() if request_data['start_time'] else None,
                    'end_time': request_data['end_time'].isoformat() if request_data['end_time'] else None,
                    'start_log_id': int(request_data['start_log'].id) if request_data['start_log'] else None,
                    'end_log_id': int(request_data['end_log'].id) if request_data['end_log'] else None,
                    'start_level': str(request_data['start_log'].level) if request_data['start_log'] else None,
                    'end_level': str(request_data['end_log'].level) if request_data['end_log'] else None
                }
            }
            merged_logs_list.append(merged_log)
        
        # 添加其他日志
        for log in other_logs:
            merged_logs_list.append({
                'id': log.id,
                'level': log.level,
                'log_type': log.log_type,
                'module': log.module,
                'message': log.message,
                'details': log.details,
                'user_id': log.user_id,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'created_at': log.created_at,
                'is_merged': False,
                'original_logs': [log]
            })
        
        # 按时间排序（最新的在前）
        merged_logs_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        # 分页
        total = len(merged_logs_list)
        start = (page - 1) * per_page
        end = start + per_page
        items = merged_logs_list[start:end]
        
        # 创建分页对象
        class Pagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
                
            def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
                last = self.pages
                for num in range(1, last + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and num < self.page + right_current) or \
                       num > last - right_edge:
                        yield num
        
        pagination = Pagination(page, per_page, total, items)
        
        return pagination
        
    except Exception as e:
        logging.error(f"获取合并日志失败: {e}")
        # 如果合并失败，返回原始分页
        return query.order_by(Log.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )


@logs_bp.route("/")
@login_required
def index():
    """系统日志页面"""
    try:
        from app.models.log import Log
        
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        level = request.args.get("level", "", type=str)
        module = request.args.get("module", "", type=str)
        start_date = request.args.get("start_date", "", type=str)
        end_date = request.args.get("end_date", "", type=str)
        search = request.args.get("search", "", type=str)
        
        # 构建查询
        query = Log.query
        
        if level and level != "all":
            query = query.filter(Log.level == level)
            
        if module and module != "all":
            query = query.filter(Log.module == module)
            
        if search:
            query = query.filter(Log.message.contains(search))
            
        if start_date:
            from datetime import datetime
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Log.created_at >= start_datetime)
            
        if end_date:
            from datetime import datetime
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            # 添加一天到结束日期，使其包含整天
            from datetime import timedelta
            end_datetime = end_datetime + timedelta(days=1)
            query = query.filter(Log.created_at < end_datetime)
        
        # 获取合并后的日志数据
        merged_logs = get_merged_request_logs(query, page, 20)
        
        return render_template("logs/system_logs.html", 
                             merged_logs=merged_logs,
                             level=level,
                             module=module,
                             start_date=start_date,
                             end_date=end_date,
                             search=search)
                             
    except Exception as e:
        logging.error(f"加载日志页面失败: {e}")
        flash("加载日志页面失败", "error")
        return render_template("logs/system_logs.html", 
                             merged_logs=None,
                             level="",
                             module="",
                             start_date="",
                             end_date="",
                             search="")


@logs_bp.route("/api", methods=["GET"])
@login_required
def get_system_logs():
    """获取系统日志API"""
    try:
        from app.models.log import Log

        page = request.args.get("page", 1, type=int)
        size = request.args.get("size", 20, type=int)
        level = request.args.get("level", "", type=str)
        time_range = request.args.get("time_range", "", type=str)
        keyword = request.args.get("keyword", "", type=str)

        # 构建查询
        query = Log.query

        if level and level != "all":
            query = query.filter(Log.level == level)

        if keyword:
            query = query.filter(Log.message.contains(keyword))

        if time_range:
            # 使用UTC时间进行筛选，因为数据库存储的是UTC时间
            if time_range == "1h":
                hour_ago = datetime.utcnow() - timedelta(hours=1)
                query = query.filter(Log.created_at >= hour_ago)
            elif time_range == "today":
                # 对于今天，需要转换为UTC日期
                from app.utils.timezone import CHINA_TZ

                china_today = datetime.now(CHINA_TZ).date()
                # 转换为UTC的今天开始和结束时间
                utc_today_start = (
                    CHINA_TZ.localize(
                        datetime.combine(china_today, datetime.min.time())
                    )
                    .astimezone(pytz.UTC)
                    .replace(tzinfo=None)
                )
                utc_today_end = (
                    CHINA_TZ.localize(
                        datetime.combine(china_today, datetime.max.time())
                    )
                    .astimezone(pytz.UTC)
                    .replace(tzinfo=None)
                )
                query = query.filter(
                    Log.created_at >= utc_today_start, Log.created_at <= utc_today_end
                )
            elif time_range == "week":
                week_ago = datetime.utcnow() - timedelta(days=7)
                query = query.filter(Log.created_at >= week_ago)
            elif time_range == "month":
                month_ago = datetime.utcnow() - timedelta(days=30)
                query = query.filter(Log.created_at >= month_ago)

        # 分页查询
        logs_pagination = query.order_by(Log.created_at.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        # 转换为前端需要的格式
        from app.utils.timezone import format_china_time

        logs = []
        for log in logs_pagination.items:
            logs.append(
                {
                    "id": log.id,
                    "timestamp": format_china_time(log.created_at, "%Y-%m-%d %H:%M:%S"),
                    "level": log.level,
                    "module": log.module or "system",
                    "message": log.message,
                    "details": log.details,
                    "user_id": log.user_id,
                }
            )

        pagination = {
            "page": page,
            "pages": logs_pagination.pages,
            "per_page": size,
            "total": logs_pagination.total,
            "has_next": logs_pagination.has_next,
            "has_prev": logs_pagination.has_prev,
        }

        return APIResponse.success(data={"logs": logs, "pagination": pagination})

    except Exception as e:
        logging.error(f"获取系统日志失败: {e}")
        return APIResponse.server_error("获取系统日志失败")


@logs_bp.route("/stats", methods=["GET"])
@login_required
def get_logs_stats():
    """获取日志统计"""
    try:
        from app.models.log import Log
        from sqlalchemy import func

        # 总日志数
        total_logs = Log.query.count()

        # 按级别统计
        level_stats = (
            db.session.query(Log.level, func.count(Log.id).label("count"))
            .group_by(Log.level)
            .all()
        )

        level_distribution = {stat.level: stat.count for stat in level_stats}

        # 按模块统计
        module_stats = (
            db.session.query(Log.module, func.count(Log.id).label("count"))
            .group_by(Log.module)
            .all()
        )

        module_distribution = {
            stat.module or "unknown": stat.count for stat in module_stats
        }

        # 最近24小时的日志
        recent_logs = Log.query.filter(
            Log.created_at >= datetime.now() - timedelta(hours=24)
        ).count()

        return APIResponse.success(
            data={
                "total_logs": total_logs,
                "level_distribution": level_distribution,
                "module_distribution": module_distribution,
                "recent_logs": recent_logs,
            }
        )

    except Exception as e:
        logging.error(f"获取日志统计失败: {e}")
        return APIResponse.server_error("获取日志统计失败")


# 旧版日志管理功能已移除


@logs_bp.route("/<int:log_id>")
@login_required
def detail(log_id):
    """日志详情"""
    log = Log.query.get_or_404(log_id)

    if request.is_json:
        # 格式化时间显示
        from app.utils.timezone import format_china_time

        log_dict = log.to_dict()
        log_dict["created_at"] = format_china_time(log.created_at, "%Y-%m-%d %H:%M:%S")
        return jsonify(log_dict)

    return render_template("logs/detail.html", log=log)


@logs_bp.route("/export")
@login_required
def export():
    """导出日志CSV"""
    try:
        # 获取查询参数（与index函数保持一致）
        level = request.args.get("level", "", type=str)
        module = request.args.get("module", "", type=str)
        start_date = request.args.get("start_date", "", type=str)
        end_date = request.args.get("end_date", "", type=str)
        search = request.args.get("search", "", type=str)
        
        # 构建查询（与index函数保持一致）
        query = Log.query
        
        if level and level != "all":
            query = query.filter(Log.level == level)
            
        if module and module != "all":
            query = query.filter(Log.module == module)
            
        if search:
            query = query.filter(Log.message.contains(search))
            
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Log.created_at >= start_datetime)
            
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            end_datetime = end_datetime + timedelta(days=1)
            query = query.filter(Log.created_at < end_datetime)
        
        # 获取所有日志（不分页）
        logs = query.order_by(Log.created_at.desc()).all()
        
        # 构建CSV数据
        import csv
        import io
        from flask import make_response
        from app.utils.timezone import format_china_time
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "时间", "级别", "类型", "模块", "用户", "IP地址", "消息", "详情"
        ])
        
        # 写入数据
        for log in logs:
            writer.writerow([
                format_china_time(log.created_at, "%Y-%m-%d %H:%M:%S") if log.created_at else "",
                log.level or "",
                log.log_type or "",
                log.module or "",
                log.user.username if log.user else "系统",
                log.ip_address or "",
                log.message or "",
                log.details or "",
            ])
        
        # 返回CSV文件
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return response
        
    except Exception as e:
        logging.error(f"导出日志失败: {e}")
        flash(f"导出失败: {str(e)}", "error")
        return redirect(url_for("logs.index"))


@logs_bp.route("/cleanup", methods=["POST"])
@login_required
def cleanup():
    """清理旧日志"""
    days = request.args.get("days", 30, type=int)

    try:
        # 删除指定天数前的日志
        cutoff_date = now() - timedelta(days=days)
        deleted_count = Log.query.filter(Log.created_at < cutoff_date).delete()

        db.session.commit()

        if request.is_json:
            return jsonify(
                {
                    "message": f"已清理 {deleted_count} 条 {days} 天前的日志",
                    "deleted_count": deleted_count,
                }
            )

        flash(f"已清理 {deleted_count} 条 {days} 天前的日志", "success")

    except Exception as e:
        db.session.rollback()
        logging.error(f"清理日志失败: {e}")

        if request.is_json:
            return jsonify({"error": "清理日志失败，请重试"}), 500

        flash("清理日志失败，请重试", "error")

    return redirect(url_for("logs.index"))


@logs_bp.route("/statistics")
@login_required
def statistics():
    """日志统计"""
    # 获取统计信息
    stats = get_log_statistics()

    if request.is_json:
        return jsonify(stats)

    return render_template("logs/statistics.html", stats=stats)


def get_log_statistics():
    """获取日志统计信息"""
    try:
        # 总日志数
        total_logs = Log.query.count()

        # 各级别日志数量
        level_stats = (
            db.session.query(Log.level, db.func.count(Log.id).label("count"))
            .group_by(Log.level)
            .all()
        )

        # 各类型日志数量
        type_stats = (
            db.session.query(Log.log_type, db.func.count(Log.id).label("count"))
            .group_by(Log.log_type)
            .all()
        )

        # 今日日志数
        today = now().date()
        today_logs = Log.query.filter(db.func.date(Log.created_at) == today).count()

        # 最近7天日志趋势
        week_ago = now() - timedelta(days=7)
        week_logs = Log.query.filter(Log.created_at >= week_ago).count()

        # 错误日志数
        error_logs = Log.query.filter(Log.level.in_(["ERROR", "CRITICAL"])).count()

        # 用户操作统计
        user_stats = (
            db.session.query(User.username, db.func.count(Log.id).label("log_count"))
            .outerjoin(Log)
            .group_by(User.id, User.username)
            .all()
        )

        return {
            "total_logs": total_logs,
            "today_logs": today_logs,
            "week_logs": week_logs,
            "error_logs": error_logs,
            "level_stats": [
                {"level": stat.level, "count": stat.count} for stat in level_stats
            ],
            "type_stats": [
                {"type": stat.log_type, "count": stat.count} for stat in type_stats
            ],
            "user_stats": [
                {"username": stat.username, "count": stat.log_count or 0}
                for stat in user_stats
            ],
        }
    except Exception as e:
        logging.error(f"获取日志统计失败: {e}")
        return {
            "total_logs": 0,
            "today_logs": 0,
            "week_logs": 0,
            "error_logs": 0,
            "level_stats": [],
            "type_stats": [],
            "user_stats": [],
        }


# API路由
@logs_bp.route("/api/logs")
@jwt_required()
def api_list():
    """获取日志列表API"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    logs = Log.query.order_by(Log.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        {
            "logs": [log.to_dict() for log in logs.items],
            "pagination": {
                "page": logs.page,
                "pages": logs.pages,
                "per_page": logs.per_page,
                "total": logs.total,
                "has_next": logs.has_next,
                "has_prev": logs.has_prev,
            },
        }
    )


@logs_bp.route("/api/logs/<int:log_id>")
@jwt_required()
def api_detail(log_id):
    """获取日志详情API"""
    log = Log.query.get_or_404(log_id)
    return jsonify(log.to_dict())


@logs_bp.route("/api/logs/statistics")
@jwt_required()
def api_statistics():
    """获取日志统计API"""
    stats = get_log_statistics()
    return jsonify(stats)
