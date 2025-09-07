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
        关闭数据库连接（改进版本）
        
        Args:
            instance: 数据库实例
        """
        try:
            if instance.id in self.connections:
                conn = self.connections[instance.id]
                if conn:
                    # 确保连接被正确关闭
                    if hasattr(conn, 'close'):
                        conn.close()
                    elif hasattr(conn, 'disconnect'):
                        conn.disconnect()
                del self.connections[instance.id]
                log_operation('database_disconnect', details={
                    'instance_id': instance.id,
                    'db_type': instance.db_type
                })
        except Exception as e:
            log_error(e, context={'instance_id': instance.id})
        finally:
            # 确保连接被清理
            if instance.id in self.connections:
                del self.connections[instance.id]
    
    def close_all_connections(self):
        """关闭所有数据库连接（改进版本）"""
        connection_ids = list(self.connections.keys())
        for instance_id in connection_ids:
            try:
                conn = self.connections[instance_id]
                if conn:
                    # 确保连接被正确关闭
                    if hasattr(conn, 'close'):
                        conn.close()
                    elif hasattr(conn, 'disconnect'):
                        conn.disconnect()
            except Exception as e:
                log_error(e, context={'instance_id': instance_id})
        self.connections.clear()
    
    def get_connection_count(self):
        """
        获取当前连接数
        
        Returns:
            int: 连接数
        """
        return len(self.connections)
    
    def cleanup_stale_connections(self):
        """
        清理过期的连接
        """
        stale_connections = []
        for instance_id, conn in self.connections.items():
            try:
                # 测试连接是否仍然有效
                if hasattr(conn, 'ping'):
                    conn.ping()
                elif hasattr(conn, 'execute'):
                    conn.execute('SELECT 1')
            except Exception:
                stale_connections.append(instance_id)
        
        # 移除过期连接
        for instance_id in stale_connections:
            try:
                conn = self.connections[instance_id]
                if hasattr(conn, 'close'):
                    conn.close()
                del self.connections[instance_id]
            except Exception:
                pass
    
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
        执行SQL查询（安全版本）
        
        Args:
            instance: 数据库实例
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Dict: 查询结果
        """
        try:
            # 安全检查：防止SQL注入
            if not self._is_safe_query(query):
                return {
                    'success': False,
                    'error': '查询包含不安全的操作，已被阻止'
                }
            
            conn = self.get_connection(instance)
            if not conn:
                return {
                    'success': False,
                    'error': '无法获取数据库连接'
                }
            
            cursor = conn.cursor()
            
            # 使用参数化查询防止SQL注入
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
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
    
    def _is_safe_query(self, query: str) -> bool:
        """
        检查查询是否安全
        
        Args:
            query: SQL查询语句
            
        Returns:
            bool: 是否安全
        """
        # 转换为大写进行检查
        query_upper = query.upper().strip()
        
        # 危险操作列表
        dangerous_operations = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE',
            'EXEC', 'EXECUTE', 'SP_', 'XP_', 'BULK', 'BULKINSERT',
            'UNION', '--', '/*', '*/', ';', 'XP_CMDSHELL', 'SP_EXECUTESQL'
        ]
        
        # 检查是否包含危险操作
        for operation in dangerous_operations:
            if operation in query_upper:
                return False
        
        # 只允许SELECT查询（用于数据查看）
        if not query_upper.startswith('SELECT'):
            return False
        
        # 检查查询长度（防止过长的查询）
        if len(query) > 10000:
            return False
        
        return True