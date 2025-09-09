#!/bin/bash

echo "🐟 泰摸鱼吧 - 应用启动脚本"
echo "==================================================="

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境 'venv' 不存在。请先运行 'setup_dev_environment.sh'。"
    exit 1
fi

# 检查Flask
echo "🔍 检查Flask..."
python3 -c "import flask; print(f'✅ Flask版本: {flask.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Flask未安装。请运行: pip install -r requirements.txt"
    exit 1
fi

# 检查Oracle环境变量
echo "🔍 检查Oracle环境变量..."
if [ -f ".env" ]; then
    source .env
    echo "✅ 已加载.env文件"
    if [ -n "$DYLD_LIBRARY_PATH" ]; then
        echo "✅ DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"
    else
        echo "⚠️  DYLD_LIBRARY_PATH未设置"
    fi
else
    echo "⚠️  .env文件不存在"
fi

# 启动应用
echo "🚀 启动Flask应用..."
echo "使用命令: python3 app.py"
echo "==================================================="
python3 app.py
