#!/usr/bin/env python3
"""
泰摸鱼吧 - 统一日志按钮功能演示
展示如何在现有日志界面中访问统一日志功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.unified_log import UnifiedLog, LogLevel
from app.utils.structlog_config import get_auth_logger, get_db_logger, get_api_logger


def demo_unified_logs():
    """演示统一日志功能"""
    print("🎯 泰摸鱼吧统一日志按钮功能演示")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # 生成一些演示日志
        print("📝 生成演示日志...")
        
        # 认证日志
        auth_logger = get_auth_logger()
        auth_logger.info("用户登录成功", user_id=123, username="admin", ip="192.168.1.100")
        auth_logger.warning("登录失败", username="hacker", ip="192.168.1.200", reason="密码错误")
        
        # 数据库日志
        db_logger = get_db_logger()
        db_logger.info("查询执行", query="SELECT * FROM users", duration=0.5, rows=100)
        db_logger.error("连接失败", database="mysql", error="Connection timeout")
        
        # API日志
        api_logger = get_api_logger()
        api_logger.info("API请求", endpoint="/api/users", method="GET", status_code=200)
        api_logger.error("API错误", endpoint="/api/accounts", method="POST", status_code=500, error="Validation failed")
        
        # 等待异步写入完成
        time.sleep(3)
        
        # 查询日志统计
        stats = UnifiedLog.get_log_statistics(hours=1)
        print(f"📊 日志统计:")
        print(f"   总日志数: {stats.get('total_logs', 0)}")
        print(f"   错误日志: {stats.get('error_count', 0)}")
        print(f"   警告日志: {stats.get('warning_count', 0)}")
        print(f"   信息日志: {stats.get('info_count', 0)}")
        
        # 查询最近的日志
        recent_logs = UnifiedLog.get_recent_logs(hours=1, limit=5)
        print(f"\n📋 最近5条日志:")
        for log in recent_logs:
            print(f"   [{log.level.value}] {log.module}: {log.message}")
        
        print(f"\n🎉 演示完成!")
        print(f"\n📱 现在您可以:")
        print(f"   1. 访问统一日志中心: http://localhost:5001/logs/")
        print(f"   2. 查看结构化日志")
        print(f"   3. 使用筛选器过滤日志")
        print(f"   4. 导出日志为CSV格式")
        print(f"   5. 查看日志统计信息")
        
        print(f"\n🔧 API端点:")
        print(f"   - 查询日志: http://localhost:5001/logs/api/structlog/search")
        print(f"   - 获取统计: http://localhost:5001/logs/api/structlog/stats")
        print(f"   - 获取模块: http://localhost:5001/logs/api/structlog/modules")
        print(f"   - 导出日志: http://localhost:5001/logs/api/structlog/export")


if __name__ == "__main__":
    demo_unified_logs()
