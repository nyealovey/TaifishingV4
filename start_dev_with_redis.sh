#!/bin/bash

# 泰摸鱼吧 - 完整本地开发环境启动脚本（包含Redis）

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

# 主函数
main() {
    print_title "泰摸鱼吧 - 完整本地开发环境"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_message $RED "❌ Python3未安装"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        print_message $BLUE "📦 创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    print_message $BLUE "🔄 激活虚拟环境..."
    source venv/bin/activate
    
    # 安装依赖
    print_message $BLUE "📦 安装依赖..."
    pip install --upgrade pip
    pip install -r requirements-local.txt
    
    # 创建用户数据目录
    print_message $BLUE "📁 创建用户数据目录..."
    mkdir -p userdata/{backups,logs,exports,uploads,redis}
    
    # 启动Redis
    print_message $BLUE "🔴 启动Redis..."
    if ! ./scripts/start_redis.sh status > /dev/null 2>&1; then
        ./scripts/start_redis.sh start
    else
        print_message $GREEN "✅ Redis已在运行"
    fi
    
    # 创建环境配置
    print_message $BLUE "⚙️  创建环境配置..."
    cat > .env << EOF
FLASK_APP=app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///./userdata/taifish_dev.db
SQLALCHEMY_DATABASE_URI=sqlite:///./userdata/taifish_dev.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=dev-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600
DEVELOPMENT=True
EOF
    
    # 初始化数据库迁移
    print_message $BLUE "🔧 初始化数据库迁移..."
    if [ ! -d "migrations" ]; then
        flask db init
        print_message $GREEN "✅ 迁移环境初始化完成"
    else
        print_message $GREEN "✅ 迁移环境已存在"
    fi
    
    # 创建初始迁移（如果不存在）
    print_message $BLUE "📝 检查数据库迁移..."
    if [ ! -f "migrations/versions/$(ls migrations/versions/ 2>/dev/null | head -1)" ]; then
        flask db migrate -m "初始数据库结构"
        print_message $GREEN "✅ 初始迁移创建完成"
    fi
    
    # 升级数据库
    print_message $BLUE "⬆️  升级数据库..."
    flask db upgrade
    
    # 初始化测试数据
    print_message $BLUE "📊 初始化测试数据..."
    python scripts/init_data.py --init-all
    
    print_message $GREEN "✅ 环境准备完成！"
    print_message $BLUE "🌐 启动Flask应用..."
    print_message $BLUE "📱 访问地址: http://localhost:5001"
    print_message $BLUE "🔑 默认登录: admin/Admin123"
    print_message $BLUE "🔴 Redis状态: 运行中"
    print_message $BLUE "💾 数据库: SQLite (userdata/taifish_dev.db)"
    print_message $YELLOW "按 Ctrl+C 停止服务器"
    echo ""
    
    # 启动Flask应用
    export FLASK_PORT=5001
    python app.py
}

# 执行主函数
main "$@"
