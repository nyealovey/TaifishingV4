#!/bin/bash

# 泰摸鱼吧 - 本地开发环境启动脚本

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

# 检查Python环境
check_python() {
    print_message $BLUE "🐍 检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_message $RED "❌ Python3未安装"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    print_message $GREEN "✅ Python版本: $python_version"
}

# 检查虚拟环境
check_venv() {
    print_message $BLUE "🔍 检查虚拟环境..."
    
    if [ ! -d "venv" ]; then
        print_message $YELLOW "⚠️  虚拟环境不存在，正在创建..."
        python3 -m venv venv
        print_message $GREEN "✅ 虚拟环境创建成功"
    else
        print_message $GREEN "✅ 虚拟环境已存在"
    fi
}

# 激活虚拟环境
activate_venv() {
    print_message $BLUE "🔄 激活虚拟环境..."
    source venv/bin/activate
    print_message $GREEN "✅ 虚拟环境已激活"
}

# 安装依赖
install_dependencies() {
    print_message $BLUE "📦 安装Python依赖..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    print_message $GREEN "✅ 依赖安装完成"
}

# 创建用户数据目录
create_userdata_dirs() {
    print_message $BLUE "📁 创建用户数据目录..."
    
    mkdir -p userdata/{backups,logs,exports,uploads}
    mkdir -p userdata/logs
    
    print_message $GREEN "✅ 用户数据目录创建完成"
}

# 创建本地环境配置
create_local_config() {
    print_message $BLUE "⚙️  创建本地开发配置..."
    
    cat > .env << EOF
# 泰摸鱼吧 - 本地开发环境配置

# Flask配置
FLASK_APP=app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# 数据库配置 (SQLite)
DATABASE_URL=sqlite:///userdata/taifish_dev.db
SQLALCHEMY_DATABASE_URI=sqlite:///userdata/taifish_dev.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Redis配置 (本地Redis)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 缓存配置
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# JWT配置
JWT_SECRET_KEY=dev-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# 日志配置
LOG_LEVEL=DEBUG
LOG_FILE=userdata/logs/app.log

# 文件上传配置
UPLOAD_FOLDER=userdata/uploads
MAX_CONTENT_LENGTH=16777216

# 备份配置
BACKUP_FOLDER=userdata/backups

# 导出配置
EXPORT_FOLDER=userdata/exports

# 开发模式
DEVELOPMENT=True
EOF

    print_message $GREEN "✅ 本地开发配置创建完成"
}

# 初始化数据库
init_database() {
    print_message $BLUE "🗄️ 初始化SQLite数据库..."
    
    # 检查数据库是否存在
    if [ -f "userdata/taifish_dev.db" ]; then
        print_message $GREEN "✅ 数据库已存在，跳过初始化"
        return
    fi
    
    # 初始化数据库
    python scripts/init_database.py --init
    
    print_message $GREEN "✅ 数据库初始化完成"
}

# 初始化测试数据
init_test_data() {
    print_message $BLUE "📊 初始化测试数据..."
    
    python scripts/init_data.py --init-all
    
    print_message $GREEN "✅ 测试数据初始化完成"
}

# 检查Redis
check_redis() {
    print_message $BLUE "🔍 检查Redis服务..."
    
    if ! command -v redis-server &> /dev/null; then
        print_message $YELLOW "⚠️  Redis未安装，请先安装Redis"
        print_message $YELLOW "   macOS: brew install redis"
        print_message $YELLOW "   Ubuntu: sudo apt-get install redis-server"
        return 1
    fi
    
    # 检查Redis是否运行
    if ! redis-cli ping &> /dev/null; then
        print_message $YELLOW "⚠️  Redis未运行，正在启动..."
        redis-server --daemonize yes
        sleep 2
    fi
    
    print_message $GREEN "✅ Redis服务正常"
    return 0
}

# 启动Celery Worker
start_celery_worker() {
    print_message $BLUE "🚀 启动Celery Worker..."
    
    # 在后台启动Celery Worker
    celery -A app.celery worker --loglevel=info --detach
    
    print_message $GREEN "✅ Celery Worker已启动"
}

# 启动Celery Beat
start_celery_beat() {
    print_message $BLUE "⏰ 启动Celery Beat..."
    
    # 在后台启动Celery Beat
    celery -A app.celery beat --loglevel=info --detach
    
    print_message $GREEN "✅ Celery Beat已启动"
}

# 启动Flask应用
start_flask_app() {
    print_message $BLUE "🌐 启动Flask应用..."
    
    print_message $GREEN "✅ Flask应用启动完成"
    print_message $YELLOW "📱 访问地址: http://localhost:5000"
    print_message $YELLOW "🔑 默认登录: admin/admin123"
    print_message $YELLOW "📊 管理界面: http://localhost:5000/admin"
    
    # 启动Flask应用
    python app.py
}

# 清理函数
cleanup() {
    print_message $YELLOW "🧹 清理后台进程..."
    
    # 停止Celery进程
    pkill -f "celery.*worker" || true
    pkill -f "celery.*beat" || true
    
    print_message $GREEN "✅ 清理完成"
}

# 设置信号处理
trap cleanup EXIT INT TERM

# 主函数
main() {
    print_title "泰摸鱼吧 - 本地开发环境启动"
    
    # 检查环境
    check_python
    check_venv
    activate_venv
    
    # 准备环境
    create_userdata_dirs
    create_local_config
    install_dependencies
    
    # 初始化数据
    init_database
    init_test_data
    
    # 检查Redis
    if ! check_redis; then
        print_message $YELLOW "⚠️  跳过Redis相关功能"
    else
        # 启动Celery
        start_celery_worker
        start_celery_beat
    fi
    
    # 启动Flask应用
    start_flask_app
}

# 处理命令行参数
case "${1:-}" in
    --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h      显示此帮助信息"
        echo ""
        echo "功能:"
        echo "  - 创建Python虚拟环境"
        echo "  - 安装所有依赖包"
        echo "  - 初始化SQLite数据库"
        echo "  - 启动Flask开发服务器"
        echo "  - 启动Celery Worker和Beat"
        echo ""
        echo "要求:"
        echo "  - Python 3.8+"
        echo "  - Redis (可选)"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
