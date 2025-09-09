#!/usr/bin/env python3
"""
泰摸鱼吧 - Celery 管理器
用于管理Celery Beat和Worker进程的生命周期
"""

import os
import sys
import signal
import threading
import time
import subprocess
import psutil
from typing import List, Optional

class CeleryManager:
    """Celery进程管理器"""
    
    def __init__(self):
        self.beat_process = None
        self.worker_process = None
        self.running = False
        self.shutdown_event = threading.Event()
        
    def start_celery_services(self):
        """启动Celery服务"""
        try:
            print("🚀 启动Celery服务...")
            
            # 检查Redis是否运行
            if not self._check_redis():
                print("❌ Redis服务未运行，请先启动Redis")
                return False
            
            # 启动Celery Beat
            if not self._start_beat():
                print("❌ 启动Celery Beat失败")
                return False
            
            # 启动Celery Worker
            if not self._start_worker():
                print("❌ 启动Celery Worker失败")
                return False
            
            self.running = True
            print("✅ Celery服务启动成功")
            
            # 启动监控线程
            self._start_monitor()
            
            return True
            
        except Exception as e:
            print(f"❌ 启动Celery服务失败: {e}")
            return False
    
    def stop_celery_services(self):
        """停止Celery服务"""
        try:
            print("🛑 停止Celery服务...")
            self.running = False
            self.shutdown_event.set()
            
            # 停止Beat进程
            if self.beat_process and self.beat_process.poll() is None:
                self.beat_process.terminate()
                try:
                    self.beat_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.beat_process.kill()
                print("✅ Celery Beat已停止")
            
            # 停止Worker进程
            if self.worker_process and self.worker_process.poll() is None:
                self.worker_process.terminate()
                try:
                    self.worker_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.worker_process.kill()
                print("✅ Celery Worker已停止")
            
            print("✅ Celery服务已完全停止")
            
        except Exception as e:
            print(f"❌ 停止Celery服务失败: {e}")
    
    def _check_redis(self) -> bool:
        """检查Redis是否运行"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return True
        except:
            return False
    
    def _start_beat(self) -> bool:
        """启动Celery Beat"""
        try:
            cmd = [
                sys.executable, '-m', 'celery',
                '-A', 'app.celery',
                'beat',
                '--loglevel=info',
                '--pidfile=celerybeat.pid'
            ]
            
            self.beat_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # 等待一下确保启动成功
            time.sleep(2)
            
            if self.beat_process.poll() is None:
                print("✅ Celery Beat启动成功")
                return True
            else:
                print("❌ Celery Beat启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动Celery Beat异常: {e}")
            return False
    
    def _start_worker(self) -> bool:
        """启动Celery Worker"""
        try:
            cmd = [
                sys.executable, '-m', 'celery',
                '-A', 'app.celery',
                'worker',
                '--loglevel=info',
                '--concurrency=4'
            ]
            
            self.worker_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # 等待一下确保启动成功
            time.sleep(2)
            
            if self.worker_process.poll() is None:
                print("✅ Celery Worker启动成功")
                return True
            else:
                print("❌ Celery Worker启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动Celery Worker异常: {e}")
            return False
    
    def _start_monitor(self):
        """启动监控线程"""
        def monitor():
            while self.running and not self.shutdown_event.is_set():
                try:
                    # 检查Beat进程
                    if self.beat_process and self.beat_process.poll() is not None:
                        print("⚠️  Celery Beat进程异常退出，尝试重启...")
                        if not self._start_beat():
                            print("❌ 重启Celery Beat失败")
                    
                    # 检查Worker进程
                    if self.worker_process and self.worker_process.poll() is not None:
                        print("⚠️  Celery Worker进程异常退出，尝试重启...")
                        if not self._start_worker():
                            print("❌ 重启Celery Worker失败")
                    
                    # 每30秒检查一次
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"❌ 监控线程异常: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def get_status(self) -> dict:
        """获取服务状态"""
        status = {
            'running': self.running,
            'beat_running': self.beat_process and self.beat_process.poll() is None,
            'worker_running': self.worker_process and self.worker_process.poll() is None,
            'redis_available': self._check_redis()
        }
        return status

# 全局管理器实例
celery_manager = CeleryManager()

def start_celery_with_app():
    """在Flask应用启动时启动Celery"""
    celery_manager.start_celery_services()

def stop_celery_with_app():
    """在Flask应用关闭时停止Celery"""
    celery_manager.stop_celery_services()

def get_celery_status():
    """获取Celery状态"""
    return celery_manager.get_status()
