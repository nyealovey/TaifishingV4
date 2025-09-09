#!/bin/bash

# 泰摸鱼吧 - 启动定时任务服务
# 此脚本启动Celery Beat调度器和Worker

echo "🚀 启动泰摸鱼吧定时任务服务..."

# 检查Redis是否运行
echo "📡 检查Redis连接..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis未运行，请先启动Redis服务"
    echo "   可以使用: redis-server 或 brew services start redis"
    exit 1
fi
echo "✅ Redis连接正常"

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "🐍 激活虚拟环境..."
    source venv/bin/activate
fi

# 设置环境变量
export FLASK_APP=app
export FLASK_ENV=development

# 启动Celery Beat (定时调度器)
echo "⏰ 启动Celery Beat调度器..."
python3 start_celery_beat.py &
BEAT_PID=$!

# 启动Celery Worker (任务执行器)
echo "👷 启动Celery Worker..."
python3 start_celery_worker.py &
WORKER_PID=$!

echo "✅ 定时任务服务启动完成！"
echo "   Beat PID: $BEAT_PID"
echo "   Worker PID: $WORKER_PID"
echo ""
echo "📋 管理命令："
echo "   查看进程: ps aux | grep celery"
echo "   停止服务: kill $BEAT_PID $WORKER_PID"
echo "   查看日志: tail -f userdata/logs/app.log"
echo ""
echo "🎯 定时任务将按照配置的cron表达式自动执行"
echo "   当前配置: */5 * * * * (每5分钟执行一次)"

# 等待用户中断
trap "echo '🛑 停止定时任务服务...'; kill $BEAT_PID $WORKER_PID; exit 0" INT
wait
