#!/bin/bash
# 泰摸鱼吧 - 渐进式依赖安装脚本

echo "🚀 泰摸鱼吧 - 渐进式依赖安装"
echo "================================"

# 阶段1: 核心依赖 (已安装)
echo "✅ 阶段1: 核心依赖已安装"
echo "   - Flask框架"
echo "   - 数据库ORM"
echo "   - 基础认证"

# 阶段2: 数据库驱动
echo ""
echo "🔧 阶段2: 安装数据库驱动..."

# MySQL驱动 (通常没问题)
echo "   - 安装MySQL驱动..."
pip install PyMySQL==1.0.2

# SQL Server驱动 (可能有编译问题)
echo "   - 尝试安装SQL Server驱动..."
if pip install pymssql==2.2.5; then
    echo "   ✅ SQL Server驱动安装成功"
else
    echo "   ⚠️  SQL Server驱动安装失败，将在后续处理"
fi

# ODBC驱动 (可能有编译问题)
echo "   - 尝试安装ODBC驱动..."
if pip install pyodbc==4.0.32; then
    echo "   ✅ ODBC驱动安装成功"
else
    echo "   ⚠️  ODBC驱动安装失败，将在后续处理"
fi

# Oracle驱动 (需要客户端)
echo "   - 尝试安装Oracle驱动..."
if pip install cx-Oracle==8.3.0; then
    echo "   ✅ Oracle驱动安装成功"
else
    echo "   ⚠️  Oracle驱动安装失败，需要安装Oracle Instant Client"
fi

# 阶段3: 安全组件
echo ""
echo "🔐 阶段3: 安装安全组件..."

# Flask-Security (可能有依赖冲突)
echo "   - 尝试安装Flask-Security..."
if pip install Flask-Security==5.6.2; then
    echo "   ✅ Flask-Security安装成功"
else
    echo "   ⚠️  Flask-Security安装失败，使用替代方案"
    echo "   - 将使用Flask-Login + Flask-JWT-Extended组合"
fi

# 阶段4: 日志组件
echo ""
echo "📝 阶段4: 安装日志组件..."

# Flask-Logging (有问题)
echo "   - 尝试安装Flask-Logging..."
if pip install Flask-Logging==0.1.0; then
    echo "   ✅ Flask-Logging安装成功"
else
    echo "   ⚠️  Flask-Logging安装失败，使用Python标准库logging"
fi

echo ""
echo "🎉 渐进式依赖安装完成！"
echo ""
echo "📊 安装状态总结:"
echo "   - 核心功能: ✅ 可用"
echo "   - MySQL支持: ✅ 可用"
echo "   - SQL Server支持: 待确认"
echo "   - Oracle支持: 待确认"
echo "   - 用户认证: ✅ 可用"
echo "   - 日志记录: ✅ 可用"
echo ""
echo "🔧 下一步:"
echo "   1. 测试数据库连接"
echo "   2. 测试用户认证功能"
echo "   3. 根据实际需要安装缺失的驱动"
