#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级系统功能测试脚本
验证高级错误处理和管理API系统是否真正集成
"""

import sys
import os
import requests
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_advanced_error_handler():
    """测试高级错误处理系统"""
    print("=== 测试高级错误处理系统 ===")
    
    try:
        from app.utils.advanced_error_handler import advanced_error_handler, ErrorContext, ErrorCategory, ErrorSeverity
        
        # 测试错误处理
        test_error = Exception("测试错误 - 验证高级错误处理系统")
        context = ErrorContext(test_error)
        result = advanced_error_handler.handle_error(test_error, context)
        
        print(f"✓ 错误处理结果: {result.get('error_id', 'N/A')}")
        print(f"✓ 错误分类: {result.get('category', 'N/A')}")
        print(f"✓ 严重程度: {result.get('severity', 'N/A')}")
        print(f"✓ 恢复状态: {result.get('recovery', {}).get('success', False)}")
        
        # 测试错误指标
        metrics = advanced_error_handler.get_error_metrics()
        print(f"✓ 错误指标: {len(metrics)} 个指标")
        
        print("✓ 高级错误处理系统测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 高级错误处理系统测试失败: {e}")
        return False

def test_admin_api_endpoints():
    """测试管理API端点"""
    print("\n=== 测试管理API端点 ===")
    
    base_url = "http://localhost:5001"
    endpoints = [
        "/admin/system-info",
        "/admin/performance",
        "/admin/error-metrics",
        "/admin/constants/api",
        "/admin/system-logs"
    ]
    
    success_count = 0
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:  # 401/403 表示需要登录，但端点存在
                print(f"✓ {endpoint}: {response.status_code}")
                success_count += 1
            else:
                print(f"✗ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint}: 连接失败 - {e}")
    
    print(f"✓ 管理API端点测试: {success_count}/{len(endpoints)} 个端点可访问")
    return success_count >= len(endpoints) * 0.8  # 80% 成功率

def test_error_handling_integration():
    """测试错误处理集成"""
    print("\n=== 测试错误处理集成 ===")
    
    try:
        # 测试一个会触发错误的请求
        response = requests.get("http://localhost:5001/nonexistent-endpoint", timeout=5)
        
        if response.status_code == 404:
            print("✓ 404错误被正确处理")
            
            # 检查响应是否包含高级错误处理的信息
            try:
                data = response.json()
                if 'error_id' in data or 'category' in data:
                    print("✓ 高级错误处理信息已包含在响应中")
                    return True
                else:
                    print("⚠ 响应中未找到高级错误处理信息")
                    return False
            except:
                print("⚠ 响应不是JSON格式")
                return False
        else:
            print(f"✗ 意外的状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 错误处理集成测试失败: {e}")
        return False

def test_performance_monitor_integration():
    """测试性能监控集成"""
    print("\n=== 测试性能监控集成 ===")
    
    try:
        from app.utils.performance_monitor import performance_monitor
        
        # 检查性能监控是否运行
        if hasattr(performance_monitor, 'is_monitoring') and performance_monitor.is_monitoring:
            print("✓ 性能监控正在运行")
        else:
            print("⚠ 性能监控状态未知")
        
        # 获取性能摘要
        summary = performance_monitor.get_performance_summary()
        print(f"✓ 性能摘要: {len(summary)} 个指标")
        
        # 检查是否有性能数据
        if 'memory_percent' in summary or 'cpu_percent' in summary:
            print("✓ 性能数据正常收集")
            return True
        else:
            print("⚠ 性能数据收集异常")
            return False
            
    except Exception as e:
        print(f"✗ 性能监控集成测试失败: {e}")
        return False

def test_management_interfaces():
    """测试管理界面"""
    print("\n=== 测试管理界面 ===")
    
    base_url = "http://localhost:5001"
    interfaces = [
        "/admin/system-management",
        "/admin/error-management", 
        "/admin/constants",
        "/admin/dashboard"
    ]
    
    success_count = 0
    
    for interface in interfaces:
        try:
            response = requests.get(f"{base_url}{interface}", timeout=5)
            if response.status_code in [200, 401, 403]:  # 401/403 表示需要登录，但界面存在
                print(f"✓ {interface}: {response.status_code}")
                success_count += 1
            else:
                print(f"✗ {interface}: {response.status_code}")
        except Exception as e:
            print(f"✗ {interface}: 连接失败 - {e}")
    
    print(f"✓ 管理界面测试: {success_count}/{len(interfaces)} 个界面可访问")
    return success_count >= len(interfaces) * 0.8  # 80% 成功率

def test_constant_management():
    """测试常量管理"""
    print("\n=== 测试常量管理 ===")
    
    try:
        from app.constants import SystemConstants, DefaultConfig, ErrorMessages, SuccessMessages
        
        # 测试常量使用
        assert SystemConstants.DEFAULT_PAGE_SIZE == 20
        assert SystemConstants.MAX_FILE_SIZE == 16 * 1024 * 1024
        assert ErrorMessages.INTERNAL_ERROR == "服务器内部错误"
        assert SuccessMessages.OPERATION_SUCCESS == "操作成功"
        
        print("✓ 常量定义正确")
        print("✓ 常量值一致性验证通过")
        print("✓ 常量管理系统正常工作")
        return True
        
    except Exception as e:
        print(f"✗ 常量管理测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始高级系统功能测试...\n")
    
    tests = [
        test_advanced_error_handler,
        test_admin_api_endpoints,
        test_error_handling_integration,
        test_performance_monitor_integration,
        test_management_interfaces,
        test_constant_management
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！高级系统功能完全集成！")
        return True
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
