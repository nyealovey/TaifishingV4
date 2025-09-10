#!/bin/bash

# 泰摸鱼吧 - 快速本地开发启动脚本

echo "🐟 泰摸鱼吧 - 本地开发环境"
echo "================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements-local.txt

# 启动Redis
echo "🔴 启动Redis..."
if ! ./scripts/start_redis.sh status > /dev/null 2>&1; then
    ./scripts/start_redis.sh start
else
    echo "✅ Redis已在运行"
fi

# 创建用户数据目录
echo "📁 创建用户数据目录..."
mkdir -p userdata/{backups,logs,exports,uploads}

# 创建环境配置
echo "⚙️  创建环境配置..."
cat > .env << EOF
FLASK_APP=app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///./userdata/taifish_dev.db
SQLALCHEMY_DATABASE_URI=sqlite:///./userdata/taifish_dev.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=dev-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600
DEVELOPMENT=True
EOF

# 初始化数据库迁移
echo "🔧 初始化数据库迁移..."
if [ ! -d "migrations" ]; then
    flask db init
    echo "✅ 迁移环境初始化完成"
else
    echo "✅ 迁移环境已存在"
fi

# 创建初始迁移（如果不存在）
echo "📝 检查数据库迁移..."
if [ ! -f "migrations/versions/$(ls migrations/versions/ 2>/dev/null | head -1)" ]; then
    flask db migrate -m "初始数据库结构"
    echo "✅ 初始迁移创建完成"
fi

# 升级数据库
echo "⬆️  升级数据库..."
flask db upgrade

# 初始化测试数据
echo "📊 初始化测试数据..."
python scripts/init_data.py --init-all

echo ""
echo "✅ 环境准备完成！"
echo "🌐 启动Flask应用..."
echo "📱 访问地址: http://localhost:5001"
echo "🔑 默认登录: admin/Admin123"
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动Flask应用
export FLASK_PORT=5001
python app.py
