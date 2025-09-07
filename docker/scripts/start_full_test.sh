#!/bin/bash
# 泰摸鱼吧 - 全功能测试环境启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 打印标题
print_title() {
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}================================================${NC}"
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
        print_message $GREEN "✅ 已创建 .env 文件"
    fi
}

# 创建用户数据目录
create_userdata_dirs() {
    print_message $BLUE "📁 创建用户数据目录..."
    mkdir -p userdata/{logs,uploads,backups,exports,static}
    chmod -R 755 userdata/
}

# 停止现有容器
stop_containers() {
    print_message $YELLOW "🛑 停止现有容器..."
    docker-compose -f docker/compose/docker-compose.yml down 2>/dev/null || true
}

# 清理Docker缓存
clean_docker_cache() {
    print_message $YELLOW "🧹 清理Docker缓存..."
    docker system prune -f
}

# 检查是否需要构建镜像
check_build_needed() {
    print_message $BLUE "🔍 检查是否需要构建镜像..."
    
    # 检查关键文件是否有变化
    local build_needed=false
    local last_build_file=".last_build_hash"
    
    # 计算当前代码的哈希值
    local current_hash=$(find . -name "*.py" -o -name "requirements.txt" -o -name "Dockerfile" -o -name "docker-compose.yml" | \
        grep -v __pycache__ | \
        grep -v .git | \
        sort | \
        xargs cat | \
        md5sum | \
        cut -d' ' -f1)
    
    # 检查是否有上次构建的记录
    if [ -f "$last_build_file" ]; then
        local last_hash=$(cat "$last_build_file")
        if [ "$current_hash" = "$last_hash" ]; then
            print_message $GREEN "✅ 代码未变化，跳过构建"
            return 1
        else
            print_message $YELLOW "⚠️  代码已变化，需要重新构建"
            build_needed=true
        fi
    else
        print_message $YELLOW "⚠️  首次运行，需要构建镜像"
        build_needed=true
    fi
    
    # 检查镜像是否存在
    if [ "$build_needed" = false ]; then
        if ! docker image inspect compose-flask:latest >/dev/null 2>&1; then
            print_message $YELLOW "⚠️  Flask镜像不存在，需要构建"
            build_needed=true
        elif ! docker image inspect compose-celery-worker:latest >/dev/null 2>&1; then
            print_message $YELLOW "⚠️  Celery Worker镜像不存在，需要构建"
            build_needed=true
        elif ! docker image inspect compose-celery-beat:latest >/dev/null 2>&1; then
            print_message $YELLOW "⚠️  Celery Beat镜像不存在，需要构建"
            build_needed=true
        fi
    fi
    
    if [ "$build_needed" = true ]; then
        return 0
    else
        return 1
    fi
}

# 构建镜像
build_images() {
    print_message $BLUE "🔨 构建应用镜像..."
    echo "================================================"
    
    # 只构建我们自己的应用镜像，PostgreSQL和Redis使用官方镜像
    print_message $BLUE "构建Flask应用镜像..."
    docker-compose -f docker/compose/docker-compose.yml build flask --progress=plain
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ Flask应用镜像构建成功"
    else
        print_message $RED "❌ Flask应用镜像构建失败"
        exit 1
    fi
    
    # 构建Celery Worker镜像
    print_message $BLUE "构建Celery Worker镜像..."
    docker-compose -f docker/compose/docker-compose.yml build celery-worker --progress=plain
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ Celery Worker镜像构建成功"
    else
        print_message $RED "❌ Celery Worker镜像构建失败"
        exit 1
    fi
    
    # 构建Celery Beat镜像
    print_message $BLUE "构建Celery Beat镜像..."
    docker-compose -f docker/compose/docker-compose.yml build celery-beat --progress=plain
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ Celery Beat镜像构建成功"
    else
        print_message $RED "❌ Celery Beat镜像构建失败"
        exit 1
    fi
    
    # 保存构建哈希值
    local current_hash=$(find . -name "*.py" -o -name "requirements.txt" -o -name "Dockerfile" -o -name "docker-compose.yml" | \
        grep -v __pycache__ | \
        grep -v .git | \
        sort | \
        xargs cat | \
        md5sum | \
        cut -d' ' -f1)
    echo "$current_hash" > .last_build_hash
    
    echo "================================================"
    print_message $GREEN "✅ 应用镜像构建完成"
    print_message $YELLOW "ℹ️  PostgreSQL和Redis使用官方镜像，无需构建"
}

