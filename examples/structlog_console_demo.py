#!/usr/bin/env python3
"""
泰摸鱼吧 - Structlog 控制台输出和上下文绑定演示
展示如何使用美化的控制台输出和上下文变量绑定功能
"""

import sys
import os
import time
import random
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.utils.structlog_config import (
    get_logger,
    bind_context,
    clear_context,
    get_context,
    LogContext,
    with_log_context,
    bind_request_context,
    clear_request_context,
    log_info,
    log_error,
    log_warning,
    log_debug,
    set_debug_logging_enabled,
)

def demo_basic_logging():
    """演示基本日志记录"""
    print("=" * 60)
    print("🎯 基本日志记录演示")
    print("=" * 60)
    
    # 获取不同类型的日志记录器
    system_logger = get_logger("system")
    api_logger = get_logger("api")
    db_logger = get_logger("database")
    
    # 记录不同级别的日志
    system_logger.info("系统启动完成", module="system", version="4.0.0")
    api_logger.warning("API请求频率过高", module="api", endpoint="/api/users", rate_limit=100)
    db_logger.error("数据库连接失败", module="database", host="localhost", port=5432, error="Connection refused")
    
    # 使用便捷函数
    log_info("用户登录成功", module="auth", user_id=123, username="admin")
    log_warning("密码强度不足", module="auth", user_id=123, password_strength="weak")
    log_error("文件上传失败", module="upload", filename="test.pdf", size="10MB", error="File too large")


def demo_context_binding():
    """演示上下文绑定功能"""
    print("\n" + "=" * 60)
    print("🔗 上下文绑定演示")
    print("=" * 60)
    
    # 绑定全局上下文
    bind_context(
        operation_id="op_001",
        session_id="sess_123456",
        feature="user_management",
        environment="development"
    )
    
    print(f"当前全局上下文: {get_context()}")
    
    # 记录日志（会自动包含上下文）
    logger = get_logger("demo")
    logger.info("开始处理用户请求", module="demo", user_id=456)
    logger.warning("检测到异常行为", module="demo", suspicious_activity="multiple_failed_logins")
    
    # 使用上下文管理器临时添加更多上下文
    with LogContext(transaction_id="tx_789", step="validation"):
        logger.info("验证用户输入", module="demo", input_type="email")
        logger.debug("检查邮箱格式", module="demo", email="test@example.com")
    
    # 上下文管理器退出后，临时上下文被清除
    logger.info("验证完成", module="demo")
    
    # 清除全局上下文
    clear_context()
    print(f"清除后的上下文: {get_context()}")


def demo_request_context():
    """演示请求上下文绑定"""
    print("\n" + "=" * 60)
    print("🌐 请求上下文演示")
    print("=" * 60)
    
    # 模拟请求上下文
    bind_request_context(request_id="req_001", user_id=789)
    
    logger = get_logger("request")
    logger.info("处理HTTP请求", module="request", method="POST", path="/api/users")
    logger.debug("解析请求参数", module="request", params={"name": "John", "age": 30})
    
    # 清除请求上下文
    clear_request_context()
    logger.info("请求处理完成", module="request")


def demo_decorator_context():
    """演示装饰器上下文绑定"""
    print("\n" + "=" * 60)
    print("🎭 装饰器上下文演示")
    print("=" * 60)
    
    @with_log_context(service="user_service", version="1.2.0")
    def create_user(username: str, email: str):
        """创建用户"""
        logger = get_logger("user_service")
        logger.info("开始创建用户", module="user_service", username=username, email=email)
        
        # 模拟一些处理步骤
        time.sleep(0.1)
        logger.debug("验证用户数据", module="user_service", validation_rules=["email_format", "username_length"])
        
        time.sleep(0.1)
        logger.info("用户创建成功", module="user_service", user_id=random.randint(1000, 9999))
        
        return {"success": True, "username": username}
    
    # 调用带上下文的函数
    result = create_user("john_doe", "john@example.com")
    print(f"创建用户结果: {result}")


def demo_debug_logging():
    """演示DEBUG日志控制"""
    print("\n" + "=" * 60)
    print("🐛 DEBUG日志控制演示")
    print("=" * 60)
    
    # 启用DEBUG日志
    set_debug_logging_enabled(True)
    print("✅ DEBUG日志已启用")
    
    logger = get_logger("debug_demo")
    logger.debug("这是DEBUG级别的日志", module="debug_demo", detail="详细调试信息")
    log_debug("使用便捷函数记录DEBUG日志", module="debug_demo", step="step_1")
    
    # 禁用DEBUG日志
    set_debug_logging_enabled(False)
    print("❌ DEBUG日志已禁用")
    
    logger.debug("这条DEBUG日志不会显示", module="debug_demo")
    log_debug("这条DEBUG日志也不会显示", module="debug_demo")


def demo_error_tracking():
    """演示错误追踪和堆栈信息"""
    print("\n" + "=" * 60)
    print("🚨 错误追踪演示")
    print("=" * 60)
    
    logger = get_logger("error_demo")
    
    try:
        # 模拟一个错误
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error(
            "除零错误",
            module="error_demo",
            operation="division",
            dividend=10,
            divisor=0,
            exception=str(e)
        )
    
    try:
        # 模拟另一个错误
        data = {"key": "value"}
        value = data["nonexistent_key"]
    except KeyError as e:
        logger.error(
            "键不存在错误",
            module="error_demo",
            operation="dict_access",
            key="nonexistent_key",
            available_keys=list(data.keys()),
            exception=str(e)
        )


def demo_performance_logging():
    """演示性能日志记录"""
    print("\n" + "=" * 60)
    print("⚡ 性能日志演示")
    print("=" * 60)
    
    logger = get_logger("performance")
    
    # 模拟性能监控
    start_time = time.time()
    
    with LogContext(operation="data_processing", batch_size=1000):
        logger.info("开始处理数据", module="performance", total_records=1000)
        
        # 模拟数据处理
        for i in range(10):
            time.sleep(0.05)  # 模拟处理时间
            if i % 3 == 0:
                logger.debug(f"处理进度: {i+1}/10", module="performance", progress=f"{(i+1)*10}%")
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(
            "数据处理完成",
            module="performance",
            duration=f"{duration:.2f}s",
            records_per_second=f"{1000/duration:.0f}"
        )


def main():
    """主函数"""
    print("🚀 泰摸鱼吧 - Structlog 控制台输出和上下文绑定演示")
    print("=" * 80)
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        # 运行各种演示
        demo_basic_logging()
        demo_context_binding()
        demo_request_context()
        demo_decorator_context()
        demo_debug_logging()
        demo_error_tracking()
        demo_performance_logging()
        
        print("\n" + "=" * 80)
        print("✅ 演示完成！")
        print("=" * 80)
        print("\n💡 使用提示:")
        print("1. 在终端中运行此脚本可以看到彩色的美化输出")
        print("2. 在非终端环境中会使用简单的文本输出")
        print("3. 所有日志都会同时输出到控制台和数据库")
        print("4. 使用 bind_context() 可以绑定全局上下文变量")
        print("5. 使用 LogContext 可以临时绑定上下文")
        print("6. 使用 @with_log_context 装饰器可以自动绑定上下文")


if __name__ == "__main__":
    main()
