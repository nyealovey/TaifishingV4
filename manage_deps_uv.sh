#!/bin/bash

# 泰摸鱼吧 - UV 依赖管理脚本
# 使用 uv 管理项目依赖

echo "📦 泰摸鱼吧依赖管理 - UV 版本"
echo "=============================="

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: uv 未安装"
    echo "请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  install     安装所有依赖"
    echo "  install-dev 安装开发依赖"
    echo "  update      更新所有依赖"
    echo "  add <包名>  添加新依赖"
    echo "  add-dev <包名> 添加开发依赖"
    echo "  remove <包名> 移除依赖"
    echo "  list        列出已安装的包"
    echo "  tree        显示依赖树"
    echo "  clean       清理缓存"
    echo "  help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 install"
    echo "  $0 add requests"
    echo "  $0 add-dev pytest"
    echo "  $0 remove requests"
}

# 根据参数执行相应操作
case "${1:-help}" in
    "install")
        echo "📦 安装所有依赖..."
        uv sync
        ;;
    "install-dev")
        echo "📦 安装开发依赖..."
        uv sync --dev
        ;;
    "update")
        echo "🔄 更新所有依赖..."
        uv sync --upgrade
        ;;
    "add")
        if [ -z "$2" ]; then
            echo "❌ 错误: 请指定要添加的包名"
            echo "用法: $0 add <包名>"
            exit 1
        fi
        echo "➕ 添加依赖: $2"
        uv add "$2"
        ;;
    "add-dev")
        if [ -z "$2" ]; then
            echo "❌ 错误: 请指定要添加的开发包名"
            echo "用法: $0 add-dev <包名>"
            exit 1
        fi
        echo "➕ 添加开发依赖: $2"
        uv add --dev "$2"
        ;;
    "remove")
        if [ -z "$2" ]; then
            echo "❌ 错误: 请指定要移除的包名"
            echo "用法: $0 remove <包名>"
            exit 1
        fi
        echo "➖ 移除依赖: $2"
        uv remove "$2"
        ;;
    "list")
        echo "📋 已安装的包:"
        uv pip list
        ;;
    "tree")
        echo "🌳 依赖树:"
        uv pip show --tree
        ;;
    "clean")
        echo "🧹 清理缓存..."
        uv cache clean
        ;;
    "help"|*)
        show_help
        ;;
esac
