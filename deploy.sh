#!/bin/bash

# 泰摸鱼吧生产环境部署脚本
# 适用于Debian/Ubuntu系统
# 作者: 泰摸鱼吧团队
# 版本: 1.0.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用root用户运行此脚本！"
        exit 1
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if ! command -v apt-get &> /dev/null; then
        log_error "此脚本仅支持Debian/Ubuntu系统"
        exit 1
    fi
    
    # 检查内存
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ $MEMORY -lt 2048 ]; then
        log_warning "系统内存少于2GB，可能影响性能"
    fi
    
    # 检查磁盘空间
    DISK_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $DISK_SPACE -lt 10 ]; then
        log_error "磁盘空间不足10GB，请清理空间后重试"
        exit 1
    fi
    
    log_success "系统检查通过"
}

# 安装Docker和Docker Compose
install_docker() {
    log_info "安装Docker和Docker Compose..."
    
    # 更新包列表
    sudo apt-get update
    
    # 安装必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        software-properties-common
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 更新包列表
    sudo apt-get update
    
    # 安装Docker
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 安装Docker Compose V2
    sudo apt-get install -y docker-compose-plugin
    
    log_success "Docker安装完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    # 创建项目目录
    sudo mkdir -p /opt/taifish
    sudo mkdir -p /opt/taifish/logs
    sudo mkdir -p /opt/taifish/backups
    sudo mkdir -p /opt/taifish/ssl
    sudo mkdir -p /opt/taifish/data/postgres
    sudo mkdir -p /opt/taifish/data/redis
    sudo mkdir -p /opt/taifish/data/app
    
    # 设置权限
    sudo chown -R $USER:$USER /opt/taifish
    
    log_success "目录创建完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 检查ufw是否安装
    if ! command -v ufw &> /dev/null; then
        sudo apt-get install -y ufw
    fi
    
    # 配置防火墙规则
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    
    log_success "防火墙配置完成"
}

# 创建环境配置文件
create_env_file() {
    log_info "创建环境配置文件..."
    
    # 生成随机密码
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    SECRET_KEY=$(openssl rand -base64 64)
    
    # 创建.env文件
    cat > /opt/taifish/.env << EOF
# 泰摸鱼吧生产环境配置
# 自动生成于 $(date)

# 应用配置
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=${SECRET_KEY}
APP_NAME=泰摸鱼吧
APP_VERSION=1.0.0
APP_DESCRIPTION=数据同步管理平台

# 数据库配置
DATABASE_URL=postgresql://taifish_user:${POSTGRES_PASSWORD}@postgres:5432/taifish_prod
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Redis配置
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=${REDIS_PASSWORD}

# Celery配置
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/taifish.log

# 安全配置
PERMANENT_SESSION_LIFETIME=3600
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
WTF_CSRF_ENABLED=True

# 时区配置
TZ=Asia/Shanghai
TIMEZONE=Asia/Shanghai

# 环境标识
ENVIRONMENT=production
DEPLOYMENT_DATE=$(date +%Y-%m-%d)
VERSION=1.0.0
EOF
    
    # 设置权限
    chmod 600 /opt/taifish/.env
    
    log_success "环境配置文件创建完成"
    log_warning "请妥善保存生成的密码！"
    echo "PostgreSQL密码: ${POSTGRES_PASSWORD}"
    echo "Redis密码: ${REDIS_PASSWORD}"
    echo "密钥: ${SECRET_KEY}"
}

# 复制项目文件
copy_project_files() {
    log_info "复制项目文件..."
    
    # 复制项目文件到部署目录
    cp -r . /opt/taifish/
    
    # 复制环境配置
    cp /opt/taifish/.env /opt/taifish/.env.production
    
    # 设置权限
    chmod +x /opt/taifish/deploy.sh
    chmod +x /opt/taifish/start.sh
    chmod +x /opt/taifish/stop.sh
    chmod +x /opt/taifish/restart.sh
    
    log_success "项目文件复制完成"
}

# 构建和启动服务
start_services() {
    log_info "构建和启动服务..."
    
    cd /opt/taifish
    
    # 构建镜像
    docker compose build --no-cache
    
    # 启动服务
    docker compose up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    docker compose ps
    
    log_success "服务启动完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    cd /opt/taifish
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 20
    
    # 运行数据库迁移
    docker compose exec app python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库表创建完成')
"
    
    # 初始化权限配置
    docker compose exec app python scripts/init_permission_config.py
    
    # 初始化分类规则
    docker compose exec app python scripts/init_default_classification_rules.py
    
    # 创建管理员用户
    docker compose exec app python scripts/create_admin_user.py
    
    log_success "数据库初始化完成"
}

