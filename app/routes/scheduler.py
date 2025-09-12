"""
定时任务管理路由
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.utils.api_response import APIResponse
from app.scheduler import get_scheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/scheduler')


@scheduler_bp.route('/')
@login_required
@admin_required
def index():
    """定时任务管理页面"""
    return render_template('scheduler/index.html')


@scheduler_bp.route('/api/jobs')
@login_required
@admin_required
def get_jobs():
    """获取所有定时任务"""
    try:
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", status_code=500)
        jobs = scheduler.get_jobs()
        logger.info(f"获取到 {len(jobs)} 个任务")
        jobs_data = []
        
        for job in jobs:
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'func': job.func.__name__ if hasattr(job.func, '__name__') else str(job.func),
                'args': job.args,
                'kwargs': job.kwargs,
                'misfire_grace_time': job.misfire_grace_time,
                'max_instances': job.max_instances,
                'coalesce': job.coalesce
            }
            jobs_data.append(job_info)
        
        return APIResponse.success(data=jobs_data, message="任务列表获取成功")
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return APIResponse.error(f"获取任务列表失败: {str(e)}")


@scheduler_bp.route('/api/jobs/<job_id>')
@login_required
@admin_required
def get_job(job_id):
    """获取指定任务详情"""
    try:
        job = get_scheduler().get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", status_code=404)
        
        job_info = {
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger),
            'func': job.func.__name__ if hasattr(job.func, '__name__') else str(job.func),
            'args': job.args,
            'kwargs': job.kwargs,
            'misfire_grace_time': job.misfire_grace_time,
            'max_instances': job.max_instances,
            'coalesce': job.coalesce
        }
        
        return APIResponse.success(data=job_info, message="任务详情获取成功")
        
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return APIResponse.error(f"获取任务详情失败: {str(e)}")


@scheduler_bp.route('/api/jobs', methods=['POST'])
@login_required
@admin_required
def create_job():
    """创建新的定时任务"""
    try:
        data = request.get_json()
        logger.info(f"创建任务请求数据: {data}")
        
        # 验证必需字段
        required_fields = ['id', 'name', 'func', 'trigger_type']
        for field in required_fields:
            if field not in data:
                logger.error(f"缺少必需字段: {field}")
                return APIResponse.error(f"缺少必需字段: {field}", status_code=400)
        
        # 构建触发器
        trigger = _build_trigger(data)
        if not trigger:
            return APIResponse.error("无效的触发器配置", status_code=400)
        
        # 获取任务函数
        task_func = _get_task_function(data['func'])
        if not task_func:
            return APIResponse.error(f"未找到任务函数: {data['func']}", status_code=400)
        
        # 添加任务
        job = get_scheduler().add_job(
            func=task_func,
            trigger=trigger,
            id=data['id'],
            name=data['name'],
            args=data.get('args', []),
            kwargs=data.get('kwargs', {}),
            replace_existing=True
        )
        
        logger.info(f"任务创建成功: {job.id}")
        return APIResponse.success(data={'job_id': job.id}, message="任务创建成功")
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return APIResponse.error(f"创建任务失败: {str(e)}")


@scheduler_bp.route('/api/jobs/<job_id>', methods=['PUT'])
@login_required
@admin_required
def update_job(job_id):
    """更新定时任务"""
    try:
        data = request.get_json()
        
        # 检查任务是否存在
        job = get_scheduler().get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", status_code=404)
        
        # 构建新的触发器
        if 'trigger_type' in data:
            trigger = _build_trigger(data)
            if not trigger:
                return APIResponse.error("无效的触发器配置", status_code=400)
            
            # 更新任务
            get_scheduler().modify_job(
                job_id,
                trigger=trigger,
                name=data.get('name', job.name),
                args=data.get('args', job.args),
                kwargs=data.get('kwargs', job.kwargs)
            )
        else:
            # 只更新其他属性
            get_scheduler().modify_job(
                job_id,
                name=data.get('name', job.name),
                args=data.get('args', job.args),
                kwargs=data.get('kwargs', job.kwargs)
            )
        
        logger.info(f"任务更新成功: {job_id}")
        return APIResponse.success("任务更新成功")
        
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return APIResponse.error(f"更新任务失败: {str(e)}")


@scheduler_bp.route('/api/jobs/<job_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_job(job_id):
    """删除定时任务"""
    try:
        get_scheduler().remove_job(job_id)
        logger.info(f"任务删除成功: {job_id}")
        return APIResponse.success("任务删除成功")
        
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return APIResponse.error(f"删除任务失败: {str(e)}")


@scheduler_bp.route('/api/jobs/<job_id>/pause', methods=['POST'])
@login_required
@admin_required
def pause_job(job_id):
    """暂停任务"""
    try:
        get_scheduler().pause_job(job_id)
        logger.info(f"任务暂停成功: {job_id}")
        return APIResponse.success("任务暂停成功")
        
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        return APIResponse.error(f"暂停任务失败: {str(e)}")


@scheduler_bp.route('/api/jobs/<job_id>/resume', methods=['POST'])
@login_required
@admin_required
def resume_job(job_id):
    """恢复任务"""
    try:
        get_scheduler().resume_job(job_id)
        logger.info(f"任务恢复成功: {job_id}")
        return APIResponse.success("任务恢复成功")
        
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        return APIResponse.error(f"恢复任务失败: {str(e)}")


@scheduler_bp.route('/api/jobs/<job_id>/run', methods=['POST'])
@login_required
@admin_required
def run_job(job_id):
    """立即执行任务"""
    try:
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", status_code=500)
            
        job = scheduler.get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", status_code=404)
        
        logger.info(f"开始立即执行任务: {job_id} - {job.name}")
        
        # 立即执行任务
        try:
            result = job.func(*job.args, **job.kwargs)
            logger.info(f"任务立即执行成功: {job_id} - 结果: {result}")
            return APIResponse.success(data={"result": str(result)}, message="任务执行成功")
        except Exception as func_error:
            logger.error(f"任务函数执行失败: {job_id} - {func_error}")
            return APIResponse.error(f"任务执行失败: {str(func_error)}")
        
    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        return APIResponse.error(f"执行任务失败: {str(e)}")


def _get_task_function(func_name):
    """获取任务函数"""
    from app.tasks import (
        cleanup_old_logs,
        backup_database,
        sync_accounts,
        generate_reports
    )
    
    # 任务函数映射
    task_functions = {
        'cleanup_old_logs': cleanup_old_logs,
        'backup_database': backup_database,
        'sync_accounts': sync_accounts,
        'generate_reports': generate_reports
    }
    
    return task_functions.get(func_name)


def _build_trigger(data):
    """构建触发器"""
    trigger_type = data.get('trigger_type')
    
    if trigger_type == 'cron':
        return CronTrigger(
            year=data.get('year'),
            month=data.get('month'),
            day=data.get('day'),
            week=data.get('week'),
            day_of_week=data.get('day_of_week'),
            hour=data.get('hour'),
            minute=data.get('minute'),
            second=data.get('second')
        )
    elif trigger_type == 'interval':
        return IntervalTrigger(
            weeks=data.get('weeks'),
            days=data.get('days'),
            hours=data.get('hours'),
            minutes=data.get('minutes'),
            seconds=data.get('seconds')
        )
    elif trigger_type == 'date':
        run_date = data.get('run_date')
        if run_date:
            from datetime import datetime
            return DateTrigger(run_date=datetime.fromisoformat(run_date))
    
    return None
