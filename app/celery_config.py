# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - Celery配置
"""

from celery import Celery
from celery.schedules import crontab
import os

# 创建Celery实例
celery = Celery('taifish')

# 配置Celery
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery.conf.update(
    broker_url=redis_url,
    result_backend=redis_url,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟
    task_soft_time_limit=25 * 60,  # 25分钟
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """配置定时任务"""
    from app.models.task import Task
    from app import create_app
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 获取所有活跃的定时任务
        active_tasks = Task.query.filter_by(is_active=True).all()
        
        for task in active_tasks:
            if task.schedule:
                # 解析cron表达式
                cron_parts = task.schedule.split()
                if len(cron_parts) == 5:
                    minute, hour, day, month, day_of_week = cron_parts
                    
                    # 添加定时任务
                    sender.add_periodic_task(
                        crontab(
                            minute=minute,
                            hour=hour,
                            day_of_month=day,
                            month_of_year=month,
                            day_of_week=day_of_week
                        ),
                        execute_task.s(task.id),
                        name=f'periodic-{task.name}'
                    )

@celery.task(bind=True)
def execute_task(self, task_id):
    """执行定时任务"""
    from app.services.task_executor import TaskExecutor
    
    executor = TaskExecutor()
    result = executor.execute_task(task_id)
    
    return result

# 注册任务
celery.task(execute_task)
