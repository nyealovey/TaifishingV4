#!/bin/bash

# Oracle Instant Client环境设置脚本
# 用于设置DYLD_LIBRARY_PATH环境变量

# Oracle Instant Client路径
ORACLE_INSTANT_CLIENT_PATH="/Users/apple/Downloads/instantclient_23_3"

# 检查Oracle Instant Client是否存在
if [ ! -d "$ORACLE_INSTANT_CLIENT_PATH" ]; then
    echo "❌ Oracle Instant Client未找到: $ORACLE_INSTANT_CLIENT_PATH"
    echo "请先安装Oracle Instant Client"
    exit 1
fi

# 检查libclntsh.dylib是否存在
if [ ! -f "$ORACLE_INSTANT_CLIENT_PATH/libclntsh.dylib" ]; then
    echo "❌ Oracle Instant Client库文件未找到: $ORACLE_INSTANT_CLIENT_PATH/libclntsh.dylib"
    exit 1
fi

# 设置环境变量
export DYLD_LIBRARY_PATH="$ORACLE_INSTANT_CLIENT_PATH:$DYLD_LIBRARY_PATH"

echo "✅ Oracle Instant Client环境设置完成"
echo "   路径: $ORACLE_INSTANT_CLIENT_PATH"
echo "   DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"

# 测试cx_Oracle
echo ""
echo "测试cx_Oracle..."
python3 -c "
import cx_Oracle
print(f'✅ cx_Oracle版本: {cx_Oracle.version}')
try:
    client_version = cx_Oracle.clientversion()
    print(f'✅ Oracle Client版本: {client_version}')
    print('✅ Oracle Instant Client工作正常！')
except Exception as e:
    print(f'❌ Oracle Client测试失败: {e}')
"

echo ""
echo "现在可以在泰摸鱼吧中使用Oracle功能了！"
echo ""
echo "注意: 每次重新打开终端时，需要重新运行此脚本或手动设置环境变量:"
echo "export DYLD_LIBRARY_PATH=$ORACLE_INSTANT_CLIENT_PATH:\$DYLD_LIBRARY_PATH"
