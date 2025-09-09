#!/bin/bash
"""
泰摸鱼吧 - 服务管理脚本
用于启动、停止、重启和检查服务状态
"""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
PYTHON_PATH="$VENV_PATH/bin/python"

# PID文件路径
BEAT_PID_FILE="$PROJECT_ROOT/celerybeat.pid"
WORKER_PID_FILE="$PROJECT_ROOT/celeryworker.pid"
APP_PID_FILE="$PROJECT_ROOT/app.pid"

# 日志文件路径
LOG_DIR="$PROJECT_ROOT/logs"
BEAT_LOG="$LOG_DIR/celery_beat.log"
WORKER_LOG="$LOG_DIR/celery_worker.log"
APP_LOG="$LOG_DIR/app.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 函数：打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 函数：检查Redis是否运行
check_redis() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            return 0
        fi
    fi
    return 1
}

# 函数：检查进程是否运行
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# 函数：启动Redis
start_redis() {
    print_message $BLUE "🔍 检查Redis服务..."
    if check_redis; then
        print_message $GREEN "✅ Redis服务已运行"
        return 0
    fi
    
    print_message $YELLOW "🚀 启动Redis服务..."
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes --logfile "$LOG_DIR/redis.log"
        sleep 2
        if check_redis; then
            print_message $GREEN "✅ Redis服务启动成功"
            return 0
        fi
    fi
    
    print_message $RED "❌ Redis服务启动失败，请手动启动Redis"
    return 1
}

# 函数：启动Celery Beat
start_celery_beat() {
    if is_running "$BEAT_PID_FILE"; then
        print_message $YELLOW "⚠️  Celery Beat已在运行"
        return 0
    fi
    
    print_message $BLUE "🚀 启动Celery Beat..."
    nohup "$PYTHON_PATH" -m celery -A app.celery beat --loglevel=info --pidfile="$BEAT_PID_FILE" > "$BEAT_LOG" 2>&1 &
    sleep 3
    
    if is_running "$BEAT_PID_FILE"; then
        print_message $GREEN "✅ Celery Beat启动成功"
        return 0
    else
        print_message $RED "❌ Celery Beat启动失败"
        return 1
    fi
}

# 函数：启动Celery Worker
start_celery_worker() {
    if is_running "$WORKER_PID_FILE"; then
        print_message $YELLOW "⚠️  Celery Worker已在运行"
        return 0
    fi
    
    print_message $BLUE "🚀 启动Celery Worker..."
    nohup "$PYTHON_PATH" -m celery -A app.celery worker --loglevel=info --concurrency=4 --pidfile="$WORKER_PID_FILE" > "$WORKER_LOG" 2>&1 &
    sleep 3
    
    if is_running "$WORKER_PID_FILE"; then
        print_message $GREEN "✅ Celery Worker启动成功"
        return 0
    else
        print_message $RED "❌ Celery Worker启动失败"
        return 1
    fi
}

# 函数：启动Flask应用
start_flask_app() {
    if is_running "$APP_PID_FILE"; then
        print_message $YELLOW "⚠️  Flask应用已在运行"
        return 0
    fi
    
    print_message $BLUE "🚀 启动Flask应用..."
    nohup "$PYTHON_PATH" start_app_with_celery.py > "$APP_LOG" 2>&1 &
    echo $! > "$APP_PID_FILE"
    sleep 5
    
    if is_running "$APP_PID_FILE"; then
        print_message $GREEN "✅ Flask应用启动成功"
        print_message $GREEN "📱 访问地址: http://localhost:5001"
        return 0
    else
        print_message $RED "❌ Flask应用启动失败"
        return 1
    fi
}

# 函数：停止服务
stop_service() {
    local service_name=$1
    local pid_file=$2
    local log_file=$3
    
    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        print_message $YELLOW "🛑 停止$service_name (PID: $pid)..."
        kill "$pid"
        sleep 3
        
        if is_running "$pid_file"; then
            print_message $YELLOW "强制停止$service_name..."
            kill -9 "$pid"
            sleep 1
        fi
        
        rm -f "$pid_file"
        print_message $GREEN "✅ $service_name已停止"
    else
        print_message $YELLOW "⚠️  $service_name未运行"
    fi
}

