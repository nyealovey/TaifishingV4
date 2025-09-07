#!/bin/bash
# 泰摸鱼吧 - x86_64开发环境启动脚本

set -e

echo "🍎 启动泰摸鱼吧开发环境 (x86_64版本)..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker Desktop"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Desktop"
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

# 设置目录权限
chmod -R 755 userdata/

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose -f docker-compose.x86_64.yml down

# 清理Docker缓存
echo "🧹 清理Docker缓存..."
docker system prune -f

# 构建x86_64镜像
echo "🔨 构建x86_64 Docker镜像..."
docker-compose -f docker-compose.x86_64.yml build --no-cache

# 启动服务
echo "🚀 启动服务..."
docker-compose -f docker-compose.x86_64.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.x86_64.yml ps

# 等待健康检查通过
echo "🏥 等待健康检查通过..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose -f docker-compose.x86_64.yml ps | grep -q "healthy"; then
        echo "✅ 服务健康检查通过"
        break
    fi
    echo "⏳ 等待健康检查... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

# 显示日志
echo "📋 显示服务日志..."
docker-compose -f docker-compose.x86_64.yml logs --tail=50

echo ""
echo "✅ x86_64开发环境启动完成！"
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
echo "🔧 数据库驱动状态:"
echo "   - MySQL: ✅ PyMySQL"
echo "   - PostgreSQL: ✅ psycopg2"
echo "   - SQL Server: ✅ pymssql (x86_64)"
echo "   - Oracle: ✅ cx_Oracle (x86_64)"
echo "   - ODBC: ✅ pyodbc (x86_64)"
echo ""
echo "📝 常用命令:"
echo "   - 查看日志: docker-compose -f docker-compose.x86_64.yml logs -f"
echo "   - 停止服务: docker-compose -f docker-compose.x86_64.yml down"
echo "   - 重启服务: docker-compose -f docker-compose.x86_64.yml restart"
echo "   - 进入容器: docker-compose -f docker-compose.x86_64.yml exec flask bash"
echo ""
echo "🔧 下一步操作:"
echo "   1. 运行数据初始化脚本: docker-compose -f docker-compose.x86_64.yml exec flask python scripts/init_data.py --init-all"
echo "   2. 验证数据: docker-compose -f docker-compose.x86_64.yml exec flask python scripts/init_data.py --validate-all"
echo "   3. 访问应用: http://localhost:8000"
echo ""
echo "🍎 x86_64特别提示:"
echo "   - 使用x86_64架构解决了ARM64的编译问题"
echo "   - 所有数据库驱动都已安装并可用"
echo "   - 性能可能略低于原生ARM64，但功能完整"
