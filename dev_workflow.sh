#!/bin/bash

# 泰摸鱼吧 - 开发工作流脚本
# 确保每次开发功能时数据不丢失

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

# 开始新功能开发
start_feature() {
    local feature_name=$1
    
    if [ -z "$feature_name" ]; then
        print_message $RED "❌ 请提供功能名称"
        echo "用法: ./dev_workflow.sh start '功能名称'"
        exit 1
    fi
    
    print_title "开始新功能开发: $feature_name"
    
    check_venv
    
    # 1. 检查当前数据库状态
    print_message $BLUE "📊 检查当前数据库状态..."
    flask db current
    
    # 2. 创建功能分支（如果使用Git）
    if [ -d ".git" ]; then
        print_message $BLUE "🌿 创建功能分支..."
        git checkout -b "feature/$feature_name" 2>/dev/null || git checkout "feature/$feature_name"
    fi
    
    print_message $GREEN "✅ 功能开发环境准备完成"
    print_message $YELLOW "💡 提示: 修改模型后记得运行 './dev_workflow.sh migrate'"
}

# 创建数据库迁移
create_migration() {
    local message=$1
    
    if [ -z "$message" ]; then
        print_message $RED "❌ 请提供迁移描述"
        echo "用法: ./dev_workflow.sh migrate '迁移描述'"
        exit 1
    fi
    
    print_title "创建数据库迁移"
    
    check_venv
    
    # 1. 检查模型变更
    print_message $BLUE "🔍 检查模型变更..."
    flask db migrate -m "$message"
    
    # 2. 显示生成的迁移文件
    print_message $BLUE "📝 生成的迁移文件:"
    ls -la migrations/versions/ | tail -1
    
    print_message $GREEN "✅ 迁移文件创建成功"
    print_message $YELLOW "💡 提示: 检查迁移文件后运行 './dev_workflow.sh apply' 应用迁移"
}

# 应用数据库迁移
apply_migration() {
    print_title "应用数据库迁移"
    
    check_venv
    
    # 1. 显示当前版本
    print_message $BLUE "📊 当前数据库版本:"
    flask db current
    
    # 2. 显示将要应用的迁移
    print_message $BLUE "📋 待应用的迁移:"
    flask db history --verbose
    
    # 3. 确认应用
    read -p "确认应用迁移？(y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        print_message $BLUE "⬆️  应用数据库迁移..."
        flask db upgrade
        
        print_message $GREEN "✅ 数据库迁移应用成功"
        
        # 4. 显示新版本
        print_message $BLUE "📊 新数据库版本:"
        flask db current
    else
        print_message $YELLOW "❌ 迁移已取消"
    fi
}

# 回滚数据库迁移
rollback_migration() {
    local steps=${1:-1}
    
    print_title "回滚数据库迁移"
    
    check_venv
    
    # 1. 显示当前版本
    print_message $BLUE "📊 当前数据库版本:"
    flask db current
    
    # 2. 显示回滚目标
    print_message $BLUE "📋 回滚 $steps 个版本..."
    
    # 3. 确认回滚
    read -p "确认回滚？(y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        print_message $BLUE "⬇️  回滚数据库迁移..."
        flask db downgrade -$steps
        
        print_message $GREEN "✅ 数据库回滚成功"
        
        # 4. 显示新版本
        print_message $BLUE "📊 新数据库版本:"
        flask db current
    else
        print_message $YELLOW "❌ 回滚已取消"
    fi
}

# 备份数据库
backup_database() {
    local backup_name=${1:-"backup_$(date +%Y%m%d_%H%M%S)"}
    
    print_title "备份数据库"
    
    check_venv
    
    # 创建备份目录
    mkdir -p userdata/backups
    
    # 备份SQLite数据库
    if [ -f "userdata/taifish_dev.db" ]; then
        cp userdata/taifish_dev.db "userdata/backups/${backup_name}.db"
        print_message $GREEN "✅ 数据库备份完成: userdata/backups/${backup_name}.db"
    else
        print_message $YELLOW "⚠️  数据库文件不存在"
    fi
}

# 恢复数据库
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_message $RED "❌ 请指定备份文件"
        echo "用法: ./dev_workflow.sh restore <备份文件>"
        echo "可用备份文件:"
        ls -la userdata/backups/*.db 2>/dev/null || echo "  无备份文件"
        exit 1
    fi
    
    print_title "恢复数据库"
    
    check_venv
    
    # 确认恢复
    read -p "确认恢复数据库？这将覆盖当前数据！(y/N): " confirm
    
    if [[ $confirm =~ ^[Yy]$ ]]; then
        if [ -f "$backup_file" ]; then
            cp "$backup_file" userdata/taifish_dev.db
            print_message $GREEN "✅ 数据库恢复成功"
        else
            print_message $RED "❌ 备份文件不存在: $backup_file"
        fi
    else
        print_message $YELLOW "❌ 恢复已取消"
    fi
}

# 显示开发状态
show_status() {
    print_title "开发状态"
    
    check_venv
    
    # 1. 数据库版本
    print_message $BLUE "📊 数据库版本:"
    flask db current
    
    # 2. 迁移历史
    print_message $BLUE "📚 最近迁移:"
    flask db history --verbose | head -5
    
    # 3. 数据库文件大小
    if [ -f "userdata/taifish_dev.db" ]; then
        local db_size=$(du -h userdata/taifish_dev.db | cut -f1)
        print_message $BLUE "💾 数据库大小: $db_size"
    fi
    
    # 4. 备份文件
    local backup_count=$(ls userdata/backups/*.db 2>/dev/null | wc -l)
    print_message $BLUE "💾 备份文件数量: $backup_count"
}

# 显示帮助
show_help() {
    echo "泰摸鱼吧 - 开发工作流"
    echo ""
    echo "用法: ./dev_workflow.sh <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  start <name>             开始新功能开发"
    echo "  migrate <message>        创建数据库迁移"
    echo "  apply                    应用数据库迁移"
    echo "  rollback [steps]         回滚数据库迁移"
    echo "  backup [name]            备份数据库"
    echo "  restore <file>           恢复数据库"
    echo "  status                   显示开发状态"
    echo "  help                     显示此帮助信息"
    echo ""
    echo "开发流程:"
    echo "  1. ./dev_workflow.sh start '功能名称'"
    echo "  2. 修改模型文件"
    echo "  3. ./dev_workflow.sh migrate '描述变更'"
    echo "  4. ./dev_workflow.sh apply"
    echo "  5. 测试功能"
    echo "  6. 如有问题: ./dev_workflow.sh rollback"
    echo ""
    echo "示例:"
    echo "  ./dev_workflow.sh start '用户管理'"
    echo "  ./dev_workflow.sh migrate '添加用户角色字段'"
    echo "  ./dev_workflow.sh apply"
    echo "  ./dev_workflow.sh backup '用户管理完成'"
}

# 主函数
main() {
    case "${1:-}" in
        start)
            start_feature "$2"
            ;;
        migrate)
            create_migration "$2"
            ;;
        apply)
            apply_migration
            ;;
        rollback)
            rollback_migration "$2"
            ;;
        backup)
            backup_database "$2"
            ;;
        restore)
            restore_database "$2"
            ;;
        status)
            show_status
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
