"""
泰摸鱼吧 - 数据库驱动管理
处理不同平台的数据库驱动兼容性问题
"""

import platform
import sys
from typing import Dict, Any, Optional


class DatabaseDriverManager:
    """数据库驱动管理器"""

    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.available_drivers = self._detect_available_drivers()

    def _detect_available_drivers(self) -> Dict[str, bool]:
        """检测可用的数据库驱动"""
        drivers = {
            "mysql": False,
            "postgresql": False,
            "sqlserver": False,
            "oracle": False,
            "odbc": False,
        }

        # MySQL驱动
        try:
            import pymysql

            drivers["mysql"] = True
        except ImportError:
            pass

        # PostgreSQL驱动
        try:
            import psycopg

            drivers["postgresql"] = True
        except ImportError:
            pass

        # SQL Server驱动
        try:
            import pymssql

            drivers["sqlserver"] = True
        except ImportError:
            pass

        # Oracle驱动
        try:
            import oracledb

            drivers["oracle"] = True
        except ImportError:
            pass

        # ODBC驱动
        try:
            import pyodbc

            drivers["odbc"] = True
        except ImportError:
            pass

        return drivers

    def get_connection_string(
        self,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str = None,
    ) -> Optional[str]:
        """
        获取数据库连接字符串

        Args:
            db_type: 数据库类型
            host: 主机地址
            port: 端口号
            username: 用户名
            password: 密码
            database: 数据库名

        Returns:
            str: 连接字符串
        """
        if db_type.lower() == "mysql":
            if self.available_drivers["mysql"]:
                return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database or 'mysql'}"
            else:
                return None

        elif db_type.lower() == "postgresql":
            if self.available_drivers["postgresql"]:
                return f"postgresql://{username}:{password}@{host}:{port}/{database or 'postgres'}"
            else:
                return None

        elif db_type.lower() == "sql server":
            if self.available_drivers["sqlserver"]:
                return f"mssql+pymssql://{username}:{password}@{host}:{port}/{database or 'master'}"
            elif self.available_drivers["odbc"]:
                # 使用ODBC连接SQL Server
                return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database or 'master'}?driver=ODBC+Driver+17+for+SQL+Server"
            else:
                return None

        elif db_type.lower() == "oracle":
            if self.available_drivers["oracle"]:
                return f"oracle+oracledb://{username}:{password}@{host}:{port}/{database or 'ORCL'}"
            else:
                return None

        return None

    def get_connection_method(self, db_type: str) -> str:
        """
        获取推荐的连接方法

        Args:
            db_type: 数据库类型

        Returns:
            str: 连接方法描述
        """
        if db_type.lower() == "mysql":
            if self.available_drivers["mysql"]:
                return "PyMySQL (推荐)"
            else:
                return "需要安装: pip install PyMySQL"

        elif db_type.lower() == "postgresql":
            if self.available_drivers["postgresql"]:
                return "psycopg (推荐)"
            else:
                return "需要安装: pip install psycopg[binary]"

        elif db_type.lower() == "sql server":
            if self.available_drivers["sqlserver"]:
                return "pymssql (推荐)"
            elif self.available_drivers["odbc"]:
                return "pyodbc (替代方案)"
            else:
                return "需要安装: pip install pymssql 或 pip install pyodbc"

        elif db_type.lower() == "oracle":
            if self.available_drivers["oracle"]:
                return "python-oracledb (推荐)"
            else:
                return "需要安装: pip install python-oracledb"

        return "未知数据库类型"

    def get_installation_guide(self) -> Dict[str, str]:
        """获取安装指南"""
        guide = {
            "mysql": "pip install PyMySQL",
            "postgresql": "pip install psycopg[binary]",
            "sqlserver": "pip install pymssql (或 pip install pyodbc)",
            "oracle": "pip install python-oracledb",
            "odbc": "pip install pyodbc + 系统ODBC驱动",
        }

        # 添加平台特定说明
        if self.system == "darwin":  # macOS
            guide["sqlserver"] += " (在ARM64 Mac上可能编译失败，建议使用pyodbc)"
            guide[
                "oracle"
            ] += " (python-oracledb支持Thin模式，无需Oracle Instant Client)"

        return guide

    def get_status_report(self) -> str:
        """获取状态报告"""
        report = f"数据库驱动状态报告 (系统: {self.system} {self.architecture})\n"
        report += "=" * 50 + "\n"

        for driver, available in self.available_drivers.items():
            status = "✅ 可用" if available else "❌ 不可用"
            report += f"{driver.upper()}: {status}\n"

        report += "\n安装指南:\n"
        guide = self.get_installation_guide()
        for db_type, command in guide.items():
            report += f"  {db_type}: {command}\n"

        return report


# 创建全局实例
driver_manager = DatabaseDriverManager()