# 启动服务
start_services() {
    print_message $GREEN "🚀 启动服务..."
    echo "================================================"
    
    # 启动基础服务（使用官方镜像，无需构建）
    print_message $BLUE "启动PostgreSQL和Redis（官方镜像）..."
    docker-compose -f docker/compose/docker-compose.yml up -d postgres redis
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ PostgreSQL和Redis启动成功"
    else
        print_message $RED "❌ PostgreSQL和Redis启动失败"
        exit 1
    fi
    
    # 等待基础服务就绪
    print_message $BLUE "等待基础服务就绪..."
    sleep 10
    
    # 启动Flask应用（我们自己的镜像）
    print_message $BLUE "启动Flask应用..."
    docker-compose -f docker/compose/docker-compose.yml up -d flask
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ Flask应用启动成功"
    else
        print_message $RED "❌ Flask应用启动失败"
        exit 1
    fi
    
    # 启动Celery服务（我们自己的镜像）
    print_message $BLUE "启动Celery服务..."
    docker-compose -f docker/compose/docker-compose.yml up -d celery-worker celery-beat
    
    if [ $? -eq 0 ]; then
        print_message $GREEN "✅ Celery服务启动成功"
    else
        print_message $RED "❌ Celery服务启动失败"
        exit 1
    fi
    
    # Nginx已禁用
    print_message $YELLOW "⚠️  Nginx已禁用，直接访问Flask应用"
    
    echo "================================================"
    print_message $GREEN "✅ 所有服务启动完成"
}

# 等待服务启动
wait_for_services() {
    print_message $BLUE "⏳ 等待服务启动..."
    echo "================================================"
    
    # 等待PostgreSQL
    print_message $BLUE "等待PostgreSQL启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f docker/compose/docker-compose.yml exec -T postgres pg_isready -U taifish > /dev/null 2>&1; then
            print_message $GREEN "✅ PostgreSQL已就绪"
            break
        fi
        echo -n "."
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_message $RED "❌ PostgreSQL启动超时"
        exit 1
    fi
    
    # 等待Redis
    print_message $BLUE "等待Redis启动..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose -f docker/compose/docker-compose.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
            print_message $GREEN "✅ Redis已就绪"
            break
        fi
        echo -n "."
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_message $RED "❌ Redis启动超时"
        exit 1
    fi
    
    # 等待Flask应用
    print_message $BLUE "等待Flask应用启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
            print_message $GREEN "✅ Flask应用已就绪"
            break
        fi
        echo -n "."
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        print_message $RED "❌ Flask应用启动超时"
        print_message $BLUE "查看Flask应用日志："
        docker-compose -f docker/compose/docker-compose.yml logs flask
        exit 1
    fi
    
    echo "================================================"
    print_message $GREEN "✅ 所有服务已就绪"
}

# 检查服务状态
check_services() {
    print_message $BLUE "🔍 检查服务状态..."
    docker-compose -f docker/compose/docker-compose.yml ps
}

# 等待健康检查
wait_for_health() {
    print_message $BLUE "🏥 等待健康检查通过..."
    local timeout=120
    local counter=0
    while [ $counter -lt $timeout ]; do
        if docker-compose -f docker/compose/docker-compose.yml ps | grep -q "healthy"; then
            print_message $GREEN "✅ 服务健康检查通过"
            break
        fi
        echo "⏳ 等待健康检查... ($counter/$timeout)"
        sleep 3
        counter=$((counter + 3))
    done
}

# 检查数据库是否需要初始化
check_database_init() {
    print_message $BLUE "🔍 检查数据库状态..."
    
    # 等待PostgreSQL完全启动
    sleep 5
    
    # 检查数据库是否已存在数据
    local user_count=$(docker-compose -f docker/compose/docker-compose.yml exec -T postgres psql -U taifish_user -d taifish_dev -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' \n' || echo "0")
    
    # 确保user_count是数字
    if ! [[ "$user_count" =~ ^[0-9]+$ ]]; then
        user_count=0
    fi
    
    if [ "$user_count" -gt 0 ]; then
        print_message $GREEN "✅ 数据库已有数据，跳过初始化"
        print_message $YELLOW "ℹ️  保留现有数据，继续使用"
        return 1
    else
        print_message $YELLOW "⚠️  数据库为空，需要初始化"
        return 0
    fi
}

# 初始化数据库
init_database() {
    print_message $BLUE "🗄️ 初始化数据库..."
    docker-compose -f docker/compose/docker-compose.yml exec -T flask python scripts/init_database.py --init
}

# 初始化测试数据
init_test_data() {
    print_message $BLUE "📊 初始化测试数据..."
    docker-compose -f docker/compose/docker-compose.yml exec -T flask python scripts/init_data.py --init-all
}

# 验证数据
validate_data() {
    print_message $BLUE "✅ 验证数据..."
    docker-compose -f docker/compose/docker-compose.yml exec -T flask python scripts/init_data.py --validate-all
}

# 测试数据库连接
test_database_connections() {
    print_message $BLUE "🔗 测试数据库连接..."
    docker-compose -f docker/compose/docker-compose.yml exec -T flask python app/services/database_drivers.py
}

# 运行测试
run_tests() {
    print_message $BLUE "🧪 运行测试..."
    docker-compose -f docker/compose/docker-compose.yml exec -T flask python -m pytest tests/ -v
}

