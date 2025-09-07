#!/bin/bash

# 泰摸鱼吧 - 数据库迁移管理脚本

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

# 检查虚拟环境
check_venv() {
    if [ ! -d "venv" ]; then
        print_message $RED "❌ 虚拟环境不存在，请先运行 ./start_dev.sh"
        exit 1
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
}

# 初始化迁移
init_migration() {
    print_title "初始化数据库迁移环境"
    
    check_venv
    
    print_message $BLUE "🔧 初始化迁移环境..."
    flask db init
    
    print_message $GREEN "✅ 迁移环境初始化完成"
}

# 创建迁移
create_migration() {
    local message=$1
    
    if [ -z "$message" ]; then
        print_message $RED "❌ 请提供迁移描述"
        echo "用法: ./migrate.sh create '迁移描述'"
        exit 1
    fi
    
    print_title "创建数据库迁移"
    
    check_venv
    
    print_message $BLUE "📝 创建迁移: $message"
    flask db migrate -m "$message"
    
    print_message $GREEN "✅ 迁移文件创建成功"
}

# 升级数据库
upgrade_database() {
    local revision=${1:-head}
    
    print_title "升级数据库"
    
    check_venv
    
    print_message $BLUE "⬆️  升级数据库到: $revision"
    flask db upgrade $revision
    
    print_message $GREEN "✅ 数据库升级成功"
}

# 降级数据库
downgrade_database() {
    local revision=$1
    
    if [ -z "$revision" ]; then
        print_message $RED "❌ 请指定要降级到的版本"
        echo "用法: ./migrate.sh downgrade <版本号>"
        exit 1
    fi
    
    print_title "降级数据库"
    
    check_venv
    
    print_message $YELLOW "⚠️  降级数据库到: $revision"
    read -p "确认继续？(y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        flask db downgrade $revision
        print_message $GREEN "✅ 数据库降级成功"
    else
        print_message $YELLOW "❌ 操作已取消"
    fi
}

# 显示当前版本
show_current() {
    print_title "当前数据库版本"
    
    check_venv
    
    print_message $BLUE "📊 当前数据库版本:"
    flask db current
}

# 显示迁移历史
show_history() {
    print_title "迁移历史"
    
    check_venv
    
    print_message $BLUE "📚 迁移历史:"
    flask db history
}

# 显示帮助
show_help() {
    echo "泰摸鱼吧 - 数据库迁移管理"
    echo ""
    echo "用法: ./migrate.sh <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  init                    初始化迁移环境"
    echo "  create <message>        创建新的迁移"
    echo "  upgrade [revision]      升级数据库（默认到最新）"
    echo "  downgrade <revision>    降级数据库"
    echo "  current                 显示当前版本"
    echo "  history                 显示迁移历史"
    echo "  help                    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./migrate.sh init"
    echo "  ./migrate.sh create '添加用户表'"
    echo "  ./migrate.sh upgrade"
    echo "  ./migrate.sh downgrade -1"
    echo "  ./migrate.sh current"
    echo "  ./migrate.sh history"
}

# 主函数
main() {
    case "${1:-}" in
        init)
            init_migration
            ;;
        create)
            create_migration "$2"
            ;;
        upgrade)
            upgrade_database "$2"
            ;;
        downgrade)
            downgrade_database "$2"
            ;;
        current)
            show_current
            ;;
        history)
            show_history
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
