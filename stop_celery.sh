#!/bin/bash

# 泰摸鱼吧 - Celery 停止脚本
# 用于停止 Celery Beat 和 Worker 进程

echo "停止泰摸鱼吧定时任务服务..."

# 停止Celery Beat进程
echo "停止Celery Beat调度器..."
pkill -f 'celery.*beat'

# 停止Celery Worker进程
echo "停止Celery Worker工作进程..."
pkill -f 'celery.*worker'

# 等待进程完全停止
sleep 2

# 检查是否还有残留进程
remaining=$(ps aux | grep celery | grep -v grep | wc -l)
if [ $remaining -gt 0 ]; then
    echo "强制停止残留进程..."
    pkill -9 -f 'celery'
    sleep 1
fi

# 最终检查
remaining=$(ps aux | grep celery | grep -v grep | wc -l)
if [ $remaining -eq 0 ]; then
    echo "定时任务服务已完全停止"
else
    echo "警告: 仍有 $remaining 个Celery进程在运行"
    ps aux | grep celery | grep -v grep
fi
