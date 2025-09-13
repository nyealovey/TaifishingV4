#!/usr/bin/env python3
"""
泰摸鱼吧 - 测试迁移后的日志系统
验证所有日志调用都已正确迁移到structlog模式
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.unified_log import UnifiedLog, LogLevel
from app.utils.structlog_config import (
    get_logger, log_info, log_warning, log_error, log_critical, log_debug,
    get_auth_logger, get_db_logger, get_sync_logger, get_api_logger, get_system_logger, get_task_logger
)


def test_basic_logging():
    """测试基础日志记录"""
    print("=== 测试基础日志记录 ===")
    
    # 基础日志
    log_info("这是一条信息日志")
    log_warning("这是一条警告日志")
    log_error("这是一条错误日志")
    log_debug("这是一条调试日志")
    log_critical("这是一条严重错误日志")
    
    print("✅ 基础日志记录完成")


def test_specialized_loggers():
    """测试专用日志记录器"""
    print("\n=== 测试专用日志记录器 ===")
    
    # 认证日志
    auth_logger = get_auth_logger()
    auth_logger.info("用户认证成功", user_id=123, method="password")
    auth_logger.warning("登录失败", username="test", ip="192.168.1.1")
    
    # 数据库日志
    db_logger = get_db_logger()
    db_logger.info("查询执行", query="SELECT * FROM users", duration=0.5, rows=100)
    db_logger.error("连接失败", database="mysql", error="Connection timeout")
    
    # 同步日志
    sync_logger = get_sync_logger()
    sync_logger.info("同步开始", task_id=1, instance="mysql-prod")
    sync_logger.warning("同步警告", task_id=1, message="部分数据同步失败")
    
    # API日志
    api_logger = get_api_logger()
    api_logger.info("API请求", endpoint="/api/users", method="GET", status_code=200)
    api_logger.error("API错误", endpoint="/api/users", status_code=500, error="Internal server error")
    
    # 系统日志
    system_logger = get_system_logger()
    system_logger.info("系统启动", version="1.0.0", environment="production")
    system_logger.critical("系统错误", component="database", error="Connection pool exhausted")
    
    # 任务日志
    task_logger = get_task_logger()
    task_logger.info("任务执行", task_name="sync_accounts", duration=30.5)
    task_logger.error("任务失败", task_name="sync_accounts", error="Database connection lost")
    
    print("✅ 专用日志记录器测试完成")


def test_contextual_logging():
    """测试带上下文的日志记录"""
    print("\n=== 测试带上下文的日志记录 ===")
    
    # 带额外信息的日志
    log_info("用户操作", user_id=123, action="login", ip_address="192.168.1.1")
    log_error("数据库连接失败", database="mysql", error="Connection timeout")
    log_warning("缓存未命中", cache_key="user:123", ttl=300)
    
    # 带异常信息的日志
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        log_error("除零错误", exception=e, context={"operation": "division"})
    
    print("✅ 上下文日志记录完成")


def test_database_storage():
    """测试数据库存储"""
    print("\n=== 测试数据库存储 ===")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 等待异步日志写入完成
            time.sleep(3)
            
            # 查询最近的日志
            recent_logs = UnifiedLog.get_recent_logs(hours=1, limit=20)
            print(f"📊 查询到 {len(recent_logs)} 条最近日志")
            
            # 按模块统计
            modules = {}
            for log in recent_logs:
                module = log.module
                modules[module] = modules.get(module, 0) + 1
            
            print("📈 按模块统计:")
            for module, count in modules.items():
                print(f"   {module}: {count} 条")
            
            # 按级别统计
            levels = {}
            for log in recent_logs:
                level = log.level.value
                levels[level] = levels.get(level, 0) + 1
            
            print("📊 按级别统计:")
            for level, count in levels.items():
                print(f"   {level}: {count} 条")
            
            # 查询错误日志
            error_logs = UnifiedLog.get_error_logs(hours=1, limit=10)
            print(f"❌ 查询到 {len(error_logs)} 条错误日志")
            
            # 获取统计信息
            stats = UnifiedLog.get_log_statistics(hours=1)
            print(f"📈 统计信息: 总日志数={stats['total_logs']}, 错误数={stats['error_count']}")
            
        except Exception as e:
            print(f"❌ 数据库存储测试失败: {e}")


def test_log_queries():
    """测试日志查询功能"""
    print("\n=== 测试日志查询功能 ===")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 按模块查询
            test_logs = UnifiedLog.get_logs_by_module("test", hours=1, limit=5)
            print(f"🔍 按模块查询: 找到 {len(test_logs)} 条test模块日志")
            
            # 搜索日志
            search_results = UnifiedLog.search_logs("用户", hours=1, limit=5)
            print(f"🔍 搜索'用户': 找到 {len(search_results)} 条匹配日志")
            
            # 按级别查询
            error_logs = UnifiedLog.get_recent_logs(hours=1, level=LogLevel.ERROR, limit=5)
            print(f"🔍 按级别查询: 找到 {len(error_logs)} 条ERROR级别日志")
            
        except Exception as e:
            print(f"❌ 日志查询测试失败: {e}")


def test_application_integration():
    """测试应用集成"""
    print("\n=== 测试应用集成 ===")
    
    app = create_app()
    
    with app.app_context():
        try:
            # 测试数据库服务日志
            from app.services.database_service import DatabaseService
            db_service = DatabaseService()
            
            # 测试认证日志
            from app.utils.structlog_config import get_auth_logger
            auth_logger = get_auth_logger()
            auth_logger.info("测试认证日志", user_id=999, action="test")
            
            # 测试API日志
            from app.utils.structlog_config import get_api_logger
            api_logger = get_api_logger()
            api_logger.info("测试API日志", endpoint="/test", method="GET")
            
            print("✅ 应用集成测试完成")
            
        except Exception as e:
            print(f"❌ 应用集成测试失败: {e}")


def main():
    """主函数"""
    print("🔧 泰摸鱼吧迁移后日志系统测试")
    print("=" * 50)
    
    # 运行测试
    test_basic_logging()
    test_specialized_loggers()
    test_contextual_logging()
    
    # 等待异步日志写入完成
    print("\n⏳ 等待异步日志写入完成...")
    time.sleep(5)
    
    test_database_storage()
    test_log_queries()
    test_application_integration()
    
    print("\n🎉 所有测试完成!")
    print("\n📁 查看数据库中的日志:")
    print("   - 使用日志界面: http://localhost:5001/logs/")
    print("   - 统一日志API: http://localhost:5001/logs/api/structlog/search")
    print("   - 或直接查询数据库: SELECT * FROM unified_logs ORDER BY timestamp DESC LIMIT 10;")


if __name__ == "__main__":
    main()
