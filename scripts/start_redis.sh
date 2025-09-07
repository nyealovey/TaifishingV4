#!/bin/bash

# 泰摸鱼吧 - Redis启动脚本

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

# 检查Redis是否已安装
check_redis_installed() {
    if command -v redis-server &> /dev/null; then
        print_message $GREEN "✅ Redis已安装"
        return 0
    else
        print_message $RED "❌ Redis未安装"
        return 1
    fi
}

# 安装Redis (macOS)
install_redis_macos() {
    print_message $BLUE "📦 安装Redis..."
    
    if command -v brew &> /dev/null; then
        print_message $BLUE "使用Homebrew安装Redis..."
        brew install redis
        print_message $GREEN "✅ Redis安装成功"
    else
        print_message $RED "❌ 未找到Homebrew，请手动安装Redis"
        print_message $YELLOW "请访问: https://redis.io/download"
        exit 1
    fi
}

# 启动Redis
start_redis() {
    print_title "启动Redis服务器"
    
    # 检查Redis是否已运行
    if pgrep -x "redis-server" > /dev/null; then
        print_message $YELLOW "⚠️  Redis已在运行"
        return 0
    fi
    
    # 创建Redis数据目录
    mkdir -p userdata/redis
    
    # 启动Redis
    print_message $BLUE "🚀 启动Redis服务器..."
    redis-server --daemonize yes --dir userdata/redis --logfile userdata/logs/redis.log --port 6379
    
    # 等待Redis启动
    sleep 2
    
    # 检查Redis是否启动成功
    if pgrep -x "redis-server" > /dev/null; then
        print_message $GREEN "✅ Redis启动成功"
        print_message $BLUE "📊 Redis端口: 6379"
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
    
    if pgrep -x "redis-server" > /dev/null; then
        print_message $BLUE "🛑 停止Redis服务器..."
        pkill -x redis-server
        sleep 1
        
        if pgrep -x "redis-server" > /dev/null; then
            print_message $RED "❌ Redis停止失败"
        else
            print_message $GREEN "✅ Redis已停止"
        fi
    else
        print_message $YELLOW "⚠️  Redis未运行"
    fi
}

# 检查Redis状态
check_redis_status() {
    print_title "Redis状态检查"
    
    if pgrep -x "redis-server" > /dev/null; then
        print_message $GREEN "✅ Redis正在运行"
        
        # 测试Redis连接
        if redis-cli ping > /dev/null 2>&1; then
            print_message $GREEN "✅ Redis连接正常"
        else
            print_message $RED "❌ Redis连接失败"
        fi
    else
        print_message $RED "❌ Redis未运行"
    fi
}

# 主函数
main() {
    case "${1:-}" in
        start)
            if ! check_redis_installed; then
                install_redis_macos
            fi
            start_redis
            ;;
        stop)
            stop_redis
            ;;
        restart)
            stop_redis
            sleep 1
            start_redis
            ;;
        status)
            check_redis_status
            ;;
        install)
            install_redis_macos
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|install}"
            echo ""
            echo "命令:"
            echo "  start     启动Redis服务器"
            echo "  stop      停止Redis服务器"
            echo "  restart   重启Redis服务器"
            echo "  status    检查Redis状态"
            echo "  install   安装Redis"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
