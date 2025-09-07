# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 数据库连接池管理
"""

import threading
import time
from typing import Dict, Any, Optional
from queue import Queue, Empty
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class ConnectionPool:
    """数据库连接池"""
    
    def __init__(self, max_connections=10, timeout=30):
        self.max_connections = max_connections
        self.timeout = timeout
        self.pools = {}  # {instance_id: Queue}
        self.locks = {}  # {instance_id: Lock}
        self.connection_counts = {}  # {instance_id: int}
        self._lock = threading.Lock()
    
    def get_connection(self, instance_id: int, connection_factory):
        """获取数据库连接"""
        with self._lock:
            if instance_id not in self.pools:
                self.pools[instance_id] = Queue(maxsize=self.max_connections)
                self.locks[instance_id] = threading.Lock()
                self.connection_counts[instance_id] = 0
        
        pool = self.pools[instance_id]
        lock = self.locks[instance_id]
        
        try:
            # 尝试从池中获取连接
            connection = pool.get(timeout=self.timeout)
            logger.debug(f"从连接池获取连接: instance_id={instance_id}")
            return connection
        except Empty:
            # 池中没有可用连接，创建新连接
            with lock:
                if self.connection_counts[instance_id] < self.max_connections:
                    try:
                        connection = connection_factory()
                        self.connection_counts[instance_id] += 1
                        logger.debug(f"创建新连接: instance_id={instance_id}, count={self.connection_counts[instance_id]}")
                        return connection
                    except Exception as e:
                        logger.error(f"创建连接失败: {e}")
                        raise
                else:
                    raise Exception(f"连接池已满，无法创建新连接: instance_id={instance_id}")
    
    def return_connection(self, instance_id: int, connection):
        """归还数据库连接"""
        if instance_id in self.pools:
            try:
                self.pools[instance_id].put(connection, timeout=1)
                logger.debug(f"归还连接到池: instance_id={instance_id}")
            except Exception as e:
                logger.warning(f"归还连接失败: {e}")
                # 连接可能已损坏，关闭它
                try:
                    connection.close()
                except:
                    pass
                with self._lock:
                    if instance_id in self.connection_counts:
                        self.connection_counts[instance_id] -= 1
    
    def close_connection(self, instance_id: int, connection):
        """关闭数据库连接"""
        try:
            connection.close()
            logger.debug(f"关闭连接: instance_id={instance_id}")
        except Exception as e:
            logger.warning(f"关闭连接失败: {e}")
        finally:
            with self._lock:
                if instance_id in self.connection_counts:
                    self.connection_counts[instance_id] -= 1
    
    def close_all_connections(self, instance_id: int = None):
        """关闭所有连接"""
        if instance_id:
            # 关闭特定实例的所有连接
            if instance_id in self.pools:
                pool = self.pools[instance_id]
                while not pool.empty():
                    try:
                        conn = pool.get_nowait()
                        conn.close()
                    except:
                        pass
                with self._lock:
                    self.connection_counts[instance_id] = 0
        else:
            # 关闭所有连接
            for instance_id in list(self.pools.keys()):
                self.close_all_connections(instance_id)
    
    @contextmanager
    def get_connection_context(self, instance_id: int, connection_factory):
        """连接上下文管理器"""
        connection = None
        try:
            connection = self.get_connection(instance_id, connection_factory)
            yield connection
        finally:
            if connection:
                self.return_connection(instance_id, connection)
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取连接池状态"""
        status = {}
        with self._lock:
            for instance_id, pool in self.pools.items():
                status[instance_id] = {
                    'max_connections': self.max_connections,
                    'current_connections': self.connection_counts.get(instance_id, 0),
                    'available_connections': pool.qsize(),
                    'utilization': self.connection_counts.get(instance_id, 0) / self.max_connections * 100
                }
        return status

# 全局连接池实例
connection_pool = ConnectionPool()
