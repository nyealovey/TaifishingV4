"""
泰摸鱼吧 - 数据库连接管理服务
"""

import pymysql
from typing import Dict, Any, Optional, List
from app.models import Instance, Credential
from app.utils.logger import log_operation, log_error

class DatabaseService:
    """数据库连接管理服务"""
    
    def __init__(self):
        self.connections = {}
    
    def test_connection(self, instance: Instance) -> Dict[str, Any]:
        """
        测试数据库连接
        
        Args:
            instance: 数据库实例
            
        Returns:
            Dict: 测试结果
        """
        try:
            if instance.db_type == 'postgresql':
                return self._test_postgresql_connection(instance)
            elif instance.db_type == 'mysql':
                return self._test_mysql_connection(instance)
            elif instance.db_type == 'sqlserver':
                return self._test_sqlserver_connection(instance)
            elif instance.db_type == 'oracle':
                return self._test_oracle_connection(instance)
            else:
                return {
                    'success': False,
                    'error': f'不支持的数据库类型: {instance.db_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'连接测试失败: {str(e)}'
            }
    
    def sync_accounts(self, instance: Instance) -> Dict[str, Any]:
        """
        同步账户信息
        
        Args:
            instance: 数据库实例
            
        Returns:
            Dict: 同步结果
        """
        try:
            # 这里实现账户同步逻辑
            # 暂时返回成功
            return {
                'success': True,
                'message': '账户同步功能开发中',
                'synced_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'账户同步失败: {str(e)}'
            }
    
    def _test_postgresql_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试PostgreSQL连接"""
        return {
            'success': False,
            'error': 'PostgreSQL驱动未安装，请安装psycopg2'
        }
    
    def _test_mysql_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试MySQL连接"""
        try:
            conn = pymysql.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name,
                user=instance.credential.username if instance.credential else '',
                password=instance.credential.password if instance.credential else ''
            )
            conn.close()
            return {
                'success': True,
                'message': 'MySQL连接成功'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'MySQL连接失败: {str(e)}'
            }
    
    def _test_sqlserver_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试SQL Server连接"""
        return {
            'success': False,
            'error': 'SQL Server驱动未安装，请安装pymssql'
        }
    
    def _test_oracle_connection(self, instance: Instance) -> Dict[str, Any]:
        """测试Oracle连接"""
        return {
            'success': False,
            'error': 'Oracle驱动未安装，请安装cx_Oracle'
        }

    def get_connection(self, instance: Instance) -> Optional[Any]:
        """
        获取数据库连接
        
        Args:
            instance: 数据库实例
            
        Returns:
            Any: 数据库连接对象
        """
        try:
            if instance.db_type == 'mysql':
                return self._get_mysql_connection(instance)
            else:
                log_error(f"不支持的数据库类型: {instance.db_type}")
                return None
        except Exception as e:
            log_error(e, context={'instance_id': instance.id, 'instance_name': instance.name})
            return None
    
    def _get_mysql_connection(self, instance: Instance) -> Optional[Any]:
        """获取MySQL连接"""
        try:
            conn = pymysql.connect(
                host=instance.host,
                port=instance.port,
                database=instance.database_name,
                user=instance.credential.username if instance.credential else '',
                password=instance.credential.password if instance.credential else '',
                charset='utf8mb4',
                autocommit=True
            )
            log_operation('database_connect', details={
                'instance_id': instance.id,
                'db_type': 'MySQL',
                'host': instance.host
            })
            return conn
        except Exception as e:
            log_error(e, context={'instance_id': instance.id, 'db_type': 'MySQL'})
            return None
    
    def close_connection(self, instance: Instance):
        """
        关闭数据库连接
        
        Args:
            instance: 数据库实例
        """
        try:
            if instance.id in self.connections:
                self.connections[instance.id].close()
                del self.connections[instance.id]
                log_operation('database_disconnect', details={
                    'instance_id': instance.id,
                    'db_type': instance.db_type
                })
        except Exception as e:
            log_error(e, context={'instance_id': instance.id})
    
    def close_all_connections(self):
        """关闭所有数据库连接"""
        for instance_id, conn in self.connections.items():
            try:
                conn.close()
            except Exception as e:
                log_error(e, context={'instance_id': instance_id})
        self.connections.clear()
    
    def get_connection_status(self, instance: Instance) -> Dict[str, Any]:
        """
        获取连接状态
        
        Args:
            instance: 数据库实例
            
        Returns:
            Dict: 连接状态信息
        """
        try:
            if instance.id in self.connections:
                conn = self.connections[instance.id]
                # 尝试执行简单查询测试连接
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return {
                    'connected': True,
                    'status': 'active',
                    'message': '连接正常'
                }
            else:
                return {
                    'connected': False,
                    'status': 'disconnected',
                    'message': '未连接'
                }
        except Exception as e:
            return {
                'connected': False,
                'status': 'error',
                'message': f'连接错误: {str(e)}'
            }
    
    def execute_query(self, instance: Instance, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        执行SQL查询
        
        Args:
            instance: 数据库实例
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Dict: 查询结果
        """
        try:
            conn = self.get_connection(instance)
            if not conn:
                return {
                    'success': False,
                    'error': '无法获取数据库连接'
                }
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                return {
                    'success': True,
                    'data': results,
                    'columns': columns,
                    'row_count': len(results)
                }
            else:
                conn.commit()
                cursor.close()
                return {
                    'success': True,
                    'message': '查询执行成功',
                    'affected_rows': cursor.rowcount
                }
                
        except Exception as e:
            log_error(e, context={
                'instance_id': instance.id,
                'query': query,
                'params': params
            })
            return {
                'success': False,
                'error': f'查询执行失败: {str(e)}'
            }