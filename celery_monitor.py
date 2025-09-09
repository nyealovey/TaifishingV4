#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - Celery Beat监控和自动重启脚本
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('userdata/logs/celery_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_celery_beat():
    """检查Celery Beat是否运行"""
    try:
        result = subprocess.run(['pgrep', '-f', 'celery.*beat'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"检查Celery Beat进程失败: {e}")
        return False

def check_redis():
    """检查Redis是否运行"""
    try:
        result = subprocess.run(['redis-cli', '-a', 'taifish_redis_pass', 'ping'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"检查Redis失败: {e}")
        return False

def start_celery_beat():
    """启动Celery Beat"""
    try:
        logger.info("正在启动Celery Beat...")
        result = subprocess.run(['./manage_celery.sh', 'start'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Celery Beat启动成功")
            return True
        else:
            logger.error(f"Celery Beat启动失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"启动Celery Beat失败: {e}")
        return False

def main():
    """主监控循环"""
    logger.info("开始监控Celery Beat...")
    
    while True:
        try:
            # 检查Redis
            if not check_redis():
                logger.error("Redis未运行，请先启动Redis")
                time.sleep(30)
                continue
            
            # 检查Celery Beat
            if not check_celery_beat():
                logger.warning("Celery Beat未运行，正在启动...")
                if start_celery_beat():
                    logger.info("Celery Beat启动成功")
                else:
                    logger.error("Celery Beat启动失败")
            else:
                logger.debug("Celery Beat运行正常")
            
            # 等待60秒后再次检查
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止监控")
            break
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")
            time.sleep(30)

if __name__ == '__main__':
    main()