# 函数：检查服务状态
check_status() {
    print_message $BLUE "🔍 检查服务状态..."
    echo
    
    # 检查Redis
    if check_redis; then
        print_message $GREEN "✅ Redis: 运行中"
    else
        print_message $RED "❌ Redis: 未运行"
    fi
    
    # 检查Celery Beat
    if is_running "$BEAT_PID_FILE"; then
        local beat_pid=$(cat "$BEAT_PID_FILE")
        print_message $GREEN "✅ Celery Beat: 运行中 (PID: $beat_pid)"
    else
        print_message $RED "❌ Celery Beat: 未运行"
    fi
    
    # 检查Celery Worker
    if is_running "$WORKER_PID_FILE"; then
        local worker_pid=$(cat "$WORKER_PID_FILE")
        print_message $GREEN "✅ Celery Worker: 运行中 (PID: $worker_pid)"
    else
        print_message $RED "❌ Celery Worker: 未运行"
    fi
    
    # 检查Flask应用
    if is_running "$APP_PID_FILE"; then
        local app_pid=$(cat "$APP_PID_FILE")
        print_message $GREEN "✅ Flask应用: 运行中 (PID: $app_pid)"
    else
        print_message $RED "❌ Flask应用: 未运行"
    fi
}

# 函数：显示帮助信息
show_help() {
    echo "泰摸鱼吧 - 服务管理脚本"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    检查服务状态"
    echo "  logs      查看日志"
    echo "  help      显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 start    # 启动所有服务"
    echo "  $0 status   # 检查服务状态"
    echo "  $0 logs     # 查看日志"
}

# 函数：查看日志
view_logs() {
    print_message $BLUE "📋 查看日志..."
    echo
    echo "选择要查看的日志:"
    echo "1) Flask应用日志"
    echo "2) Celery Beat日志"
    echo "3) Celery Worker日志"
    echo "4) Redis日志"
    echo "5) 所有日志"
    echo
    read -p "请选择 (1-5): " choice
    
    case $choice in
        1)
            if [ -f "$APP_LOG" ]; then
                tail -f "$APP_LOG"
            else
                print_message $RED "❌ Flask应用日志文件不存在"
            fi
            ;;
        2)
            if [ -f "$BEAT_LOG" ]; then
                tail -f "$BEAT_LOG"
            else
                print_message $RED "❌ Celery Beat日志文件不存在"
            fi
            ;;
        3)
            if [ -f "$WORKER_LOG" ]; then
                tail -f "$WORKER_LOG"
            else
                print_message $RED "❌ Celery Worker日志文件不存在"
            fi
            ;;
        4)
            if [ -f "$LOG_DIR/redis.log" ]; then
                tail -f "$LOG_DIR/redis.log"
            else
                print_message $RED "❌ Redis日志文件不存在"
            fi
            ;;
        5)
            print_message $BLUE "📋 所有日志 (最后50行):"
            echo "=== Flask应用日志 ==="
            tail -n 20 "$APP_LOG" 2>/dev/null || echo "无日志"
            echo
            echo "=== Celery Beat日志 ==="
            tail -n 20 "$BEAT_LOG" 2>/dev/null || echo "无日志"
            echo
            echo "=== Celery Worker日志 ==="
            tail -n 20 "$WORKER_LOG" 2>/dev/null || echo "无日志"
            echo
            echo "=== Redis日志 ==="
            tail -n 20 "$LOG_DIR/redis.log" 2>/dev/null || echo "无日志"
            ;;
        *)
            print_message $RED "❌ 无效选择"
            ;;
    esac
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            print_message $BLUE "🚀 启动泰摸鱼吧服务..."
            echo
            
            # 检查虚拟环境
            if [ ! -f "$PYTHON_PATH" ]; then
                print_message $RED "❌ 虚拟环境未找到: $VENV_PATH"
                print_message $YELLOW "请先创建虚拟环境: python -m venv venv"
                exit 1
            fi
            
            # 启动Redis
            if ! start_redis; then
                exit 1
            fi
            
            # 启动Celery Beat
            if ! start_celery_beat; then
                exit 1
            fi
            
            # 启动Celery Worker
            if ! start_celery_worker; then
                exit 1
            fi
            
            # 启动Flask应用
            if ! start_flask_app; then
                exit 1
            fi
            
            print_message $GREEN "🎉 所有服务启动成功！"
            print_message $GREEN "📱 访问地址: http://localhost:5001"
            ;;
            
        stop)
            print_message $YELLOW "🛑 停止泰摸鱼吧服务..."
            echo
            
            stop_service "Flask应用" "$APP_PID_FILE" "$APP_LOG"
            stop_service "Celery Worker" "$WORKER_PID_FILE" "$WORKER_LOG"
            stop_service "Celery Beat" "$BEAT_PID_FILE" "$BEAT_LOG"
            
            print_message $GREEN "✅ 所有服务已停止"
            ;;
            
        restart)
            print_message $YELLOW "🔄 重启泰摸鱼吧服务..."
            $0 stop
            sleep 2
            $0 start
            ;;
            
        status)
            check_status
            ;;
            
        logs)
            view_logs
            ;;
            
        help|--help|-h)
            show_help
            ;;
            
        *)
            print_message $RED "❌ 未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
