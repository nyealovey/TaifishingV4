#!/bin/bash

# 泰摸鱼吧 - 带Oracle支持的启动脚本

echo "🐟 泰摸鱼吧 - 启动应用（带Oracle支持）"
echo "========================================"

# 设置Oracle Instant Client环境变量
echo "🔧 设置Oracle Instant Client环境变量..."
export DYLD_LIBRARY_PATH="/Users/apple/Downloads/instantclient_23_3:$DYLD_LIBRARY_PATH"

# 验证环境变量
echo "📋 环境变量检查:"
echo "   DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"

# 检查Oracle Instant Client
oracle_path="/Users/apple/Downloads/instantclient_23_3"
if [ -d "$oracle_path" ]; then
    echo "   ✅ Oracle Instant Client路径存在: $oracle_path"
    if [ -f "$oracle_path/libclntsh.dylib" ]; then
        echo "   ✅ Oracle Instant Client库文件存在"
    else
        echo "   ❌ Oracle Instant Client库文件不存在"
        exit 1
    fi
else
    echo "   ❌ Oracle Instant Client路径不存在: $oracle_path"
    exit 1
fi

# 测试cx_Oracle
echo "🧪 测试cx_Oracle..."
python3 -c "
import cx_Oracle
print(f'   ✅ cx_Oracle版本: {cx_Oracle.version}')
try:
    client_version = cx_Oracle.clientversion()
    print(f'   ✅ Oracle Client版本: {client_version}')
except Exception as e:
    print(f'   ❌ Oracle Client测试失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Oracle环境测试失败"
    exit 1
fi

echo ""
echo "🚀 启动Flask应用..."

# 启动Flask应用
python3 app.py
