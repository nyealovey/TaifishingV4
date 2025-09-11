#!/bin/bash

# 泰摸鱼吧 - UV 开发环境脚本
# 使用 uv 管理开发环境和工具

echo "🛠️  泰摸鱼吧开发环境 - UV 版本"
echo "================================"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: uv 未安装"
    echo "请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 同步开发依赖
echo "📦 同步开发依赖..."
uv sync --dev

# 运行代码格式化
echo "🎨 运行代码格式化..."
uv run black app/ --line-length 88

# 运行代码检查
echo "🔍 运行代码检查..."
uv run flake8 app/ --max-line-length=88 --ignore=E203,W503

# 运行类型检查
echo "🔬 运行类型检查..."
uv run mypy app/ --ignore-missing-imports

# 运行测试
echo "🧪 运行测试..."
uv run pytest tests/ -v

echo "✅ 开发环境检查完成！"
