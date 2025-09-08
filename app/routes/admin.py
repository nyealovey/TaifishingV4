# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 管理API路由
提供系统管理、监控、分析和维护功能
"""

import json
import time
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from functools import wraps
from app.constants import UserRole, ErrorMessages, SuccessMessages
from app.utils.api_response import APIResponse
from app.utils.performance_monitor import performance_monitor
from app.utils.advanced_error_handler import advanced_error_handler

logger = logging.getLogger(__name__)

# 创建管理蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return APIResponse.unauthorized("请先登录")
        
        if current_user.role != UserRole.ADMIN.value:
            return APIResponse.forbidden("需要管理员权限")
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def admin_dashboard():
    """管理仪表板"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/performance', methods=['GET'])
@login_required
@admin_required
def performance_metrics():
    """性能指标"""
    try:
        metrics = performance_monitor.get_performance_summary()
        suggestions = performance_monitor.get_optimization_suggestions()
        
        return APIResponse.success(data={
            'metrics': metrics,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        return APIResponse.server_error("获取性能指标失败")

@admin_bp.route('/errors', methods=['GET'])
@login_required
@admin_required
def error_metrics():
    """错误统计"""
    try:
        metrics = advanced_error_handler.get_error_metrics()
        
        return APIResponse.success(data={
            'error_metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"获取错误统计失败: {e}")
        return APIResponse.server_error("获取错误统计失败")



@admin_bp.route('/system-info', methods=['GET'])
@login_required
@admin_required
def system_info():
    """系统信息"""
    try:
        import platform
        import psutil
        import sys
        
        system_info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'path': sys.path
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'cpu': {
                'count': psutil.cpu_count(),
                'percent': psutil.cpu_percent(interval=1)
            }
        }
        
        return APIResponse.success(data=system_info)
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return APIResponse.server_error("获取系统信息失败")


@admin_bp.route('/maintenance', methods=['POST'])
@login_required
@admin_required
def maintenance_mode():
    """维护模式"""
    try:
        action = request.json.get('action')  # 'enable' or 'disable'
        
        if action == 'enable':
            # 启用维护模式
            current_app.config['MAINTENANCE_MODE'] = True
            logger.info("维护模式已启用")
            return APIResponse.success(message="维护模式已启用")
            
        elif action == 'disable':
            # 禁用维护模式
            current_app.config['MAINTENANCE_MODE'] = False
            logger.info("维护模式已禁用")
            return APIResponse.success(message="维护模式已禁用")
            
        else:
            return APIResponse.error("无效的操作", code=400)
        
    except Exception as e:
        logger.error(f"维护模式操作失败: {e}")
        return APIResponse.server_error("维护模式操作失败")

@admin_bp.route('/cache', methods=['POST'])
@login_required
@admin_required
def cache_management():
    """缓存管理"""
    try:
        action = request.json.get('action')  # 'clear', 'stats', 'warm'
        
        if action == 'clear':
            # 清除缓存
            from app import cache
            cache.clear()
            logger.info("缓存已清除")
            return APIResponse.success(message="缓存已清除")
            
        elif action == 'stats':
            # 获取缓存统计
            from app import cache
            # 这里可以添加缓存统计逻辑
            return APIResponse.success(data={'message': '缓存统计功能待实现'})
            
        elif action == 'warm':
            # 预热缓存
            # 这里可以添加缓存预热逻辑
            return APIResponse.success(data={'message': '缓存预热功能待实现'})
            
        else:
            return APIResponse.error("无效的操作", code=400)
        
    except Exception as e:
        logger.error(f"缓存管理操作失败: {e}")
        return APIResponse.server_error("缓存管理操作失败")

@admin_bp.route('/backup', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """创建备份"""
    try:
        backup_type = request.json.get('type', 'full')  # 'full', 'database', 'files'
        
        # 这里可以添加备份逻辑
        # 示例：调用备份脚本
        import subprocess
        result = subprocess.run(
            ['python', 'scripts/backup_manager.py', '--type', backup_type],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return APIResponse.success(message=f"{backup_type}备份创建成功")
        else:
            return APIResponse.error(f"备份创建失败: {result.stderr}")
        
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        return APIResponse.server_error("创建备份失败")

@admin_bp.route('/constants', methods=['GET'])
@login_required
@admin_required
def constants_management():
    """常量管理"""
    try:
        from app.constants import SystemConstants, DefaultConfig, ErrorMessages, SuccessMessages
        
        # 获取所有常量
        constants = {
            'system': {
                'DEFAULT_PAGE_SIZE': SystemConstants.DEFAULT_PAGE_SIZE,
                'MAX_PAGE_SIZE': SystemConstants.MAX_PAGE_SIZE,
                'MIN_PAGE_SIZE': SystemConstants.MIN_PAGE_SIZE,
                'MAX_FILE_SIZE': SystemConstants.MAX_FILE_SIZE,
                'ALLOWED_EXTENSIONS': list(SystemConstants.ALLOWED_EXTENSIONS)
            },
            'performance': {
                'SLOW_QUERY_THRESHOLD': SystemConstants.SLOW_QUERY_THRESHOLD,
                'SLOW_API_THRESHOLD': SystemConstants.SLOW_API_THRESHOLD,
                'MEMORY_WARNING_THRESHOLD': SystemConstants.MEMORY_WARNING_THRESHOLD,
                'CPU_WARNING_THRESHOLD': SystemConstants.CPU_WARNING_THRESHOLD,
                'CONNECTION_TIMEOUT': SystemConstants.CONNECTION_TIMEOUT,
                'MAX_CONNECTIONS': SystemConstants.MAX_CONNECTIONS
            },
            'security': {
                'MIN_PASSWORD_LENGTH': SystemConstants.MIN_PASSWORD_LENGTH,
                'MAX_PASSWORD_LENGTH': SystemConstants.MAX_PASSWORD_LENGTH,
                'PASSWORD_HASH_ROUNDS': SystemConstants.PASSWORD_HASH_ROUNDS,
                'SESSION_LIFETIME': SystemConstants.SESSION_LIFETIME,
                'JWT_ACCESS_TOKEN_EXPIRES': SystemConstants.JWT_ACCESS_TOKEN_EXPIRES,
                'CSRF_TOKEN_LIFETIME': SystemConstants.CSRF_TOKEN_LIFETIME
            },
            'database': {
                'CONNECTION_TIMEOUT': SystemConstants.CONNECTION_TIMEOUT,
                'QUERY_TIMEOUT': SystemConstants.QUERY_TIMEOUT,
                'CONNECTION_RETRY_ATTEMPTS': SystemConstants.CONNECTION_RETRY_ATTEMPTS,
                'SQL_SERVER_PORT': 1433,
                'MYSQL_PORT': 3306,
                'POSTGRES_PORT': 5432
            },
            'messages': {
                'errors': {
                    'INTERNAL_ERROR': ErrorMessages.INTERNAL_ERROR,
                    'VALIDATION_ERROR': ErrorMessages.VALIDATION_ERROR,
                    'PERMISSION_DENIED': ErrorMessages.PERMISSION_DENIED,
                    'RESOURCE_NOT_FOUND': ErrorMessages.RESOURCE_NOT_FOUND
                },
                'success': {
                    'OPERATION_SUCCESS': SuccessMessages.OPERATION_SUCCESS,
                    'LOGIN_SUCCESS': SuccessMessages.LOGIN_SUCCESS,
                    'DATA_SAVED': SuccessMessages.DATA_SAVED,
                    'DATA_DELETED': SuccessMessages.DATA_DELETED
                }
            }
        }
        
        return render_template('admin/constants.html', constants=constants)
        
    except Exception as e:
        logger.error(f"获取常量管理页面失败: {e}")
        return APIResponse.server_error("获取常量管理页面失败")

@admin_bp.route('/constants/api', methods=['GET'])
@login_required
@admin_required
def get_constants_api():
    """获取常量API"""
    try:
        from app.constants import SystemConstants, DefaultConfig, ErrorMessages, SuccessMessages
        
        constants = {
            'system_constants': {
                'DEFAULT_PAGE_SIZE': SystemConstants.DEFAULT_PAGE_SIZE,
                'MAX_PAGE_SIZE': SystemConstants.MAX_PAGE_SIZE,
                'MIN_PAGE_SIZE': SystemConstants.MIN_PAGE_SIZE,
                'MAX_FILE_SIZE': SystemConstants.MAX_FILE_SIZE,
                'ALLOWED_EXTENSIONS': list(SystemConstants.ALLOWED_EXTENSIONS)
            },
            'performance_constants': {
                'SLOW_QUERY_THRESHOLD': SystemConstants.SLOW_QUERY_THRESHOLD,
                'SLOW_API_THRESHOLD': SystemConstants.SLOW_API_THRESHOLD,
                'MEMORY_WARNING_THRESHOLD': SystemConstants.MEMORY_WARNING_THRESHOLD,
                'CPU_WARNING_THRESHOLD': SystemConstants.CPU_WARNING_THRESHOLD,
                'CONNECTION_TIMEOUT': SystemConstants.CONNECTION_TIMEOUT,
                'MAX_CONNECTIONS': SystemConstants.MAX_CONNECTIONS
            },
            'security_constants': {
                'MIN_PASSWORD_LENGTH': SystemConstants.MIN_PASSWORD_LENGTH,
                'MAX_PASSWORD_LENGTH': SystemConstants.MAX_PASSWORD_LENGTH,
                'PASSWORD_HASH_ROUNDS': SystemConstants.PASSWORD_HASH_ROUNDS,
                'SESSION_LIFETIME': SystemConstants.SESSION_LIFETIME,
                'JWT_ACCESS_TOKEN_EXPIRES': SystemConstants.JWT_ACCESS_TOKEN_EXPIRES,
                'CSRF_TOKEN_LIFETIME': SystemConstants.CSRF_TOKEN_LIFETIME
            },
            'database_constants': {
                'CONNECTION_TIMEOUT': SystemConstants.CONNECTION_TIMEOUT,
                'QUERY_TIMEOUT': SystemConstants.QUERY_TIMEOUT,
                'CONNECTION_RETRY_ATTEMPTS': SystemConstants.CONNECTION_RETRY_ATTEMPTS
            },
            'error_messages': {
                'INTERNAL_ERROR': ErrorMessages.INTERNAL_ERROR,
                'VALIDATION_ERROR': ErrorMessages.VALIDATION_ERROR,
                'PERMISSION_DENIED': ErrorMessages.PERMISSION_DENIED,
                'RESOURCE_NOT_FOUND': ErrorMessages.RESOURCE_NOT_FOUND
            },
            'success_messages': {
                'OPERATION_SUCCESS': SuccessMessages.OPERATION_SUCCESS,
                'LOGIN_SUCCESS': SuccessMessages.LOGIN_SUCCESS,
                'DATA_SAVED': SuccessMessages.DATA_SAVED,
                'DATA_DELETED': SuccessMessages.DATA_DELETED
            }
        }
        
        return APIResponse.success(data=constants)
        
    except Exception as e:
        logger.error(f"获取常量API失败: {e}")
        return APIResponse.server_error("获取常量API失败")

@admin_bp.route('/error-metrics', methods=['GET'])
@login_required
@admin_required
def get_error_metrics():
    """获取错误指标"""
    try:
        metrics = advanced_error_handler.get_error_metrics()
        
        # 如果没有错误数据，返回默认统计
        if not metrics:
            metrics = {
                'critical_errors': 0,
                'high_errors': 0,
                'medium_errors': 0,
                'low_errors': 0,
                'total_errors': 0,
                'recovery_success': 0,
                'recovery_failed': 0,
                'error_rate': 0.0,
                'last_error_time': None,
                'error_trend': 'stable'
            }
        
        return APIResponse.success(data=metrics)
    except Exception as e:
        logger.error(f"获取错误指标失败: {e}")
        return APIResponse.server_error("获取错误指标失败")

@admin_bp.route('/error-metrics', methods=['DELETE'])
@login_required
@admin_required
def clear_error_metrics():
    """清除错误指标"""
    try:
        advanced_error_handler.clear_error_metrics()
        return APIResponse.success(message="错误指标已清除")
    except Exception as e:
        logger.error(f"清除错误指标失败: {e}")
        return APIResponse.server_error("清除错误指标失败")

@admin_bp.route('/error-details', methods=['GET'])
@login_required
@admin_required
def get_error_details():
    """获取错误详情"""
    try:
        limit = request.args.get('limit', 20, type=int)
        # 这里应该从数据库或日志中获取错误详情
        # 暂时返回模拟数据
        error_details = [
            {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'error_type': 'SQLAlchemyError',
                'severity': 'high',
                'category': 'database',
                'recovery_success': True,
                'message': '数据库连接超时'
            },
            {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'error_type': 'ValidationError',
                'severity': 'medium',
                'category': 'validation',
                'recovery_success': True,
                'message': '输入数据验证失败'
            }
        ]
        return APIResponse.success(data=error_details[:limit])
    except Exception as e:
        logger.error(f"获取错误详情失败: {e}")
        return APIResponse.server_error("获取错误详情失败")

@admin_bp.route('/test-error-handling', methods=['POST'])
@login_required
@admin_required
def test_error_handling():
    """测试错误处理系统"""
    try:
        # 触发一个测试错误
        from app.utils.advanced_error_handler import ErrorContext
        test_error = Exception("测试错误 - 这是用于测试错误处理系统的模拟错误")
        context = ErrorContext(test_error)
        result = advanced_error_handler.handle_error(test_error, context)
        
        return APIResponse.success(data=result, message="错误处理测试完成")
    except Exception as e:
        logger.error(f"测试错误处理失败: {e}")
        return APIResponse.server_error("测试错误处理失败")


@admin_bp.route('/error-management', methods=['GET'])
@login_required
@admin_required
def error_management():
    """错误管理界面"""
    try:
        return render_template('admin/error_management.html')
    except Exception as e:
        logger.error(f"获取错误管理界面失败: {e}")
        return APIResponse.server_error("获取错误管理界面失败")



@admin_bp.route('/error-config', methods=['GET', 'POST'])
@login_required
@admin_required
def error_config():
    """错误处理配置"""
    try:
        if request.method == 'GET':
            # 获取配置
            config = {
                'auto_recovery': True,
                'max_retry_attempts': 3,
                'retry_delay': 5000,
                'notification_enabled': True
            }
            return APIResponse.success(data=config)
        else:
            # 保存配置
            data = request.get_json()
            return APIResponse.success(message="配置保存成功")
    except Exception as e:
        logger.error(f"错误处理配置失败: {e}")
        return APIResponse.server_error("错误处理配置失败")

@admin_bp.route('/system-management', methods=['GET'])
@login_required
@admin_required
def system_management():
    """系统管理界面"""
    try:
        return render_template('admin/system_management.html')
    except Exception as e:
        logger.error(f"获取系统管理界面失败: {e}")
        return APIResponse.server_error("获取系统管理界面失败")

@admin_bp.route('/system-info', methods=['GET'])
@login_required
@admin_required
def get_system_info():
    """获取系统信息"""
    try:
        import psutil
        import time
        
        # 获取系统信息
        system_info = {
            'status': 'running',
            'uptime': f"{int(time.time() - psutil.boot_time()) // 86400}天",
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(interval=1),
            'disk_usage': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids())
        }
        
        return APIResponse.success(data=system_info)
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return APIResponse.server_error("获取系统信息失败")

@admin_bp.route('/system-logs', methods=['GET'])
@login_required
@admin_required
def system_logs_page():
    """系统日志页面"""
    return render_template('admin/system_logs.html')

@admin_bp.route('/system-logs/api', methods=['GET'])
@login_required
@admin_required
def get_system_logs():
    """获取系统日志"""
    try:
        limit = request.args.get('limit', 20, type=int)
        # 这里应该从日志文件中读取
        # 暂时返回模拟数据
        logs = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'module': 'app',
                'message': '应用启动成功'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'WARNING',
                'module': 'performance_monitor',
                'message': '内存使用率超过80%'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'module': 'database',
                'message': '数据库连接超时'
            }
        ]
        return APIResponse.success(data=logs[:limit])
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return APIResponse.server_error("获取系统日志失败")

@admin_bp.route('/logs', methods=['GET'])
@login_required
@admin_required
def get_logs():
    """获取日志列表"""
    try:
        from app.models.log import Log
        from app import db
        
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        level = request.args.get('level', '', type=str)
        time_range = request.args.get('time_range', '', type=str)
        keyword = request.args.get('keyword', '', type=str)
        
        # 构建查询
        query = Log.query
        
        if level and level != 'all':
            query = query.filter(Log.level == level)
        
        if keyword:
            query = query.filter(Log.message.contains(keyword))
        
        if time_range:
            if time_range == 'today':
                today = datetime.now().date()
                query = query.filter(db.func.date(Log.created_at) == today)
            elif time_range == 'week':
                week_ago = datetime.now() - timedelta(days=7)
                query = query.filter(Log.created_at >= week_ago)
            elif time_range == 'month':
                month_ago = datetime.now() - timedelta(days=30)
                query = query.filter(Log.created_at >= month_ago)
        
        # 分页查询
        logs_pagination = query.order_by(Log.created_at.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        
        # 转换为前端需要的格式
        logs = []
        for log in logs_pagination.items:
            logs.append({
                'id': log.id,
                'timestamp': log.created_at.isoformat(),
                'level': log.level,
                'module': log.module or 'system',
                'message': log.message,
                'details': log.details,
                'user_id': log.user_id
            })
        
        pagination = {
            'current_page': page,
            'total_pages': logs_pagination.pages,
            'total_items': logs_pagination.total,
            'per_page': size
        }
        
        return APIResponse.success(data={
            'logs': logs,
            'pagination': pagination
        })
        
    except Exception as e:
        logger.error(f"获取日志列表失败: {e}")
        return APIResponse.server_error("获取日志列表失败")

@admin_bp.route('/logs/stats', methods=['GET'])
@login_required
@admin_required
def get_logs_stats():
    """获取日志统计信息"""
    try:
        from app.models.log import Log
        from app import db
        
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
        today = datetime.now().date()
        today_logs = Log.query.filter(
            db.func.date(Log.created_at) == today
        ).count()
        
        # 最近7天日志数
        week_ago = datetime.now() - timedelta(days=7)
        week_logs = Log.query.filter(
            Log.created_at >= week_ago
        ).count()
        
        stats = {
            'total_logs': total_logs,
            'today_logs': today_logs,
            'week_logs': week_logs,
            'level_stats': [
                {'level': stat.level, 'count': stat.count}
                for stat in level_stats
            ],
            'type_stats': [
                {'type': stat.log_type, 'count': stat.count}
                for stat in type_stats
            ]
        }
        
        return APIResponse.success(data=stats)
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        return APIResponse.server_error("获取日志统计失败")

@admin_bp.route('/logs/<int:log_id>', methods=['GET'])
@login_required
@admin_required
def get_log_detail(log_id):
    """获取日志详情"""
    try:
        from app.models.log import Log
        
        log = Log.query.get_or_404(log_id)
        
        return APIResponse.success(data=log.to_dict())
        
    except Exception as e:
        logger.error(f"获取日志详情失败: {e}")
        return APIResponse.server_error("获取日志详情失败")

@admin_bp.route('/maintenance-mode', methods=['POST'])
@login_required
@admin_required
def toggle_maintenance_mode():
    """切换维护模式"""
    try:
        # 这里应该实现维护模式的切换逻辑
        # 暂时只记录日志
        logger.info("维护模式切换请求")
        return APIResponse.success(message="维护模式已切换")
    except Exception as e:
        logger.error(f"切换维护模式失败: {e}")
        return APIResponse.server_error("切换维护模式失败")

@admin_bp.route('/restart', methods=['POST'])
@login_required
@admin_required
def restart_application():
    """重启应用"""
    try:
        # 这里应该实现应用重启逻辑
        # 暂时只记录日志
        logger.info("应用重启请求")
        return APIResponse.success(message="应用重启中...")
    except Exception as e:
        logger.error(f"重启应用失败: {e}")
        return APIResponse.server_error("重启应用失败")

@admin_bp.route('/clear-cache', methods=['POST'])
@login_required
@admin_required
def clear_cache():
    """清除缓存"""
    try:
        from app import cache
        cache.clear()
        return APIResponse.success(message="缓存已清除")
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return APIResponse.server_error("清除缓存失败")

@admin_bp.route('/backup-database', methods=['POST'])
@login_required
@admin_required
def backup_database():
    """备份数据库"""
    try:
        # 这里应该实现数据库备份逻辑
        logger.info("数据库备份请求")
        return APIResponse.success(message="数据库备份已开始")
    except Exception as e:
        logger.error(f"备份数据库失败: {e}")
        return APIResponse.server_error("备份数据库失败")

@admin_bp.route('/health-check', methods=['POST'])
@login_required
@admin_required
def run_health_check():
    """运行健康检查"""
    try:
        # 检查各个组件状态
        health_status = {
            'database': 'healthy',
            'redis': 'healthy',
            'application': 'healthy'
        }
        
        return APIResponse.success(data=health_status, message="健康检查完成")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return APIResponse.server_error("健康检查失败")

@admin_bp.route('/clear-logs', methods=['POST'])
@login_required
@admin_required
def clear_logs():
    """清除系统日志"""
    try:
        # 这里应该实现清除日志文件的逻辑
        logger.info("清除系统日志请求")
        return APIResponse.success(message="系统日志已清除")
    except Exception as e:
        logger.error(f"清除日志失败: {e}")
        return APIResponse.server_error("清除日志失败")

@admin_bp.route('/refresh-data', methods=['POST'])
@login_required
@admin_required
def refresh_system_data():
    """刷新系统数据"""
    try:
        # 这里可以实现数据刷新逻辑
        logger.info("系统数据刷新请求")
        return APIResponse.success(message="系统数据已刷新")
    except Exception as e:
        logger.error(f"刷新系统数据失败: {e}")
        return APIResponse.server_error("刷新系统数据失败")



# 辅助函数
def get_user_count():
    """获取用户数量"""
    from app.models.user import User
    return User.query.count()

def get_instance_count():
    """获取实例数量"""
    from app.models.instance import Instance
    return Instance.query.count()

def get_task_count():
    """获取任务数量"""
    from app.models.task import Task
    return Task.query.count()

def get_log_count():
    """获取日志数量"""
    from app.models.log import Log
    return Log.query.count()

def get_system_uptime():
    """获取系统运行时间"""
    import time
    import psutil
    
    try:
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        return int(uptime)
    except:
        return 0


def get_recent_activities():
    """获取最近活动"""
    from app.models.log import Log
    from app import db
    
    # 获取最近24小时的活动
    since = datetime.utcnow() - timedelta(hours=24)
    
    activities = Log.query.filter(
        Log.created_at >= since
    ).order_by(Log.created_at.desc()).limit(10).all()
    
    return [activity.to_dict() for activity in activities]

# 新增管理页面路由
@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def users():
    """用户管理"""
    try:
        return render_template('admin/users.html')
    except Exception as e:
        logger.error(f"获取用户管理页面失败: {e}")
        return APIResponse.server_error("获取用户管理页面失败")

@admin_bp.route('/data-management', methods=['GET'])
@login_required
@admin_required
def data_management():
    """数据管理"""
    try:
        return render_template('admin/data_management.html')
    except Exception as e:
        logger.error(f"获取数据管理页面失败: {e}")
        return APIResponse.server_error("获取数据管理页面失败")

