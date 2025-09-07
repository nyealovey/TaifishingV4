#!/bin/bash

# 泰摸鱼吧 - Redis管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_title() {
    local title=$1
    echo ""
    echo "================================================"
    echo "  $title"
    echo "================================================"
}

# 启动Redis
start_redis() {
    print_title "启动Redis服务器"
    
    if pgrep -f "redis-server" > /dev/null; then
        print_message $YELLOW "⚠️  Redis已在运行"
        return 0
    fi
    
    # 创建必要目录
    mkdir -p userdata/{redis,logs}
    
    # 启动Redis
    print_message $BLUE "🚀 启动Redis服务器..."
    redis-server --daemonize yes --dir $(pwd)/userdata/redis --logfile $(pwd)/userdata/logs/redis.log --port 6379
    
    # 等待启动
    sleep 2
    
    # 检查状态
    if pgrep -f "redis-server" > /dev/null; then
        print_message $GREEN "✅ Redis启动成功"
        print_message $BLUE "📊 端口: 6379"
        print_message $BLUE "📁 数据目录: userdata/redis"
        print_message $BLUE "📝 日志文件: userdata/logs/redis.log"
    else
        print_message $RED "❌ Redis启动失败"
        exit 1
    fi
}

# 停止Redis
stop_redis() {
    print_title "停止Redis服务器"
    
    if pgrep -f "redis-server" > /dev/null; then
        print_message $BLUE "🛑 停止Redis服务器..."
        pkill -x redis-server
        sleep 1
        
        if pgrep -f "redis-server" > /dev/null; then
            print_message $RED "❌ Redis停止失败"
        else
            print_message $GREEN "✅ Redis已停止"
        fi
    else
        print_message $YELLOW "⚠️  Redis未运行"
    fi
}

# 重启Redis
restart_redis() {
    print_title "重启Redis服务器"
    stop_redis
    sleep 1
    start_redis
}

# 检查Redis状态
check_status() {
    print_title "Redis状态检查"
    
    if pgrep -f "redis-server" > /dev/null; then
        print_message $GREEN "✅ Redis正在运行"
        
        # 测试连接
        if redis-cli ping > /dev/null 2>&1; then
            print_message $GREEN "✅ Redis连接正常"
            
            # 显示信息
            print_message $BLUE "📊 Redis信息:"
            redis-cli info server | grep -E "(redis_version|uptime_in_seconds|connected_clients)"
        else
            print_message $RED "❌ Redis连接失败"
        fi
    else
        print_message $RED "❌ Redis未运行"
    fi
}

# 查看Redis日志
view_logs() {
    print_title "Redis日志"
    
    if [ -f "userdata/logs/redis.log" ]; then
        print_message $BLUE "📝 最近日志:"
        tail -20 userdata/logs/redis.log
    else
        print_message $YELLOW "⚠️  日志文件不存在"
    fi
}

# 清理Redis数据
clear_data() {
    print_title "清理Redis数据"
    
    print_message $YELLOW "⚠️  这将删除所有Redis数据！"
    read -p "确认继续？(y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        if pgrep -f "redis-server" > /dev/null; then
            print_message $BLUE "🛑 停止Redis..."
            pkill -x redis-server
            sleep 1
        fi
        
        print_message $BLUE "🗑️  清理数据..."
        rm -rf userdata/redis/*
        
        print_message $GREEN "✅ 数据清理完成"
        print_message $BLUE "🚀 重新启动Redis..."
        start_redis
    else
        print_message $YELLOW "❌ 操作已取消"
    fi
}

# 显示帮助
show_help() {
    echo "泰摸鱼吧 - Redis管理工具"
    echo ""
    echo "用法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  start     启动Redis服务器"
    echo "  stop      停止Redis服务器"
    echo "  restart   重启Redis服务器"
    echo "  status    检查Redis状态"
    echo "  logs      查看Redis日志"
    echo "  clear     清理Redis数据"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
}

# 主函数
main() {
    case "${1:-}" in
        start)
            start_redis
            ;;
        stop)
            stop_redis
            ;;
        restart)
            restart_redis
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs
            ;;
        clear)
            clear_data
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_message $RED "❌ 未知命令: ${1:-}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
