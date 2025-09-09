#!/bin/bash

# 泰摸鱼吧 - Celery 启动脚本
# 用于启动 Celery Beat 和 Worker 进程

echo "启动泰摸鱼吧定时任务服务..."

# 进入项目目录
cd /Users/apple/Taifish/TaifishingV4

# 激活虚拟环境
source venv/bin/activate

# 检查Redis是否运行
if ! redis-cli ping > /dev/null 2>&1; then
    echo "错误: Redis服务未运行，请先启动Redis"
    exit 1
fi

# 启动Celery Beat (调度器)
echo "启动Celery Beat调度器..."
celery -A app.celery beat --loglevel=info --detach

# 等待一下确保Beat启动
sleep 2

# 启动Celery Worker (工作进程)
echo "启动Celery Worker工作进程..."
celery -A app.celery worker --loglevel=info --detach

# 检查进程状态
echo "检查Celery进程状态..."
ps aux | grep celery | grep -v grep

echo "定时任务服务启动完成！"
echo "Beat进程负责调度定时任务"
echo "Worker进程负责执行任务"
echo ""
echo "查看日志: tail -f /tmp/celery_*.log"
echo "停止服务: pkill -f 'celery.*beat' && pkill -f 'celery.*worker'"
