#!/usr/bin/env python3
"""
测试控制台日志输出和上下文绑定功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.structlog_config import (
    get_logger,
    bind_context,
    LogContext,
    with_log_context,
    log_info,
    log_error,
    log_debug,
    set_debug_logging_enabled,
)

def test_console_output():
    """测试控制台输出"""
    print("🎨 测试控制台美化输出...")
    
    logger = get_logger("test")
    
    # 测试不同级别的日志
    logger.info("这是一条信息日志", module="test", user_id=123)
    logger.warning("这是一条警告日志", module="test", warning_type="rate_limit")
    logger.error("这是一条错误日志", module="test", error_code="E001")
    
    # 测试便捷函数
    log_info("使用便捷函数记录信息", module="test", operation="create_user")
    log_error("使用便捷函数记录错误", module="test", operation="delete_user", error="Permission denied")

def test_context_binding():
    """测试上下文绑定"""
    print("\n🔗 测试上下文绑定...")
    
    # 绑定全局上下文
    bind_context(
        operation_id="test_001",
        session_id="sess_123",
        feature="testing"
    )
    
    logger = get_logger("context_test")
    logger.info("这条日志会包含全局上下文", module="context_test")
    
    # 使用上下文管理器
    with LogContext(step="validation", data_type="user_input"):
        logger.info("这条日志会包含临时上下文", module="context_test")
    
    logger.info("临时上下文已清除", module="context_test")

def test_decorator():
    """测试装饰器"""
    print("\n🎭 测试装饰器上下文...")
    
    @with_log_context(service="test_service", version="1.0.0")
    def test_function():
        logger = get_logger("decorator_test")
        logger.info("装饰器自动绑定了上下文", module="decorator_test")
        return "success"
    
    result = test_function()
    print(f"函数执行结果: {result}")

def test_debug_control():
    """测试DEBUG控制"""
    print("\n🐛 测试DEBUG控制...")
    
    # 启用DEBUG
    set_debug_logging_enabled(True)
    log_debug("这条DEBUG日志应该显示", module="debug_test")
    
    # 禁用DEBUG
    set_debug_logging_enabled(False)
    log_debug("这条DEBUG日志不应该显示", module="debug_test")

def main():
    """主函数"""
    print("🚀 测试Structlog控制台输出和上下文绑定功能")
    print("=" * 60)
    
    # 创建Flask应用上下文
    app = create_app()
    
    with app.app_context():
        test_console_output()
        test_context_binding()
        test_decorator()
        test_debug_control()
        
        print("\n✅ 测试完成！")
        print("💡 在终端中运行可以看到彩色的美化输出")

if __name__ == "__main__":
    main()
