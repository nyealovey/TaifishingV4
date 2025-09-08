#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 综合测试脚本
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ComprehensiveTester:
    """综合测试器"""
    
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始综合测试...")
        print("=" * 60)
        
        # 基础功能测试
        self.test_health_endpoints()
        self.test_authentication()
        self.test_api_endpoints()
        self.test_database_operations()
        self.test_error_handling()
        self.test_performance()
        
        # 生成测试报告
        self.generate_report()
        
    def test_health_endpoints(self):
        """测试健康检查端点"""
        print("\n📊 测试健康检查端点...")
        
        endpoints = [
            '/health/health',
            '/health/detailed',
            '/health/readiness',
            '/health/liveness'
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                self.record_test(
                    f"健康检查 - {endpoint}",
                    response.status_code == 200,
                    f"状态码: {response.status_code}",
                    response.elapsed.total_seconds()
                )
            except Exception as e:
                self.record_test(
                    f"健康检查 - {endpoint}",
                    False,
                    f"错误: {str(e)}",
                    0
                )
    
    def test_authentication(self):
        """测试认证功能"""
        print("\n🔐 测试认证功能...")
        
        # 测试登录页面
        try:
            response = self.session.get(f"{self.base_url}/auth/login")
            self.record_test(
                "认证 - 登录页面",
                response.status_code == 200,
                f"状态码: {response.status_code}",
                response.elapsed.total_seconds()
            )
        except Exception as e:
            self.record_test(
                "认证 - 登录页面",
                False,
                f"错误: {str(e)}",
                0
            )
        
        # 测试注册页面
        try:
            response = self.session.get(f"{self.base_url}/auth/register")
            self.record_test(
                "认证 - 注册页面",
                response.status_code == 200,
                f"状态码: {response.status_code}",
                response.elapsed.total_seconds()
            )
        except Exception as e:
            self.record_test(
                "认证 - 注册页面",
                False,
                f"错误: {str(e)}",
                0
            )
    
    def test_api_endpoints(self):
        """测试API端点"""
        print("\n🌐 测试API端点...")
        
        api_endpoints = [
            '/api/health',
            '/api/status',
            '/api/version'
        ]
        
        for endpoint in api_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                self.record_test(
                    f"API - {endpoint}",
                    response.status_code in [200, 401],  # 401表示需要认证
                    f"状态码: {response.status_code}",
                    response.elapsed.total_seconds()
                )
            except Exception as e:
                self.record_test(
                    f"API - {endpoint}",
                    False,
                    f"错误: {str(e)}",
                    0
                )
    
    def test_database_operations(self):
        """测试数据库操作"""
        print("\n🗄️ 测试数据库操作...")
        
        # 通过健康检查间接测试数据库
        try:
            response = self.session.get(f"{self.base_url}/health/detailed")
            if response.status_code == 200:
                data = response.json()
                db_healthy = data.get('data', {}).get('components', {}).get('database', {}).get('healthy', False)
                self.record_test(
                    "数据库 - 连接测试",
                    db_healthy,
                    f"数据库状态: {'健康' if db_healthy else '异常'}",
                    response.elapsed.total_seconds()
                )
            else:
                self.record_test(
                    "数据库 - 连接测试",
                    False,
                    f"健康检查失败: {response.status_code}",
                    response.elapsed.total_seconds()
                )
        except Exception as e:
            self.record_test(
                "数据库 - 连接测试",
                False,
                f"错误: {str(e)}",
                0
            )
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n⚠️ 测试错误处理...")
        
        # 测试404错误
        try:
            response = self.session.get(f"{self.base_url}/nonexistent-page")
            self.record_test(
                "错误处理 - 404页面",
                response.status_code == 404,
                f"状态码: {response.status_code}",
                response.elapsed.total_seconds()
            )
        except Exception as e:
            self.record_test(
                "错误处理 - 404页面",
                False,
                f"错误: {str(e)}",
                0
            )
        
        # 测试500错误（通过无效参数）
        try:
            response = self.session.get(f"{self.base_url}/logs/?page=invalid")
            # 应该返回400或500错误
            self.record_test(
                "错误处理 - 无效参数",
                response.status_code in [400, 500],
                f"状态码: {response.status_code}",
                response.elapsed.total_seconds()
            )
        except Exception as e:
            self.record_test(
                "错误处理 - 无效参数",
                False,
                f"错误: {str(e)}",
                0
            )
    
    def test_performance(self):
        """测试性能"""
        print("\n⚡ 测试性能...")
        
        # 测试响应时间
        endpoints = [
            '/health/health',
            '/auth/login',
            '/api/health'
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start_time
                
                # 响应时间应该小于2秒
                performance_ok = response_time < 2.0
                
                self.record_test(
                    f"性能 - {endpoint}",
                    performance_ok,
                    f"响应时间: {response_time:.3f}秒",
                    response_time
                )
            except Exception as e:
                self.record_test(
                    f"性能 - {endpoint}",
                    False,
                    f"错误: {str(e)}",
                    0
                )
    
    def record_test(self, test_name, passed, details, duration):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} {test_name}: {details}")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📋 测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"通过率: {(passed_tests/total_tests)*100:.1f}%")
        
        # 显示失败的测试
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        # 显示性能统计
        durations = [r['duration'] for r in self.test_results if r['duration'] > 0]
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            print(f"\n⚡ 性能统计:")
            print(f"  平均响应时间: {avg_duration:.3f}秒")
            print(f"  最大响应时间: {max_duration:.3f}秒")
        
        # 保存详细报告
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'pass_rate': (passed_tests/total_tests)*100
                },
                'results': self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")

def main():
    """主函数"""
    print("🚀 泰摸鱼吧综合测试工具")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:5001/health/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服务未正常运行，请先启动应用")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务，请先启动应用")
        return
    
    # 运行测试
    tester = ComprehensiveTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
