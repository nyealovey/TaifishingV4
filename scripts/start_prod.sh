#!/bin/bash
# 泰摸鱼吧 - 生产环境启动脚本

set -e

echo "🚀 启动泰摸鱼吧生产环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "❌ 环境变量文件 .env 不存在，请先创建并配置"
    exit 1
fi

# 验证必需的环境变量
echo "🔍 验证环境变量..."
source .env

required_vars=("SECRET_KEY" "JWT_SECRET_KEY" "POSTGRES_PASSWORD" "REDIS_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ 必需的环境变量 $var 未设置"
        exit 1
    fi
done

# 创建用户数据目录
echo "📁 创建用户数据目录..."
mkdir -p userdata/{logs,uploads,backups,exports}

# 设置目录权限
chmod -R 755 userdata/

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose -f docker-compose.prod.yml down

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose -f docker-compose.prod.yml build

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 显示日志
echo "📋 显示服务日志..."
docker-compose -f docker-compose.prod.yml logs --tail=50

echo ""
echo "✅ 生产环境启动完成！"
echo ""
echo "🌐 应用访问地址:"
echo "   - 主应用: http://localhost:8000"
echo "   - 健康检查: http://localhost:8000/health"
echo ""
echo "📊 服务状态:"
echo "   - PostgreSQL: 内部网络"
echo "   - Redis: 内部网络"
echo "   - Flask应用: localhost:8000"
echo ""
echo "📝 常用命令:"
echo "   - 查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "   - 停止服务: docker-compose -f docker-compose.prod.yml down"
echo "   - 重启服务: docker-compose -f docker-compose.prod.yml restart"
echo "   - 进入容器: docker-compose -f docker-compose.prod.yml exec flask bash"
echo ""
echo "🔧 下一步操作:"
echo "   1. 运行数据初始化脚本: docker-compose -f docker-compose.prod.yml exec flask python scripts/init_data.py --init-all"
echo "   2. 验证数据: docker-compose -f docker-compose.prod.yml exec flask python scripts/init_data.py --validate-all"
echo "   3. 访问应用: http://localhost:8000"
echo ""
echo "⚠️  生产环境注意事项:"
echo "   - 确保所有敏感信息已正确配置"
echo "   - 定期备份数据库"
echo "   - 监控服务状态和日志"
echo "   - 定期更新安全补丁"
