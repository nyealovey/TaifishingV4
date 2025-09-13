#!/usr/bin/env python3
"""
泰摸鱼吧 - Loguru使用示例
展示如何使用新的Loguru日志系统
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.loguru_logging_system import *


def example_basic_logging():
    """基础日志记录示例"""
    print("=== 基础日志记录示例 ===")
    
    # 基础日志级别
    log_info("这是一条信息日志")
    log_warning("这是一条警告日志")
    log_error("这是一条错误日志")
    log_debug("这是一条调试日志")
    log_critical("这是一条严重错误日志")
    
    print()


def example_contextual_logging():
    """带上下文的日志记录示例"""
    print("=== 带上下文的日志记录示例 ===")
    
    # 带额外信息的日志
    log_info("用户登录", user_id=123, action="login", ip_address="192.168.1.1")
    log_error("数据库连接失败", database="mysql", error="Connection timeout")
    log_warning("缓存未命中", cache_key="user:123", ttl=300)
    
    print()


def example_categorized_logging():
    """分类日志记录示例"""
    print("=== 分类日志记录示例 ===")
    
    # 访问日志
    log_access("API请求", endpoint="/api/users", method="GET", status_code=200)
    log_access("API请求", endpoint="/api/users", method="POST", status_code=201)
    
    # 安全日志
    log_security("登录失败", user_id=123, ip="192.168.1.1", reason="invalid_password")
    log_security("权限检查", user_id=123, resource="/admin", result="denied")
    
    # 数据库日志
    log_database("查询执行", query="SELECT * FROM users", duration=0.5, rows=100)
    log_database("事务提交", table="users", operation="INSERT", affected_rows=1)
    
    # 任务日志
    log_task("同步开始", task_id=1, instance="mysql-prod")
    log_task("同步完成", task_id=1, records=100, duration=30.5)
    
    print()


def example_structured_logging():
    """结构化日志记录示例"""
    print("=== 结构化日志记录示例 ===")
    
    # 用户操作事件
    log_structured("user_action", {
        "user_id": 123,
        "action": "login",
        "timestamp": "2024-01-01T00:00:00Z",
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "success": True
    })
    
    # 系统事件
    log_structured("system_event", {
        "event": "startup",
        "version": "1.0.0",
        "environment": "production",
        "config": {
            "debug": False,
            "log_level": "INFO"
        }
    })
    
    # 性能指标
    log_structured("performance_metric", {
        "metric": "response_time",
        "endpoint": "/api/users",
        "duration": 0.5,
        "status_code": 200,
        "memory_usage": "50MB"
    })
    
    print()


def example_exception_logging():
    """异常日志记录示例"""
    print("=== 异常日志记录示例 ===")
    
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
    
    print()


def example_decorator_usage():
    """装饰器使用示例"""
    print("=== 装饰器使用示例 ===")
    
    @log_function_call
    def calculate_sum(a, b):
        """计算两个数的和"""
        return a + b
    
    @log_database_operation("SELECT")
    def query_users():
        """查询用户"""
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    
    @log_api_call("/api/users")
    def get_users():
        """获取用户列表"""
        return {"users": query_users()}
    
    # 调用函数
    result = calculate_sum(5, 3)
    print(f"计算结果: {result}")
    
    users = get_users()
    print(f"用户列表: {users}")
    
    print()


def example_log_analysis():
    """日志分析示例"""
    print("=== 日志分析示例 ===")
    
    try:
        from app.utils.log_analyzer import analyze_logs, get_error_summary, get_performance_metrics
        
        # 分析应用日志
        stats = analyze_logs("app", days=1)
        print(f"应用日志统计:")
        print(f"  总日志数: {stats.total_logs}")
        print(f"  错误数: {stats.error_count}")
        print(f"  警告数: {stats.warning_count}")
        print(f"  信息数: {stats.info_count}")
        
        # 获取错误摘要
        error_summary = get_error_summary(days=1)
        print(f"\n错误摘要:")
        print(f"  错误总数: {error_summary['error_count']}")
        print(f"  唯一错误数: {error_summary['unique_errors']}")
        
        # 获取性能指标
        performance = get_performance_metrics(days=1)
        print(f"\n性能指标:")
        print(f"  总请求数: {performance['total_requests']}")
        print(f"  平均每小时请求数: {performance['avg_requests_per_hour']}")
        
    except ImportError as e:
        print(f"日志分析功能不可用: {e}")
    
    print()


def main():
    """主函数"""
    print("🔧 泰摸鱼吧 Loguru 日志系统使用示例")
    print("=" * 50)
    
    # 运行各种示例
    example_basic_logging()
    example_contextual_logging()
    example_categorized_logging()
    example_structured_logging()
    example_exception_logging()
    example_decorator_usage()
    example_log_analysis()
    
    print("✅ 所有示例运行完成!")
    print("\n📁 查看日志文件:")
    print("   - userdata/logs/app.log (应用日志)")
    print("   - userdata/logs/error.log (错误日志)")
    print("   - userdata/logs/access.log (访问日志)")
    print("   - userdata/logs/security.log (安全日志)")
    print("   - userdata/logs/database.log (数据库日志)")
    print("   - userdata/logs/tasks.log (任务日志)")
    print("   - userdata/logs/structured.log (结构化日志)")


if __name__ == "__main__":
    main()
