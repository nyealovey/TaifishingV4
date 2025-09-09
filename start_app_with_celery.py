#!/usr/bin/env python3
"""
泰摸鱼吧 - 集成启动脚本
同时启动Flask应用和Celery服务
"""

import os
import sys
import signal
import time
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n🛑 收到信号 {signum}，正在关闭应用...")
    sys.exit(0)

def check_redis():
    """检查Redis是否运行"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def main():
    """主函数"""
    print("🚀 泰摸鱼吧 - 集成启动")
    print("=" * 50)
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 检查Redis
    print("🔍 检查Redis服务...")
    if not check_redis():
        print("❌ Redis服务未运行，请先启动Redis")
        print("   启动命令: redis-server")
        return 1
    print("✅ Redis服务正常")
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 虚拟环境已激活")
    else:
        print("⚠️  建议在虚拟环境中运行")
    
    # 设置环境变量
    os.environ.setdefault('FLASK_APP', 'app.py')
    os.environ.setdefault('FLASK_ENV', 'development')
    
    try:
        # 导入Flask应用
        from app import create_app
        
        print("🔧 创建Flask应用...")
        app = create_app()
        
        print("✅ Flask应用创建成功")
        print("🌐 启动Web服务器...")
        print("📱 访问地址: http://localhost:5001")
        print("🔧 Celery状态: http://localhost:5001/celery/status")
        print("=" * 50)
        print("按 Ctrl+C 停止服务")
        print("=" * 50)
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            use_reloader=False  # 禁用重载器，避免Celery重复启动
        )
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在关闭...")
        return 0
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
