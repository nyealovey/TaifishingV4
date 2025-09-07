# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 数据库连接上下文管理器
"""

import logging
from contextlib import contextmanager
from typing import Optional, Any, Generator
from app.services.database_service import DatabaseService
from app.models.instance import Instance

logger = logging.getLogger(__name__)

class DatabaseContextManager:
    """数据库连接上下文管理器"""
    
    def __init__(self):
        self.db_service = DatabaseService()
    
    @contextmanager
    def get_connection(self, instance: Instance) -> Generator[Optional[Any], None, None]:
        """
        获取数据库连接的上下文管理器
        
        Args:
            instance: 数据库实例
            
        Yields:
            Optional[Any]: 数据库连接对象
        """
        connection = None
        try:
            connection = self.db_service.get_connection(instance)
            if not connection:
                logger.error(f"无法获取数据库连接: {instance.name}")
                yield None
                return
            
            logger.debug(f"获取数据库连接成功: {instance.name}")
            yield connection
            
        except Exception as e:
            logger.error(f"数据库连接上下文管理器错误: {e}")
            yield None
        finally:
            if connection:
                try:
                    self.db_service.close_connection(instance)
                    logger.debug(f"关闭数据库连接: {instance.name}")
                except Exception as e:
                    logger.warning(f"关闭数据库连接失败: {e}")
    
    @contextmanager
    def execute_query(self, instance: Instance, query: str, params: tuple = None) -> Generator[dict, None, None]:
        """
        执行查询的上下文管理器
        
        Args:
            instance: 数据库实例
            query: SQL查询
            params: 查询参数
            
        Yields:
            dict: 查询结果
        """
        try:
            result = self.db_service.execute_query(instance, query, params)
            yield result
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            yield {'success': False, 'error': str(e)}
    
    @contextmanager
    def transaction(self, instance: Instance) -> Generator[Optional[Any], None, None]:
        """
        数据库事务上下文管理器
        
        Args:
            instance: 数据库实例
            
        Yields:
            Optional[Any]: 数据库连接对象
        """
        connection = None
        try:
            connection = self.db_service.get_connection(instance)
            if not connection:
                logger.error(f"无法获取数据库连接进行事务: {instance.name}")
                yield None
                return
            
            # 开始事务
            if hasattr(connection, 'begin'):
                connection.begin()
            elif hasattr(connection, 'autocommit'):
                connection.autocommit = False
            
            logger.debug(f"开始数据库事务: {instance.name}")
            yield connection
            
            # 提交事务
            if hasattr(connection, 'commit'):
                connection.commit()
            logger.debug(f"提交数据库事务: {instance.name}")
            
        except Exception as e:
            # 回滚事务
            if connection:
                try:
                    if hasattr(connection, 'rollback'):
                        connection.rollback()
                    logger.debug(f"回滚数据库事务: {instance.name}")
                except Exception as rollback_error:
                    logger.error(f"回滚事务失败: {rollback_error}")
            
            logger.error(f"数据库事务错误: {e}")
            yield None
        finally:
            if connection:
                try:
                    # 恢复自动提交
                    if hasattr(connection, 'autocommit'):
                        connection.autocommit = True
                    self.db_service.close_connection(instance)
                except Exception as e:
                    logger.warning(f"清理数据库连接失败: {e}")

# 全局数据库上下文管理器
db_context = DatabaseContextManager()

# 便捷函数
@contextmanager
def get_db_connection(instance: Instance) -> Generator[Optional[Any], None, None]:
    """获取数据库连接的便捷函数"""
    with db_context.get_connection(instance) as conn:
        yield conn

@contextmanager
def execute_db_query(instance: Instance, query: str, params: tuple = None) -> Generator[dict, None, None]:
    """执行数据库查询的便捷函数"""
    with db_context.execute_query(instance, query, params) as result:
        yield result

@contextmanager
def db_transaction(instance: Instance) -> Generator[Optional[Any], None, None]:
    """数据库事务的便捷函数"""
    with db_context.transaction(instance) as conn:
        yield conn
