#!/bin/bash

# 泰摸鱼吧应用启动脚本
# 支持多种启动方式

echo "🐟 泰摸鱼吧应用启动脚本"
echo "================================"

# 检查参数
if [ "$1" = "uv" ]; then
    echo "使用 uv 启动应用..."
    nohup uv run python app.py > app.log 2>&1 &
    echo "应用已启动，日志文件: app.log"
    echo "访问地址: http://localhost:5001"
    echo "停止应用: pkill -f 'python app.py'"
elif [ "$1" = "venv" ]; then
    echo "使用虚拟环境启动应用..."
    source .venv/bin/activate
    nohup python app.py > app.log 2>&1 &
    echo "应用已启动，日志文件: app.log"
    echo "访问地址: http://localhost:5001"
    echo "停止应用: pkill -f 'python app.py'"
elif [ "$1" = "debug" ]; then
    echo "调试模式启动应用..."
    source .venv/bin/activate
    python app.py
else
    echo "用法: $0 [uv|venv|debug]"
    echo ""
    echo "启动方式:"
    echo "  uv     - 使用 uv 启动（推荐）"
    echo "  venv   - 使用虚拟环境启动"
    echo "  debug  - 调试模式启动（前台运行）"
    echo ""
    echo "示例:"
    echo "  $0 uv      # 使用 uv 后台启动"
    echo "  $0 venv    # 使用虚拟环境后台启动"
    echo "  $0 debug   # 调试模式前台启动"
fi