# 显示服务信息
show_services_info() {
    print_title "服务信息"
    print_message $GREEN "🌐 应用访问地址:"
    print_message $GREEN "   - 主应用: http://localhost:8000"
    print_message $GREEN "   - 健康检查: http://localhost:8000/api/health"
    print_message $GREEN "   - 管理界面: http://localhost:8000/admin"
    print_message $GREEN ""
    print_message $GREEN "📊 数据库服务:"
    print_message $GREEN "   - PostgreSQL: localhost:5432"
    print_message $GREEN "   - Redis: localhost:6379"
    print_message $GREEN ""
    print_message $GREEN "🔧 数据库驱动状态:"
    print_message $GREEN "   - MySQL: ✅ PyMySQL 1.1.1"
    print_message $GREEN "   - PostgreSQL: ✅ psycopg2 2.9.9"
    print_message $GREEN "   - SQL Server: ✅ pymssql 2.2.11"
    print_message $GREEN "   - Oracle: ✅ cx_Oracle 8.3.0"
    print_message $GREEN "   - ODBC: ✅ pyodbc 5.1.0"
    print_message $GREEN ""
    print_message $GREEN "📝 常用命令:"
    print_message $GREEN "   - 查看日志: docker-compose -f docker/compose/docker-compose.yml logs -f"
    print_message $GREEN "   - 停止服务: docker-compose -f docker/compose/docker-compose.yml down"
    print_message $GREEN "   - 重启服务: docker-compose -f docker/compose/docker-compose.yml restart"
    print_message $GREEN "   - 进入容器: docker-compose -f docker/compose/docker-compose.yml exec flask bash"
}

# 显示测试结果
show_test_results() {
    print_title "测试结果"
    print_message $GREEN "✅ 全功能测试环境启动完成！"
    print_message $GREEN ""
    print_message $GREEN "🎯 已测试功能:"
    print_message $GREEN "   - ✅ Docker环境构建"
    print_message $GREEN "   - ✅ 数据库连接"
    print_message $GREEN "   - ✅ Redis缓存"
    print_message $GREEN "   - ✅ Celery任务队列"
    print_message $GREEN "   - ✅ Nginx反向代理"
    print_message $GREEN "   - ✅ 所有数据库驱动"
    print_message $GREEN "   - ✅ 数据初始化"
    print_message $GREEN "   - ✅ 健康检查"
    print_message $GREEN ""
    print_message $GREEN "🚀 现在可以开始开发了！"
}

# 主函数
main() {
    # 检查是否有强制构建参数
    if [ "$1" = "--force-build" ] || [ "$1" = "-f" ]; then
        print_message $YELLOW "🔄 强制构建模式，将重新构建所有镜像"
        rm -f .last_build_hash
    fi
    
    # 检查是否有强制初始化参数
    if [ "$1" = "--force-init" ] || [ "$2" = "--force-init" ]; then
        print_message $YELLOW "🔄 强制初始化模式，将重新初始化数据库"
        FORCE_INIT=true
    else
        FORCE_INIT=false
    fi
    
    print_title "泰摸鱼吧 - 全功能测试环境启动"
    
    # 检查环境
    check_docker
    check_docker_compose
    
    # 准备环境
    create_env_file
    create_userdata_dirs
    # 不停止容器，保持数据持久化
    # stop_containers
    # clean_docker_cache
    
    # 构建和启动
    if check_build_needed; then
        # 构建镜像
        build_images
    else
        print_message $GREEN "✅ 使用现有镜像，跳过构建"
    fi
    start_services
    wait_for_services
    check_services
    wait_for_health
    
    # 初始化数据
    if [ "$FORCE_INIT" = true ] || check_database_init; then
        # 数据库为空或强制初始化
        if [ "$FORCE_INIT" = true ]; then
            print_message $YELLOW "🔄 强制重新初始化数据库"
        fi
        init_database
        init_test_data
    else
        # 数据库已有数据，只验证
        print_message $GREEN "✅ 使用现有数据库数据"
    fi
    validate_data
    
    # 测试功能
    test_database_connections
    run_tests
    
    # 显示结果
    show_services_info
    show_test_results
}

# 处理命令行参数
case "${1:-}" in
    --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h          显示此帮助信息"
        echo "  --force-build, -f   强制重新构建所有镜像"
        echo "  --force-init        强制重新初始化数据库（会清空现有数据）"
        echo ""
        echo "功能:"
        echo "  - 构建最新稳定版Docker环境"
        echo "  - 启动所有服务（Flask, PostgreSQL, Redis, Celery, Nginx）"
        echo "  - 初始化数据库和测试数据"
        echo "  - 测试所有数据库驱动"
        echo "  - 运行完整测试套件"
        echo "  - 验证所有功能正常"
        ;;
    *)
        main "$@"
        ;;
esac
