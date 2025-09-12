#!/bin/bash

# 泰摸鱼吧应用停止脚本

echo "🛑 停止泰摸鱼吧应用..."

# 查找并停止所有相关进程
PIDS=$(ps aux | grep "python app.py" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "没有找到运行中的应用"
else
    echo "找到以下进程: $PIDS"
    echo "正在停止..."
    kill -9 $PIDS
    echo "应用已停止"
fi

# 清理日志文件（可选）
if [ "$1" = "clean" ]; then
    echo "清理日志文件..."
    rm -f app.log
    echo "日志文件已清理"
fi
