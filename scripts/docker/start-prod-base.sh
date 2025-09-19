#!/bin/bash

# 服务器正式环境 - 基础环境启动脚本（x86，有代理）
# 启动：PostgreSQL + Redis + Nginx

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}📊 $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查Docker是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    log_success "Docker运行正常"
}

# 检查环境配置文件
check_env() {
    if [ ! -f ".env" ]; then
        log_warning "未找到.env文件，从env.production创建"
        cp env.production .env
        log_info "请根据需要修改.env文件中的配置，特别是代理设置"
    fi
    log_success "环境配置文件检查通过"
}

# 检查代理配置
check_proxy() {
    if [ -n "$HTTP_PROXY" ]; then
        log_info "检测到代理配置: $HTTP_PROXY"
        log_info "基础环境服务将使用代理配置"
    else
        log_warning "未设置代理，将使用直连模式"
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p userdata/{postgres,redis,nginx/{logs,ssl},logs,exports,backups,uploads}
    log_success "目录创建完成"
}

# 启动基础环境
start_base_environment() {
    log_info "启动基础环境（PostgreSQL + Redis + Nginx）..."
    
    # 停止可能存在的容器（不删除）
    docker compose -f docker-compose.prod.yml stop postgres redis nginx 2>/dev/null || true
    
    # 启动基础服务
    docker compose -f docker-compose.prod.yml up -d postgres redis nginx
    
    log_success "基础环境启动完成"
}

# 等待基础服务就绪
wait_for_base_services() {
    log_info "等待基础服务就绪..."
    
    # 等待PostgreSQL
    log_info "等待PostgreSQL启动..."
    timeout 60 bash -c 'until docker compose -f docker-compose.prod.yml exec postgres pg_isready -U whalefall_user -d whalefall_prod; do sleep 2; done'
    log_success "PostgreSQL已就绪"
    
    # 等待Redis
    log_info "等待Redis启动..."
    timeout 30 bash -c 'until docker compose -f docker-compose.prod.yml exec redis redis-cli ping; do sleep 2; done'
    log_success "Redis已就绪"
    
    # 等待Nginx
    log_info "等待Nginx启动..."
    timeout 30 bash -c 'until curl -f http://localhost > /dev/null 2>&1; do sleep 2; done'
    log_success "Nginx已就绪"
}

# 显示基础环境状态
show_base_status() {
    log_info "基础环境状态:"
    docker compose -f docker-compose.prod.yml ps postgres redis nginx
    
    echo ""
    log_info "服务信息:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo "  - Nginx: http://localhost"
    
    echo ""
    log_info "下一步:"
    echo "  运行 ./scripts/docker/start-prod-flask.sh 启动Flask应用"
}

# 主函数
main() {
    log_info "开始启动生产环境基础服务..."
    
    check_docker
    check_env
    check_proxy
    create_directories
    start_base_environment
    wait_for_base_services
    show_base_status
    
    log_success "基础环境启动完成！"
}

# 执行主函数
main "$@"
