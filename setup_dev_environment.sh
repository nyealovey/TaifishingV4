#!/bin/bash

# 泰摸鱼吧 - 开发环境一键安装脚本

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

# 检查操作系统
check_os() {
    print_title "检查操作系统"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_message $GREEN "✅ 检测到 macOS 系统"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_message $GREEN "✅ 检测到 Linux 系统"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        print_message $GREEN "✅ 检测到 Windows 系统"
    else
        print_message $RED "❌ 不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查Python
check_python() {
    print_title "检查Python环境"
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ "$PYTHON_VERSION" == "3.11" || "$PYTHON_VERSION" == "3.12" ]]; then
            print_message $GREEN "✅ Python $PYTHON_VERSION 已安装"
            PYTHON_CMD="python3"
        else
            print_message $YELLOW "⚠️  Python版本 $PYTHON_VERSION 不是推荐版本 (3.11或3.12)"
            print_message $YELLOW "继续使用当前版本，如果遇到问题请升级Python"
            PYTHON_CMD="python3"
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ "$PYTHON_VERSION" == "3.11" || "$PYTHON_VERSION" == "3.12" ]]; then
            print_message $GREEN "✅ Python $PYTHON_VERSION 已安装"
            PYTHON_CMD="python"
        else
            print_message $YELLOW "⚠️  Python版本 $PYTHON_VERSION 不是推荐版本 (3.11或3.12)"
            print_message $YELLOW "继续使用当前版本，如果遇到问题请升级Python"
            PYTHON_CMD="python"
        fi
    else
        print_message $RED "❌ 未找到Python，请先安装Python 3.11或3.12"
        print_message $BLUE "安装指南:"
        if [[ "$OS" == "macos" ]]; then
            print_message $BLUE "  brew install python@3.12"
        elif [[ "$OS" == "linux" ]]; then
            print_message $BLUE "  sudo apt install python3.12 python3.12-venv python3.12-pip"
        else
            print_message $BLUE "  访问 https://www.python.org/downloads/ 下载安装"
        fi
        exit 1
    fi
}

# 检查Git
check_git() {
    print_title "检查Git"
    
    if command -v git &> /dev/null; then
        print_message $GREEN "✅ Git 已安装"
    else
        print_message $RED "❌ 未找到Git，请先安装Git"
        if [[ "$OS" == "macos" ]]; then
            print_message $BLUE "  brew install git"
        elif [[ "$OS" == "linux" ]]; then
            print_message $BLUE "  sudo apt install git"
        else
            print_message $BLUE "  访问 https://git-scm.com/downloads 下载安装"
        fi
        exit 1
    fi
}

# 创建虚拟环境
create_venv() {
    print_title "创建Python虚拟环境"
    
    if [ ! -d "venv" ]; then
        print_message $BLUE "📦 创建虚拟环境..."
        $PYTHON_CMD -m venv venv
        print_message $GREEN "✅ 虚拟环境创建成功"
    else
        print_message $YELLOW "ℹ️  虚拟环境已存在，跳过创建"
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
    print_title "安装Python依赖"
    
    print_message $BLUE "📦 升级pip..."
    pip install --upgrade pip
    
    print_message $BLUE "📦 安装项目依赖..."
    pip install -r requirements-local.txt
    
    print_message $GREEN "✅ 依赖安装完成"
}

# 安装Redis
install_redis() {
    print_title "安装和配置Redis"
    
    if command -v redis-server &> /dev/null; then
        print_message $GREEN "✅ Redis 已安装"
    else
        print_message $BLUE "📦 安装Redis..."
        
        if [[ "$OS" == "macos" ]]; then
            if command -v brew &> /dev/null; then
                brew install redis
            else
                print_message $RED "❌ 未找到Homebrew，请先安装Homebrew"
                print_message $BLUE "安装命令: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
        elif [[ "$OS" == "linux" ]]; then
            sudo apt update
            sudo apt install -y redis-server
        else
            print_message $YELLOW "⚠️  Windows系统请手动安装Redis"
            print_message $BLUE "下载地址: https://github.com/microsoftarchive/redis/releases"
        fi
        
        print_message $GREEN "✅ Redis 安装完成"
    fi
}

