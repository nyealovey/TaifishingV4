#!/usr/bin/env python3

"""
测试API日志记录功能
"""

import time

import requests


def test_api_endpoints():
    """测试所有API端点的日志记录"""
    base_url = "http://localhost:5001"

    # 需要测试的API端点
    endpoints = [
        "/api/health",
        "/api/status",
        "/api-status",
        "/dashboard/api/overview",
        "/dashboard/api/charts",
        "/dashboard/api/activities",
        "/dashboard/api/status",
    ]

    print("🧪 开始测试API日志记录...")
    print("=" * 50)

    for endpoint in endpoints:
        try:
            print(f"📡 测试端点: {endpoint}")

            # 发送请求
            response = requests.get(f"{base_url}{endpoint}", timeout=10)

            print(f"   ✅ 状态码: {response.status_code}")
            print(f"   ⏱️  响应时间: {response.elapsed.total_seconds():.3f}s")

            # 等待一下让日志写入
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
        except Exception as e:
            print(f"   ❌ 其他错误: {e}")

        print()

    print("=" * 50)
    print("✅ API日志记录测试完成！")
    print("\n📋 请检查以下日志文件:")
    print("   - userdata/logs/api.log (API专用日志)")
    print("   - userdata/logs/app.log (主应用日志)")


if __name__ == "__main__":
    test_api_endpoints()
