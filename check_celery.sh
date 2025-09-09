#!/bin/bash

# 泰摸鱼吧 - Celery 状态检查脚本
# 用于检查 Celery Beat 和 Worker 进程状态

echo "=== 泰摸鱼吧定时任务服务状态检查 ==="
echo ""

# 检查Redis状态
echo "1. 检查Redis服务状态..."
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis服务正常运行"
else
    echo "   ❌ Redis服务未运行或连接失败"
    exit 1
fi

echo ""

# 检查Celery进程
echo "2. 检查Celery进程状态..."
beat_processes=$(ps aux | grep 'celery.*beat' | grep -v grep | wc -l)
worker_processes=$(ps aux | grep 'celery.*worker' | grep -v grep | wc -l)

if [ $beat_processes -gt 0 ]; then
    echo "   ✅ Celery Beat调度器: $beat_processes 个进程运行中"
else
    echo "   ❌ Celery Beat调度器: 未运行"
fi

if [ $worker_processes -gt 0 ]; then
    echo "   ✅ Celery Worker工作进程: $worker_processes 个进程运行中"
else
    echo "   ❌ Celery Worker工作进程: 未运行"
fi

echo ""

# 检查任务状态
echo "3. 检查定时任务状态..."
cd /Users/apple/Taifish/TaifishingV4
source venv/bin/activate

python3 -c "
from app import create_app
from app.models.task import Task
from app.models.sync_data import SyncData
from datetime import datetime, timedelta
from app.utils.timezone import now

app = create_app()
with app.app_context():
    # 检查启用的任务
    active_tasks = Task.query.filter_by(is_active=True).all()
    print(f'   启用的任务数量: {len(active_tasks)}')
    
    for task in active_tasks:
        print(f'   - {task.name}: {task.schedule} (最后运行: {task.last_run_at})')
    
    # 检查最近的同步记录
    recent_syncs = SyncData.query.filter_by(
        sync_type='task'
    ).order_by(SyncData.sync_time.desc()).limit(3).all()
    
    print(f'   最近同步记录: {len(recent_syncs)} 条')
    for sync in recent_syncs:
        print(f'   - {sync.sync_time}: {sync.status} - {sync.message}')
"

echo ""
echo "=== 状态检查完成 ==="
echo ""
echo "启动服务: ./start_celery.sh"
echo "停止服务: ./stop_celery.sh"
echo "查看日志: tail -f /tmp/celery_*.log"
