#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 修复的Celery Beat启动脚本
"""

import os
import sys
import signal
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('FLASK_APP', 'app')
os.environ.setdefault('FLASK_ENV', 'development')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('userdata/logs/celery_beat.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭Celery Beat...")
    sys.exit(0)

def check_redis_connection():
    """检查Redis连接"""
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        logger.info(f"尝试连接Redis: {redis_url}")
        
        # 解析Redis URL
        if '://' in redis_url:
            if '@' in redis_url:
                # 有密码的格式: redis://:password@host:port/db
                parts = redis_url.split('://')[1].split('@')
                if len(parts) == 2:
                    password = parts[0].lstrip(':')
                    host_port_db = parts[1]
                    host_port, db = host_port_db.split('/')
                    host, port = host_port.split(':')
                    
                    r = redis.Redis(host=host, port=int(port), db=int(db), password=password, decode_responses=True)
                else:
                    r = redis.Redis.from_url(redis_url, decode_responses=True)
            else:
                r = redis.Redis.from_url(redis_url, decode_responses=True)
        else:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        r.ping()
        logger.info("Redis连接成功")
        return True
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        return False

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("启动泰摸鱼吧 Celery Beat 调度器...")
    
    # 检查Redis连接
    if not check_redis_connection():
        logger.error("无法连接到Redis，退出")
        sys.exit(1)
    
    try:
        from app.celery_config import celery
        
        # 启动Celery Beat
        logger.info("正在启动Celery Beat...")
        celery.start(['beat', '--loglevel=info', '--pidfile=celerybeat.pid'])
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"Celery Beat启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        logger.info("Celery Beat已关闭")

if __name__ == '__main__':
    main()