# 配置SSL证书 (可选)
configure_ssl() {
    log_info "配置SSL证书..."
    
    # 创建自签名证书 (仅用于测试)
    if [ ! -f /opt/taifish/ssl/cert.pem ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /opt/taifish/ssl/key.pem \
            -out /opt/taifish/ssl/cert.pem \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=Taifish/OU=IT/CN=localhost"
    fi
    
    log_success "SSL证书配置完成"
    log_warning "生产环境请使用正式的SSL证书！"
}

# 创建管理脚本
create_management_scripts() {
    log_info "创建管理脚本..."
    
    # 启动脚本
    cat > /opt/taifish/start.sh << 'EOF'
#!/bin/bash
cd /opt/taifish
docker compose up -d
echo "泰摸鱼吧服务已启动"
EOF
    
    # 停止脚本
    cat > /opt/taifish/stop.sh << 'EOF'
#!/bin/bash
cd /opt/taifish
docker compose down
echo "泰摸鱼吧服务已停止"
EOF
    
    # 重启脚本
    cat > /opt/taifish/restart.sh << 'EOF'
#!/bin/bash
cd /opt/taifish
docker compose down
docker compose up -d
echo "泰摸鱼吧服务已重启"
EOF
    
    # 日志查看脚本
    cat > /opt/taifish/logs.sh << 'EOF'
#!/bin/bash
cd /opt/taifish
docker compose logs -f
EOF
    
    # 备份脚本
    cat > /opt/taifish/backup.sh << 'EOF'
#!/bin/bash
cd /opt/taifish
BACKUP_FILE="/opt/taifish/backups/taifish_backup_$(date +%Y%m%d_%H%M%S).sql"
docker compose exec postgres pg_dump -U taifish_user taifish_prod > $BACKUP_FILE
echo "数据库备份完成: $BACKUP_FILE"
EOF
    
    # 设置权限
    chmod +x /opt/taifish/*.sh
    
    log_success "管理脚本创建完成"
}

# 创建系统服务
create_systemd_service() {
    log_info "创建系统服务..."
    
    # 创建systemd服务文件
    sudo tee /etc/systemd/system/taifish.service > /dev/null << EOF
[Unit]
Description=Taifish Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/taifish
ExecStart=/opt/taifish/start.sh
ExecStop=/opt/taifish/stop.sh
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable taifish.service
    
    log_success "系统服务创建完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "部署完成！"
    echo ""
    echo "=========================================="
    echo "🐟 泰摸鱼吧生产环境部署信息"
    echo "=========================================="
    echo "📍 部署路径: /opt/taifish"
    echo "🌐 访问地址: http://$(hostname -I | awk '{print $1}')"
    echo "🔑 默认登录: admin / Admin123"
    echo "📊 管理界面: http://$(hostname -I | awk '{print $1}')/admin"
    echo ""
    echo "📋 管理命令:"
    echo "  启动服务: /opt/taifish/start.sh"
    echo "  停止服务: /opt/taifish/stop.sh"
    echo "  重启服务: /opt/taifish/restart.sh"
    echo "  查看日志: /opt/taifish/logs.sh"
    echo "  备份数据: /opt/taifish/backup.sh"
    echo ""
    echo "🔧 系统服务:"
    echo "  启动: sudo systemctl start taifish"
    echo "  停止: sudo systemctl stop taifish"
    echo "  状态: sudo systemctl status taifish"
    echo ""
    echo "⚠️  重要提醒:"
    echo "  1. 请修改默认密码"
    echo "  2. 配置正式SSL证书"
    echo "  3. 定期备份数据"
    echo "  4. 监控系统资源"
    echo "=========================================="
}

# 主函数
main() {
    echo "🐟 泰摸鱼吧生产环境部署脚本"
    echo "=========================================="
    
    # 检查系统要求
    check_root
    check_system
    
    # 安装依赖
    install_docker
    
    # 创建目录结构
    create_directories
    
    # 配置系统
    configure_firewall
    create_env_file
    copy_project_files
    
    # 启动服务
    start_services
    init_database
    
    # 配置SSL
    configure_ssl
    
    # 创建管理工具
    create_management_scripts
    create_systemd_service
    
    # 显示部署信息
    show_deployment_info
}

# 运行主函数
main "$@"
