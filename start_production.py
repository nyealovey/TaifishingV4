#!/usr/bin/env python3
"""
泰摸鱼吧 - 生产环境启动脚本
使用gunicorn启动Flask应用，自动管理Celery服务
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_redis():
    """检查Redis是否运行"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def start_celery_services():
    """启动Celery服务"""
    try:
        print("🚀 启动Celery服务...")
        
        # 启动Celery Beat
        beat_cmd = [
            sys.executable, '-m', 'celery',
            '-A', 'app.celery',
            'beat',
            '--loglevel=info',
            '--pidfile=celerybeat.pid'
        ]
        
        beat_process = subprocess.Popen(
            beat_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        
        # 启动Celery Worker
        worker_cmd = [
            sys.executable, '-m', 'celery',
            '-A', 'app.celery',
            'worker',
            '--loglevel=info',
            '--concurrency=4'
        ]
        
        worker_process = subprocess.Popen(
            worker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        
        # 等待一下确保启动成功
        time.sleep(3)
        
        if beat_process.poll() is None and worker_process.poll() is None:
            print("✅ Celery服务启动成功")
            return beat_process, worker_process
        else:
            print("❌ Celery服务启动失败")
            return None, None
            
    except Exception as e:
        print(f"❌ 启动Celery服务异常: {e}")
        return None, None

def stop_celery_services(beat_process, worker_process):
    """停止Celery服务"""
    try:
        print("🛑 停止Celery服务...")
        
        if beat_process and beat_process.poll() is None:
            beat_process.terminate()
            beat_process.wait(timeout=5)
            print("✅ Celery Beat已停止")
        
        if worker_process and worker_process.poll() is None:
            worker_process.terminate()
            worker_process.wait(timeout=5)
            print("✅ Celery Worker已停止")
            
    except Exception as e:
        print(f"❌ 停止Celery服务失败: {e}")

def main():
    """主函数"""
    print("🚀 泰摸鱼吧 - 生产环境启动")
    print("=" * 50)
    
    # 检查Redis
    if not check_redis():
        print("❌ Redis服务未运行，请先启动Redis")
        return 1
    
    # 启动Celery服务
    beat_process, worker_process = start_celery_services()
    if not beat_process or not worker_process:
        print("❌ 无法启动Celery服务")
        return 1
    
    try:
        # 启动Flask应用
        print("🌐 启动Flask应用...")
        print("📱 访问地址: http://localhost:5001")
        print("=" * 50)
        
        # 使用gunicorn启动
        gunicorn_cmd = [
            'gunicorn',
            '--bind', '0.0.0.0:5001',
            '--workers', '4',
            '--timeout', '120',
            '--keep-alive', '5',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--preload',
            'app:create_app()'
        ]
        
        subprocess.run(gunicorn_cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在关闭...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
    finally:
        # 停止Celery服务
        stop_celery_services(beat_process, worker_process)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
