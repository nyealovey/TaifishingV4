#!/bin/bash
# 泰摸鱼吧 - 安装完整依赖脚本

echo "🔧 安装完整依赖包..."

# 检查是否在Docker容器中
if [ -f /.dockerenv ]; then
    echo "📦 在Docker容器中安装完整依赖..."
    pip install --no-cache-dir -r /app/requirements-full.txt
else
    echo "💻 在本地环境中安装完整依赖..."
    pip install -r requirements-full.txt
fi

echo "✅ 完整依赖安装完成！"
echo ""
echo "📋 已安装的数据库驱动:"
echo "   - PyMySQL (MySQL)"
echo "   - pymssql (SQL Server)"
echo "   - pyodbc (ODBC)"
echo "   - cx-Oracle (Oracle)"
echo ""
echo "🔐 已安装的安全组件:"
echo "   - Flask-Security (用户认证)"
echo "   - Flask-JWT-Extended (JWT认证)"
echo "   - Flask-Bcrypt (密码加密)"
echo ""
echo "⚠️  注意:"
echo "   - Oracle驱动需要安装Oracle Instant Client"
echo "   - SQL Server驱动可能需要额外的系统依赖"
echo "   - 如果遇到编译问题，请检查系统依赖"
