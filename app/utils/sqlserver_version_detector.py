"""
SQL Server版本检测工具
支持SQL Server 2005-2022版本检测和兼容性处理
"""

import re
from typing import Dict, Optional, Tuple


class SQLServerVersionDetector:
    """SQL Server版本检测器"""

    # SQL Server版本映射表
    VERSION_MAP = {
        # 版本号 -> (版本名称, 年份, 支持的功能)
        "8.00": ("SQL Server 2000", 2000, ["basic"]),
        "9.00": ("SQL Server 2005", 2005, ["basic", "xml", "cte"]),
        "10.00": ("SQL Server 2008", 2008, ["basic", "xml", "cte", "merger"]),
        "10.50": (
            "SQL Server 2008 R2",
            2010,
            ["basic", "xml", "cte", "merger", "compression"],
        ),
        "11.00": (
            "SQL Server 2012",
            2012,
            ["basic", "xml", "cte", "merger", "compression", "columnstore"],
        ),
        "12.00": (
            "SQL Server 2014",
            2014,
            [
                "basic",
                "xml",
                "cte",
                "merger",
                "compression",
                "columnstore",
                "memory_optimized",
            ],
        ),
        "13.00": (
            "SQL Server 2016",
            2016,
            [
                "basic",
                "xml",
                "cte",
                "merger",
                "compression",
                "columnstore",
                "memory_optimized",
                "json",
                "temporal",
            ],
        ),
        "14.00": (
            "SQL Server 2017",
            2017,
            [
                "basic",
                "xml",
                "cte",
                "merger",
                "compression",
                "columnstore",
                "memory_optimized",
                "json",
                "temporal",
                "graph",
            ],
        ),
        "15.00": (
            "SQL Server 2019",
            2019,
            [
                "basic",
                "xml",
                "cte",
                "merger",
                "compression",
                "columnstore",
                "memory_optimized",
                "json",
                "temporal",
                "graph",
                "big_data",
            ],
        ),
        "16.00": (
            "SQL Server 2022",
            2022,
            [
                "basic",
                "xml",
                "cte",
                "merger",
                "compression",
                "columnstore",
                "memory_optimized",
                "json",
                "temporal",
                "graph",
                "big_data",
                "ledger",
            ],
        ),
    }

    @classmethod
    def detect_version(cls, version_string: str) -> Dict[str, any]:
        """
        检测SQL Server版本

        Args:
            version_string: SQL Server版本字符串 (如 "Microsoft SQL Server 2019 (RTM-CU18) (KB5003279) - 15.0.4261.1 (X64)")

        Returns:
            包含版本信息的字典
        """
        if not version_string:
            return cls._unknown_version()

        # 提取版本号
        version_match = re.search(r"(\d+\.\d+)", version_string)
        if not version_match:
            return cls._unknown_version()

        version_number = version_match.group(1)

        # 查找匹配的版本
        for ver, (name, year, features) in cls.VERSION_MAP.items():
            if version_string.startswith(ver) or version_number.startswith(
                ver.split(".")[0]
            ):
                return {
                    "version_number": version_number,
                    "version_name": name,
                    "year": year,
                    "features": features,
                    "is_modern": year >= 2012,
                    "is_legacy": year < 2008,
                    "supports_json": "json" in features,
                    "supports_temporal": "temporal" in features,
                    "supports_graph": "graph" in features,
                    "supports_columnstore": "columnstore" in features,
                    "supports_memory_optimized": "memory_optimized" in features,
                }

        # 如果没找到精确匹配，尝试根据年份推断
        year_match = re.search(r"(\d{4})", version_string)
        if year_match:
            year = int(year_match.group(1))
            if 2000 <= year <= 2022:
                return {
                    "version_number": version_number,
                    "version_name": f"SQL Server {year}",
                    "year": year,
                    "features": ["basic"],
                    "is_modern": year >= 2012,
                    "is_legacy": year < 2008,
                    "supports_json": year >= 2016,
                    "supports_temporal": year >= 2016,
                    "supports_graph": year >= 2017,
                    "supports_columnstore": year >= 2012,
                    "supports_memory_optimized": year >= 2014,
                }

        return cls._unknown_version()

    @classmethod
    def _unknown_version(cls) -> Dict[str, any]:
        """返回未知版本信息"""
        return {
            "version_number": "unknown",
            "version_name": "Unknown SQL Server",
            "year": None,
            "features": ["basic"],
            "is_modern": False,
            "is_legacy": True,
            "supports_json": False,
            "supports_temporal": False,
            "supports_graph": False,
            "supports_columnstore": False,
            "supports_memory_optimized": False,
        }

    @classmethod
    def get_recommended_driver(cls, version_info: Dict[str, any]) -> str:
        """
        根据版本信息推荐最佳驱动

        Args:
            version_info: 版本信息字典

        Returns:
            推荐的驱动名称
        """
        if version_info["is_legacy"]:
            return "pymssql"  # 老版本推荐pymssql
        elif version_info["is_modern"]:
            return "pyodbc"  # 现代版本推荐pyodbc
        else:
            return "pyodbc"  # 默认使用pyodbc

    @classmethod
    def get_connection_string_template(
        cls, version_info: Dict[str, any], driver: str
    ) -> str:
        """
        根据版本和驱动获取连接字符串模板

        Args:
            version_info: 版本信息字典
            driver: 驱动名称

        Returns:
            连接字符串模板
        """
        if driver == "pyodbc":
            if version_info["is_legacy"]:
                # 老版本使用传统驱动
                return "DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
            else:
                # 现代版本使用ODBC Driver
                return "DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"
        elif driver == "pymssql":
            # pymssql连接参数
            return "server={server};port={port};user={username};password={password};database={database};tds_version=7.4"
        else:
            return ""

    @classmethod
    def get_compatible_features(cls, version_info: Dict[str, any]) -> list[str]:
        """
        获取版本支持的功能列表

        Args:
            version_info: 版本信息字典

        Returns:
            支持的功能列表
        """
        features = []

        if version_info["supports_json"]:
            features.append("JSON数据类型")
        if version_info["supports_temporal"]:
            features.append("时态表")
        if version_info["supports_graph"]:
            features.append("图数据库")
        if version_info["supports_columnstore"]:
            features.append("列存储索引")
        if version_info["supports_memory_optimized"]:
            features.append("内存优化表")

        return features


def test_version_detection():
    """测试版本检测功能"""
    test_versions = [
        "Microsoft SQL Server 2019 (RTM-CU18) (KB5003279) - 15.0.4261.1 (X64)",
        "Microsoft SQL Server 2016 (SP2-CU17) (KB5001092) - 13.0.5888.11 (X64)",
        "Microsoft SQL Server 2012 (SP4-GDR) (KB4583465) - 11.0.7507.2 (X64)",
        "Microsoft SQL Server 2008 R2 (SP3-GDR) (KB4583465) - 10.50.6560.0 (X64)",
        "Microsoft SQL Server 2005 (SP4) - 9.00.5000.00 (X64)",
    ]

    detector = SQLServerVersionDetector()

    for version_str in test_versions:
        print(f"\n版本字符串: {version_str}")
        info = detector.detect_version(version_str)
        print(f"检测结果: {info['version_name']} ({info['year']})")
        print(f"推荐驱动: {detector.get_recommended_driver(info)}")
        print(f"支持功能: {', '.join(detector.get_compatible_features(info))}")


if __name__ == "__main__":
    test_version_detection()
