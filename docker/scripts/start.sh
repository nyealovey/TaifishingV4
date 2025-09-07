#!/bin/bash
# 泰摸鱼吧 - 统一Docker启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检测系统架构
detect_architecture() {
    local arch=$(uname -m)
    case $arch in
        x86_64)
            echo "x86_64"
            ;;
        arm64|aarch64)
            echo "arm64"
            ;;
        *)
            print_message $RED "❌ 不支持的架构: $arch"
            exit 1
            ;;
    esac
}

# 检测操作系统
detect_os() {
    local os=$(uname -s)
    case $os in
        Darwin)
            echo "macos"
            ;;
        Linux)
            echo "linux"
            ;;
        *)
            print_message $RED "❌ 不支持的操作系统: $os"
            exit 1
            ;;
    esac
}

# 检查Docker是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message $RED "❌ Docker未运行，请先启动Docker Desktop"
        exit 1
    fi
}

# 检查Docker Compose是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "❌ Docker Compose未安装，请先安装Docker Desktop"
        exit 1
    fi
}

# 创建环境变量文件
create_env_file() {
    if [ ! -f .env ]; then
        print_message $YELLOW "📝 创建环境变量文件..."
        cp docker/configs/env.example .env
        print_message $GREEN "✅ 已创建 .env 文件，请根据需要修改配置"
    fi
}

# 创建用户数据目录
create_userdata_dirs() {
    print_message $BLUE "📁 创建用户数据目录..."
    mkdir -p userdata/{logs,uploads,backups,exports}
    chmod -R 755 userdata/
}

# 停止现有容器
stop_containers() {
    print_message $YELLOW "🛑 停止现有容器..."
    docker-compose -f docker/compose/docker-compose.yml down 2>/dev/null || true
    docker-compose -f docker/compose/docker-compose.x86_64.yml down 2>/dev/null || true
}

# 清理Docker缓存
clean_docker_cache() {
    print_message $YELLOW "🧹 清理Docker缓存..."
    docker system prune -f
}

# 构建镜像
build_images() {
    local compose_file=$1
    print_message $BLUE "🔨 构建Docker镜像..."
    docker-compose -f $compose_file build --no-cache
}

# 启动服务
start_services() {
    local compose_file=$1
    print_message $GREEN "🚀 启动服务..."
    docker-compose -f $compose_file up -d
}

# 等待服务启动
wait_for_services() {
    print_message $BLUE "⏳ 等待服务启动..."
    sleep 15
}

# 检查服务状态
check_services() {
    local compose_file=$1
    print_message $BLUE "🔍 检查服务状态..."
    docker-compose -f $compose_file ps
}

# 等待健康检查
wait_for_health() {
    print_message $BLUE "🏥 等待健康检查通过..."
    local timeout=60
    local counter=0
    while [ $counter -lt $timeout ]; do
        if docker-compose -f $1 ps | grep -q "healthy"; then
            print_message $GREEN "✅ 服务健康检查通过"
            break
        fi
        echo "⏳ 等待健康检查... ($counter/$timeout)"
        sleep 2
        counter=$((counter + 2))
    done
}

# 显示日志
show_logs() {
    local compose_file=$1
    print_message $BLUE "📋 显示服务日志..."
    docker-compose -f $compose_file logs --tail=50
}

# 显示成功信息
show_success_info() {
    local arch=$1
    print_message $GREEN ""
    print_message $GREEN "✅ $arch 开发环境启动完成！"
    print_message $GREEN ""
    print_message $GREEN "🌐 应用访问地址:"
    print_message $GREEN "   - 主应用: http://localhost:8000"
    print_message $GREEN "   - 健康检查: http://localhost:8000/api/health"
    print_message $GREEN ""
    print_message $GREEN "📊 服务状态:"
    print_message $GREEN "   - PostgreSQL: localhost:5432"
    print_message $GREEN "   - Redis: localhost:6379"
    print_message $GREEN "   - Flask应用: localhost:8000"
    print_message $GREEN ""
    print_message $GREEN "🔧 数据库驱动状态:"
    print_message $GREEN "   - MySQL: ✅ PyMySQL"
    print_message $GREEN "   - PostgreSQL: ✅ psycopg2"
    if [ "$arch" = "x86_64" ]; then
        print_message $GREEN "   - SQL Server: ✅ pymssql (x86_64)"
        print_message $GREEN "   - Oracle: ✅ cx_Oracle (x86_64)"
        print_message $GREEN "   - ODBC: ✅ pyodbc (x86_64)"
    else
        print_message $YELLOW "   - SQL Server: ⚠️ 部分支持"
        print_message $YELLOW "   - Oracle: ⚠️ 需要额外配置"
        print_message $YELLOW "   - ODBC: ⚠️ 需要额外配置"
    fi
    print_message $GREEN ""
    print_message $GREEN "📝 常用命令:"
    print_message $GREEN "   - 查看日志: docker-compose -f $2 logs -f"
    print_message $GREEN "   - 停止服务: docker-compose -f $2 down"
    print_message $GREEN "   - 重启服务: docker-compose -f $2 restart"
    print_message $GREEN "   - 进入容器: docker-compose -f $2 exec flask bash"
    print_message $GREEN ""
    print_message $GREEN "🔧 下一步操作:"
    print_message $GREEN "   1. 运行数据初始化脚本: docker-compose -f $2 exec flask python scripts/init_data.py --init-all"
    print_message $GREEN "   2. 验证数据: docker-compose -f $2 exec flask python scripts/init_data.py --validate-all"
    print_message $GREEN "   3. 访问应用: http://localhost:8000"
}

# 主函数
main() {
    print_message $BLUE "🍎 启动泰摸鱼吧开发环境..."
    
    # 检测系统信息
    local arch=$(detect_architecture)
    local os=$(detect_os)
    
    print_message $BLUE "📋 检测到系统: $os ($arch)"
    
    # 检查环境
    check_docker
    check_docker_compose
    
    # 准备环境
    create_env_file
    create_userdata_dirs
    stop_containers
    clean_docker_cache
    
    # 选择Docker Compose文件
    local compose_file
    if [ "$arch" = "x86_64" ] || [ "$1" = "--x86_64" ]; then
        compose_file="docker/compose/docker-compose.x86_64.yml"
        arch="x86_64"
    else
        compose_file="docker/compose/docker-compose.yml"
        arch="arm64"
    fi
    
    # 构建和启动
    build_images $compose_file
    start_services $compose_file
    wait_for_services
    check_services $compose_file
    wait_for_health $compose_file
    show_logs $compose_file
    show_success_info $arch $compose_file
}

# 处理命令行参数
case "${1:-}" in
    --x86_64)
        main --x86_64
        ;;
    --arm64)
        main
        ;;
    --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --x86_64    使用x86_64架构 (推荐)"
        echo "  --arm64     使用ARM64架构"
        echo "  --help, -h  显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  $0           # 自动检测架构"
        echo "  $0 --x86_64  # 强制使用x86_64"
        echo "  $0 --arm64   # 强制使用ARM64"
        ;;
    *)
        main
        ;;
esac
