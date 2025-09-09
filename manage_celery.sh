#!/bin/bash

# 泰摸鱼吧 - Celery定时器管理脚本

PROJECT_DIR="/Users/apple/Taifish/TaifishingV4"
PID_FILE="$PROJECT_DIR/celerybeat.pid"
LOG_FILE="$PROJECT_DIR/userdata/logs/celery_beat.log"

# 进入项目目录
cd "$PROJECT_DIR"

# 激活虚拟环境
source venv/bin/activate

# 创建日志目录
mkdir -p userdata/logs

start() {
    echo "启动泰摸鱼吧 Celery Beat 定时器..."
    
    # 检查Redis
    if ! redis-cli -a taifish_redis_pass ping > /dev/null 2>&1; then
        echo "错误: Redis服务未运行或密码错误，请先启动Redis并设置密码"
        exit 1
    fi
    
    # 检查是否已经运行
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Celery Beat已经在运行 (PID: $(cat $PID_FILE))"
        exit 1
    fi
    
    # 设置正确的环境变量
    export REDIS_URL="redis://:taifish_redis_pass@localhost:6379/0"
    
    # 启动Celery Beat
    nohup python3 start_celery_beat_fixed.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    # 等待启动
    sleep 3
    
    # 检查是否启动成功
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Celery Beat启动成功 (PID: $(cat $PID_FILE))"
        echo "日志文件: $LOG_FILE"
        echo "使用 'tail -f $LOG_FILE' 查看日志"
    else
        echo "Celery Beat启动失败"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop() {
    echo "停止泰摸鱼吧 Celery Beat 定时器..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "Celery Beat已停止 (PID: $PID)"
        else
            echo "Celery Beat未运行"
        fi
        rm -f "$PID_FILE"
    else
        echo "PID文件不存在，尝试强制停止..."
        pkill -f "celery.*beat"
    fi
}

restart() {
    echo "重启泰摸鱼吧 Celery Beat 定时器..."
    stop
    sleep 2
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Celery Beat正在运行 (PID: $(cat $PID_FILE))"
        echo "日志文件: $LOG_FILE"
        echo "最近日志:"
        tail -n 5 "$LOG_FILE" 2>/dev/null || echo "无法读取日志文件"
    else
        echo "Celery Beat未运行"
    fi
}

logs() {
    echo "查看Celery Beat日志 (按Ctrl+C退出):"
    tail -f "$LOG_FILE"
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动Celery Beat定时器"
        echo "  stop    - 停止Celery Beat定时器"
        echo "  restart - 重启Celery Beat定时器"
        echo "  status  - 查看定时器状态"
        echo "  logs    - 查看定时器日志"
        echo ""
        echo "定时器功能:"
        echo "  - 执行定时任务调度"
        echo "  - 支持Cron表达式"
        echo "  - 自动重启机制"
        echo "  - 日志记录"
        exit 1
        ;;
esac
