#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库连接工厂
提供统一的数据库连接创建和管理功能
"""

import logging
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from app.models.instance import Instance
from app.utils.database_type_utils import DatabaseTypeUtils
from app.utils.enhanced_logger import log_error, log_operation


class DatabaseConnection(ABC):
    """数据库连接抽象基类"""
    
    def __init__(self, instance: Instance):
        self.instance = instance
        self.connection = None
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """断开数据库连接"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行查询"""
        pass
    
    @abstractmethod
    def get_version(self) -> Optional[str]:
        """获取数据库版本"""
        pass


class MySQLConnection(DatabaseConnection):
    """MySQL数据库连接"""
    
    def connect(self) -> bool:
        """建立MySQL连接"""
        try:
            import pymysql
            
            # 获取连接信息
            password = (
                self.instance.credential.get_plain_password() 
                if self.instance.credential else ""
            )
            
            self.connection = pymysql.connect(
                host=self.instance.host,
                port=self.instance.port,
                database=self.instance.database_name or DatabaseTypeUtils.get_database_type_config("mysql").default_schema or "",
                user=self.instance.credential.username if self.instance.credential else "",
                password=password,
                charset="utf8mb4",
                autocommit=True,
                connect_timeout=30,
                read_timeout=60,
                write_timeout=60,
                sql_mode="TRADITIONAL",
            )
            self.is_connected = True
            return True
            
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "db_type": "MySQL"})
            return False
    
    def disconnect(self) -> None:
        """断开MySQL连接"""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                log_error(e, context={"instance_id": self.instance.id, "db_type": "MySQL"})
            finally:
                self.connection = None
                self.is_connected = False
    
    def test_connection(self) -> Dict[str, Any]:
        """测试MySQL连接"""
        try:
            if not self.connect():
                return {"success": False, "error": "无法建立连接"}
            
            version = self.get_version()
            return {
                "success": True,
                "message": f'MySQL连接成功 (主机: {self.instance.host}:{self.instance.port}, 版本: {version or "未知"})',
                "database_version": version,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.disconnect()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行MySQL查询"""
        if not self.is_connected:
            if not self.connect():
                raise Exception("无法建立数据库连接")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def get_version(self) -> Optional[str]:
        """获取MySQL版本"""
        try:
            result = self.execute_query("SELECT VERSION()")
            return result[0][0] if result else None
        except Exception:
            return None


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL数据库连接"""
    
    def connect(self) -> bool:
        """建立PostgreSQL连接"""
        try:
            import psycopg
            
            # 获取连接信息
            password = (
                self.instance.credential.get_plain_password() 
                if self.instance.credential else ""
            )
            
            self.connection = psycopg.connect(
                host=self.instance.host,
                port=self.instance.port,
                dbname=self.instance.database_name or DatabaseTypeUtils.get_database_type_config("postgresql").default_schema or "postgres",
                user=self.instance.credential.username if self.instance.credential else "",
                password=password,
                connect_timeout=30,
            )
            self.is_connected = True
            return True
            
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "db_type": "PostgreSQL"})
            return False
    
    def disconnect(self) -> None:
        """断开PostgreSQL连接"""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                log_error(e, context={"instance_id": self.instance.id, "db_type": "PostgreSQL"})
            finally:
                self.connection = None
                self.is_connected = False
    
    def test_connection(self) -> Dict[str, Any]:
        """测试PostgreSQL连接"""
        try:
            if not self.connect():
                return {"success": False, "error": "无法建立连接"}
            
            version = self.get_version()
            return {
                "success": True,
                "message": f'PostgreSQL连接成功 (主机: {self.instance.host}:{self.instance.port}, 版本: {version or "未知"})',
                "database_version": version,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.disconnect()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行PostgreSQL查询"""
        if not self.is_connected:
            if not self.connect():
                raise Exception("无法建立数据库连接")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def get_version(self) -> Optional[str]:
        """获取PostgreSQL版本"""
        try:
            result = self.execute_query("SELECT version()")
            return result[0][0] if result else None
        except Exception:
            return None


class SQLServerConnection(DatabaseConnection):
    """SQL Server数据库连接"""
    
    def connect(self) -> bool:
        """建立SQL Server连接"""
        try:
            import pymssql
            
            # 获取连接信息
            password = (
                self.instance.credential.get_plain_password() 
                if self.instance.credential else ""
            )
            
            database_name = self.instance.database_name or DatabaseTypeUtils.get_database_type_config('sqlserver').default_schema or 'master'
            
            self.connection = pymssql.connect(
                server=self.instance.host,
                port=self.instance.port,
                user=self.instance.credential.username if self.instance.credential else "",
                password=password,
                database=database_name,
                timeout=30
            )
            self.is_connected = True
            return True
            
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "db_type": "SQL Server"})
            return False
    
    def disconnect(self) -> None:
        """断开SQL Server连接"""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                log_error(e, context={"instance_id": self.instance.id, "db_type": "SQL Server"})
            finally:
                self.connection = None
                self.is_connected = False
    
    def test_connection(self) -> Dict[str, Any]:
        """测试SQL Server连接"""
        try:
            if not self.connect():
                return {"success": False, "error": "无法建立连接"}
            
            version = self.get_version()
            return {
                "success": True,
                "message": f'SQL Server连接成功 (主机: {self.instance.host}:{self.instance.port}, 版本: {version or "未知"})',
                "database_version": version,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.disconnect()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行SQL Server查询"""
        if not self.is_connected:
            if not self.connect():
                raise Exception("无法建立数据库连接")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def get_version(self) -> Optional[str]:
        """获取SQL Server版本"""
        try:
            result = self.execute_query("SELECT @@VERSION")
            return result[0][0] if result else None
        except Exception:
            return None


class OracleConnection(DatabaseConnection):
    """Oracle数据库连接"""
    
    def connect(self) -> bool:
        """建立Oracle连接"""
        try:
            import oracledb
            
            # 获取连接信息
            password = (
                self.instance.credential.get_plain_password() 
                if self.instance.credential else ""
            )
            
            # 构建连接字符串
            database_name = self.instance.database_name or DatabaseTypeUtils.get_database_type_config("oracle").default_schema or "ORCL"
            
            if "." in database_name:
                # 服务名格式
                dsn = f"{self.instance.host}:{self.instance.port}/{database_name}"
            else:
                # SID格式
                dsn = f"{self.instance.host}:{self.instance.port}:{database_name}"
            
            # 尝试使用thin模式连接（不需要Oracle客户端）
            try:
                self.connection = oracledb.connect(
                    user=self.instance.credential.username if self.instance.credential else "",
                    password=password,
                    dsn=dsn,
                    mode=oracledb.MODE_SYSDBA if self.instance.credential.username.upper() == 'SYS' else oracledb.DEFAULT_AUTH
                )
            except Exception:
                # 如果thin模式失败，尝试使用thick模式
                try:
                    # 初始化Oracle客户端
                    oracledb.init_oracle_client()
                    self.connection = oracledb.connect(
                        user=self.instance.credential.username if self.instance.credential else "",
                        password=password,
                        dsn=dsn,
                        mode=oracledb.MODE_SYSDBA if self.instance.credential.username.upper() == 'SYS' else oracledb.DEFAULT_AUTH
                    )
                except Exception as e2:
                    # 如果都失败，抛出原始错误
                    raise e2
            
            self.is_connected = True
            return True
            
        except Exception as e:
            log_error(e, context={"instance_id": self.instance.id, "db_type": "Oracle"})
            return False
    
    def disconnect(self) -> None:
        """断开Oracle连接"""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                log_error(e, context={"instance_id": self.instance.id, "db_type": "Oracle"})
            finally:
                self.connection = None
                self.is_connected = False
    
    def test_connection(self) -> Dict[str, Any]:
        """测试Oracle连接"""
        try:
            if not self.connect():
                return {"success": False, "error": "无法建立连接"}
            
            version = self.get_version()
            return {
                "success": True,
                "message": f'Oracle连接成功 (主机: {self.instance.host}:{self.instance.port}, 版本: {version or "未知"})',
                "database_version": version,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.disconnect()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """执行Oracle查询"""
        if not self.is_connected:
            if not self.connect():
                raise Exception("无法建立数据库连接")
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def get_version(self) -> Optional[str]:
        """获取Oracle版本"""
        try:
            result = self.execute_query("SELECT * FROM v$version WHERE rownum = 1")
            return result[0][0] if result else None
        except Exception:
            return None


class ConnectionFactory:
    """数据库连接工厂"""
    
    # 数据库类型到连接类的映射
    CONNECTION_CLASSES = {
        "mysql": MySQLConnection,
        "postgresql": PostgreSQLConnection,
        "sqlserver": SQLServerConnection,
        "oracle": OracleConnection,
    }
    
    @staticmethod
    def create_connection(instance: Instance) -> Optional[DatabaseConnection]:
        """
        创建数据库连接
        
        Args:
            instance: 数据库实例
            
        Returns:
            数据库连接对象，如果类型不支持则返回None
        """
        db_type = instance.db_type.lower()
        
        if db_type not in ConnectionFactory.CONNECTION_CLASSES:
            log_error(
                f"不支持的数据库类型: {db_type}",
                context={"instance_id": instance.id, "db_type": db_type}
            )
            return None
        
        connection_class = ConnectionFactory.CONNECTION_CLASSES[db_type]
        return connection_class(instance)
    
    @staticmethod
    def test_connection(instance: Instance) -> Dict[str, Any]:
        """
        测试数据库连接
        
        Args:
            instance: 数据库实例
            
        Returns:
            测试结果字典
        """
        connection = ConnectionFactory.create_connection(instance)
        if not connection:
            return {
                "success": False,
                "error": f"不支持的数据库类型: {instance.db_type}"
            }
        
        return connection.test_connection()
    
    @staticmethod
    def get_supported_types() -> list:
        """
        获取支持的数据库类型列表
        
        Returns:
            支持的数据库类型列表
        """
        return list(ConnectionFactory.CONNECTION_CLASSES.keys())
    
    @staticmethod
    def is_type_supported(db_type: str) -> bool:
        """
        检查数据库类型是否支持
        
        Args:
            db_type: 数据库类型名称
            
        Returns:
            是否支持该数据库类型
        """
        return db_type.lower() in ConnectionFactory.CONNECTION_CLASSES