# 创建目录结构
create_directories() {
    print_title "创建项目目录结构"
    
    print_message $BLUE "📁 创建用户数据目录..."
    mkdir -p userdata/{backups,logs,exports,uploads,redis}
    chmod -R 755 userdata
    
    print_message $GREEN "✅ 目录结构创建完成"
}

# 配置环境变量
setup_environment() {
    print_title "配置环境变量"
    
    if [ ! -f ".env" ]; then
        print_message $BLUE "⚙️  创建环境配置文件..."
        cat > .env << EOF
# 泰摸鱼吧 - 开发环境配置
FLASK_APP=app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-$(date +%s)

# 数据库配置（使用默认SQLite）
# DATABASE_URL=sqlite:///./userdata/taifish_dev.db
# SQLALCHEMY_DATABASE_URI=sqlite:///./userdata/taifish_dev.db

# Redis配置
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=dev-jwt-secret-$(date +%s)
JWT_ACCESS_TOKEN_EXPIRES=3600

# 开发模式
DEVELOPMENT=True
EOF
        print_message $GREEN "✅ 环境配置文件创建完成"
    else
        print_message $YELLOW "ℹ️  环境配置文件已存在，跳过创建"
    fi
}

# 启动Redis
start_redis() {
    print_title "启动Redis服务"
    
    if ./redis_manager.sh status > /dev/null 2>&1; then
        print_message $GREEN "✅ Redis 已在运行"
    else
        print_message $BLUE "🚀 启动Redis服务..."
        ./redis_manager.sh start
    fi
}

# 测试环境
test_environment() {
    print_title "测试开发环境"
    
    print_message $BLUE "🔧 测试数据库连接..."
    if python test_database.py; then
        print_message $GREEN "✅ 数据库连接正常"
    else
        print_message $RED "❌ 数据库连接失败"
        return 1
    fi
    
    print_message $BLUE "🔴 测试Redis连接..."
    if ./redis_manager.sh status > /dev/null 2>&1; then
        print_message $GREEN "✅ Redis连接正常"
    else
        print_message $RED "❌ Redis连接失败"
        return 1
    fi
}

# 显示完成信息
show_completion() {
    print_title "安装完成"
    
    print_message $GREEN "🎉 开发环境安装完成！"
    echo ""
    print_message $BLUE "📋 下一步操作:"
    print_message $BLUE "  1. 启动应用: ./start_dev_with_redis.sh"
    print_message $BLUE "  2. 或手动启动: python app.py"
    print_message $BLUE "  3. 访问应用: http://localhost:5001"
    echo ""
    print_message $BLUE "🛠️  开发工具:"
    print_message $BLUE "  - Redis管理: ./redis_manager.sh"
    print_message $BLUE "  - 数据库迁移: ./dev_workflow.sh"
    print_message $BLUE "  - 测试环境: python test_database.py"
    echo ""
    print_message $BLUE "📚 文档:"
    print_message $BLUE "  - 开发指南: doc/development/ENVIRONMENT_SETUP.md"
    print_message $BLUE "  - 数据库迁移: doc/development/DATABASE_MIGRATION.md"
    echo ""
    print_message $YELLOW "💡 提示: 如果遇到问题，请查看故障排除部分或联系项目维护者"
}

# 主函数
main() {
    print_title "泰摸鱼吧 - 开发环境一键安装"
    
    check_os
    check_python
    check_git
    create_venv
    activate_venv
    install_dependencies
    install_redis
    create_directories
    setup_environment
    start_redis
    
    if test_environment; then
        show_completion
    else
        print_message $RED "❌ 环境测试失败，请检查错误信息并重试"
        exit 1
    fi
}

# 执行主函数
main "$@"
