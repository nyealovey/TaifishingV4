#!/bin/bash
# 泰摸鱼吧 - macOS开发环境启动脚本

set -e

echo "🍎 启动泰摸鱼吧开发环境 (macOS版)..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker Desktop"
    echo "   1. 打开Docker Desktop应用"
    echo "   2. 等待Docker完全启动"
    echo "   3. 重新运行此脚本"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Desktop"
    exit 1
fi

# 检查Docker Desktop是否完全启动
echo "🔍 检查Docker Desktop状态..."
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker Desktop未完全启动，请等待Docker完全启动后重试"
    exit 1
fi

# 创建环境变量文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp env.example .env
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
fi

# 创建用户数据目录
echo "📁 创建用户数据目录..."
mkdir -p userdata/{logs,uploads,backups,exports}

# 设置目录权限 (macOS兼容)
chmod -R 755 userdata/

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 清理Docker缓存 (macOS优化)
echo "🧹 清理Docker缓存..."
docker system prune -f

# 构建镜像 (macOS优化)
echo "🔨 构建Docker镜像..."
docker-compose build --no-cache

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 等待健康检查通过
echo "🏥 等待健康检查通过..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✅ 服务健康检查通过"
        break
    fi
    echo "⏳ 等待健康检查... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

# 显示日志
echo "📋 显示服务日志..."
docker-compose logs --tail=50

echo ""
echo "✅ 开发环境启动完成！"
echo ""
echo "🌐 应用访问地址:"
echo "   - 主应用: http://localhost:8000"
echo "   - 健康检查: http://localhost:8000/api/health"
echo ""
echo "📊 服务状态:"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo "   - Flask应用: localhost:8000"
echo ""
echo "📝 常用命令:"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo "   - 进入容器: docker-compose exec flask bash"
echo ""
echo "🔧 下一步操作:"
echo "   1. 运行数据初始化脚本: docker-compose exec flask python scripts/init_data.py --init-all"
echo "   2. 验证数据: docker-compose exec flask python scripts/init_data.py --validate-all"
echo "   3. 访问应用: http://localhost:8000"
echo ""
echo "🍎 macOS特别提示:"
echo "   - 如果遇到权限问题，请检查Docker Desktop的权限设置"
echo "   - 如果端口被占用，请检查其他应用是否使用了相同端口"
echo "   - 如果内存不足，请在Docker Desktop中增加内存分配"
