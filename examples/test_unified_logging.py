#!/usr/bin/env python3
"""
泰摸鱼吧 - 统一日志系统测试
测试基于structlog的统一日志系统功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.unified_log import LogLevel, UnifiedLog
from app.utils.structlog_config import (
    get_api_logger,
    get_auth_logger,
    get_db_logger,
    get_sync_logger,
    get_system_logger,
    get_task_logger,
    log_critical,
    log_debug,
    log_error,
    log_info,
    log_warning,
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


def test_contextual_logging():
    """测试带上下文的日志记录"""
    print("\n=== 测试带上下文的日志记录 ===")

    # 带额外信息的日志
    log_info("用户登录", user_id=123, action="login", ip_address="192.168.1.1")
    log_error("数据库连接失败", database="mysql", error="Connection timeout")
    log_warning("缓存未命中", cache_key="user:123", ttl=300)

    print("✅ 上下文日志记录完成")


def test_specialized_loggers():
    """测试专用日志记录器"""
    print("\n=== 测试专用日志记录器 ===")

    # 认证日志
    auth_logger = get_auth_logger()
    auth_logger.info("用户认证成功", user_id=123, method="password")

    # 数据库日志
    db_logger = get_db_logger()
    db_logger.info("查询执行", query="SELECT * FROM users", duration=0.5, rows=100)

    # 同步日志
    sync_logger = get_sync_logger()
    sync_logger.info("同步开始", task_id=1, instance="mysql-prod")

    # API日志
    api_logger = get_api_logger()
    api_logger.info("API请求", endpoint="/api/users", method="GET", status_code=200)

    # 系统日志
    system_logger = get_system_logger()
    system_logger.info("系统启动", version="1.0.0", environment="production")

    # 任务日志
    task_logger = get_task_logger()
    task_logger.info("任务执行", task_name="sync_accounts", duration=30.5)

    print("✅ 专用日志记录器测试完成")


def test_exception_logging():
    """测试异常日志记录"""
    print("\n=== 测试异常日志记录 ===")

    try:
        # 模拟一个错误
        result = 1 / 0
    except ZeroDivisionError as e:
        log_error("除零错误", exception=e)

    try:
        # 模拟另一个错误
        data = {"key": "value"}
        value = data["nonexistent_key"]
    except KeyError as e:
        log_critical("关键错误", exception=e, context={"data": data})

    print("✅ 异常日志记录完成")


def test_database_storage():
    """测试数据库存储"""
    print("\n=== 测试数据库存储 ===")

    app = create_app()

    with app.app_context():
        try:
            # 创建一些测试日志
            test_logs = [
                UnifiedLog.create_log_entry(
                    level=LogLevel.INFO, module="test", message="测试信息日志", context={"test_id": 1, "action": "test"}
                ),
                UnifiedLog.create_log_entry(
                    level=LogLevel.ERROR,
                    module="test",
                    message="测试错误日志",
                    traceback="Traceback (most recent call last):\n  File \"test.py\", line 1, in <module>\n    raise Exception('Test error')\nException: Test error",
                    context={"test_id": 2, "error_type": "test_error"},
                ),
                UnifiedLog.create_log_entry(
                    level=LogLevel.WARNING,
                    module="test",
                    message="测试警告日志",
                    context={"test_id": 3, "warning_type": "test_warning"},
                ),
            ]

            # 保存到数据库
            db.session.add_all(test_logs)
            db.session.commit()

            print("✅ 测试日志已保存到数据库")

            # 查询日志
            recent_logs = UnifiedLog.get_recent_logs(hours=1, limit=10)
            print(f"📊 查询到 {len(recent_logs)} 条最近日志")

            # 查询错误日志
            error_logs = UnifiedLog.get_error_logs(hours=1, limit=5)
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
            search_results = UnifiedLog.search_logs("测试", hours=1, limit=5)
            print(f"🔍 搜索'测试': 找到 {len(search_results)} 条匹配日志")

            # 按级别查询
            error_logs = UnifiedLog.get_recent_logs(hours=1, level=LogLevel.ERROR, limit=5)
            print(f"🔍 按级别查询: 找到 {len(error_logs)} 条ERROR级别日志")

        except Exception as e:
            print(f"❌ 日志查询测试失败: {e}")


def test_cleanup():
    """测试日志清理功能"""
    print("\n=== 测试日志清理功能 ===")

    app = create_app()

    with app.app_context():
        try:
            # 获取清理前的日志数量
            before_count = UnifiedLog.query.count()
            print(f"📊 清理前日志数量: {before_count}")

            # 清理旧日志（保留1天）
            deleted_count = UnifiedLog.cleanup_old_logs(days=1)
            print(f"🗑️ 清理了 {deleted_count} 条旧日志")

            # 获取清理后的日志数量
            after_count = UnifiedLog.query.count()
            print(f"📊 清理后日志数量: {after_count}")

        except Exception as e:
            print(f"❌ 日志清理测试失败: {e}")


def main():
    """主函数"""
    print("🔧 泰摸鱼吧统一日志系统测试")
    print("=" * 50)

    # 运行测试
    test_basic_logging()
    test_contextual_logging()
    test_specialized_loggers()
    test_exception_logging()

    # 等待一下让异步日志写入完成
    print("\n⏳ 等待异步日志写入完成...")
    time.sleep(3)

    test_database_storage()
    test_log_queries()
    test_cleanup()

    print("\n🎉 所有测试完成!")
    print("\n📁 查看数据库中的日志:")
    print("   - 使用日志中心界面: http://localhost:5000/logs/")
    print("   - 或直接查询数据库: SELECT * FROM unified_logs ORDER BY timestamp DESC LIMIT 10;")


if __name__ == "__main__":
    main()
