#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 第二轮审计测试脚本
运行所有新增功能的测试
"""

from app.constants import SystemConstants, DefaultConfig
import os
import sys
import time
import json
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
# 性能监控已移除
from app.utils.advanced_error_handler import advanced_error_handler
from app.utils.code_quality_analyzer import code_quality_analyzer
from app.utils.advanced_test_framework import test_framework

logger = logging.getLogger(__name__)

class SecondAuditTester:
    """第二轮审计测试器"""
    
    def __init__(self):
        self.app = create_app('testing')
        self.test_results = []
        self.start_time = None
        
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始第二轮审计测试...")
        self.start_time = time.time()
        
        with self.app.app_context():
            # 创建测试数据库
            db.create_all()
            
            try:
                # 运行各种测试
                self._test_constants_module()
                self._test_advanced_error_handler()
                # 性能监控测试已移除
                self._test_code_quality_analyzer()
                self._test_advanced_test_framework()
                self._test_admin_routes()
                self._test_automated_deployment()
                
                # 生成测试报告
                report = self._generate_test_report()
                return report
                
            finally:
                # 清理测试数据库
                db.drop_all()
    
    def _test_constants_module(self):
        """测试常量模块"""
        logger.info("测试常量模块...")
        
        try:
            from app.constants import (
                LogLevel, UserRole, TaskStatus, SystemConstants,
                DefaultConfig, ErrorMessages, SuccessMessages
            )
            
            # 测试枚举
            assert LogLevel.INFO.value == "INFO"
            assert UserRole.ADMIN.value == "admin"
            assert TaskStatus.PENDING.value == "pending"
            
            # 测试常量
            assert SystemConstants.DEFAULT_PAGE_SIZE == 20
            assert SystemConstants.MIN_PASSWORD_LENGTH == 8
            assert SystemConstants.DEFAULT_CACHE_TIMEOUT == 300
            
            # 测试配置
            assert DefaultConfig.SECRET_KEY is not None
            assert DefaultConfig.DATABASE_URL is not None
            
            # 测试消息
            assert ErrorMessages.INTERNAL_ERROR == "服务器内部错误"
            assert SuccessMessages.OPERATION_SUCCESS == "操作成功"
            
            self._record_test_result("constants_module", True, "常量模块测试通过")
            
        except Exception as e:
            self._record_test_result("constants_module", False, f"常量模块测试失败: {e}")
    
    def _test_advanced_error_handler(self):
        """测试高级错误处理器"""
        logger.info("测试高级错误处理器...")
        
        try:
            from app.utils.advanced_error_handler import (
                advanced_error_handler, ErrorCategory, ErrorSeverity,
                ErrorContext, handle_advanced_errors
            )
            
            # 测试错误分类
            assert ErrorCategory.DATABASE == "database"
            assert ErrorSeverity.HIGH == "high"
            
            # 测试错误上下文
            test_error = ValueError("测试错误")
            context = ErrorContext(test_error)
            assert context.error_id is not None
            assert context.error_type == "ValueError"
            
            # 测试错误处理
            error_response = advanced_error_handler.handle_error(test_error, context)
            assert error_response['error'] is True
            assert 'error_id' in error_response
            
            # 测试错误指标
            metrics = advanced_error_handler.get_error_metrics()
            assert isinstance(metrics, dict)
            
            self._record_test_result("advanced_error_handler", True, "高级错误处理器测试通过")
            
        except Exception as e:
            self._record_test_result("advanced_error_handler", False, f"高级错误处理器测试失败: {e}")
    
    # 性能监控测试已移除
    
    def _test_code_quality_analyzer(self):
        """测试代码质量分析器"""
        logger.info("测试代码质量分析器...")
        
        try:
            # 测试代码质量分析器初始化
            assert code_quality_analyzer is not None
            
            # 测试Python文件查找
            python_files = code_quality_analyzer._find_python_files()
            assert len(python_files) > 0
            
            # 测试单个文件分析
            if python_files:
                test_file = python_files[0]
                try:
                    code_quality_analyzer._analyze_file(test_file)
                except Exception as e:
                    logger.warning(f"分析文件失败: {test_file}, 错误: {e}")
            
            # 测试项目分析
            analysis_result = code_quality_analyzer.analyze_project()
            assert 'summary' in analysis_result
            assert 'issues' in analysis_result
            assert 'metrics' in analysis_result
            assert 'suggestions' in analysis_result
            
            self._record_test_result("code_quality_analyzer", True, "代码质量分析器测试通过")
            
        except Exception as e:
            self._record_test_result("code_quality_analyzer", False, f"代码质量分析器测试失败: {e}")
    
    def _test_advanced_test_framework(self):
        """测试高级测试框架"""
        logger.info("测试高级测试框架...")
        
        try:
            # 测试测试框架初始化
            assert test_framework is not None
            
            # 测试综合测试
            test_results = test_framework.run_comprehensive_tests()
            assert 'summary' in test_results
            assert 'results' in test_results
            
            self._record_test_result("advanced_test_framework", True, "高级测试框架测试通过")
            
        except Exception as e:
            self._record_test_result("advanced_test_framework", False, f"高级测试框架测试失败: {e}")
    
    def _test_admin_routes(self):
        """测试管理路由"""
        logger.info("测试管理路由...")
        
        try:
            from app.routes.admin import admin_bp
            
            # 测试蓝图创建
            assert admin_bp is not None
            assert admin_bp.name == 'admin'
            assert admin_bp.url_prefix == '/admin'
            
            # 测试路由注册
            routes = [rule.rule for rule in admin_bp.url_map.iter_rules()]
            expected_routes = [
                '/admin/dashboard',
                '/admin/performance',
                '/admin/errors',
                '/admin/code-quality',
                '/admin/tests',
                '/admin/system-info',
                '/admin/logs',
                '/admin/maintenance',
                '/admin/cache',
                '/admin/backup',
                '/admin/deployment'
            ]
            
            for route in expected_routes:
                assert any(route in r for r in routes), f"路由 {route} 未找到"
            
            self._record_test_result("admin_routes", True, "管理路由测试通过")
            
        except Exception as e:
            self._record_test_result("admin_routes", False, f"管理路由测试失败: {e}")
    
    def _test_automated_deployment(self):
        """测试自动化部署"""
        logger.info("测试自动化部署...")
        
        try:
            from scripts.automated_deployment import DeploymentManager
            
            # 测试部署管理器初始化
            manager = DeploymentManager()
            assert manager.project_root is not None
            assert manager.deployment_config is not None
            
            # 测试配置验证
            assert 'app_name' in manager.deployment_config
            assert 'port' in manager.deployment_config
            assert 'workers' in manager.deployment_config
            
            # 测试状态检查
            status = manager.status()
            assert isinstance(status, dict)
            
            self._record_test_result("automated_deployment", True, "自动化部署测试通过")
            
        except Exception as e:
            self._record_test_result("automated_deployment", False, f"自动化部署测试失败: {e}")
    
    def _record_test_result(self, test_name: str, success: bool, message: str):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✓ {test_name}: {message}")
        else:
            logger.error(f"✗ {test_name}: {message}")
    
    def _generate_test_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        report = {
            'test_suite': 'second_audit_tests',
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': round(success_rate, 2)
            },
            'results': self.test_results
        }
        
        # 保存报告
        report_file = 'doc/second_audit_test_report.json'
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已保存: {report_file}")
        
        return report

def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    tester = SecondAuditTester()
    report = tester.run_all_tests()
    
    # 输出结果
    print("\n" + "="*60)
    print("第二轮审计测试结果")
    print("="*60)
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"成功率: {report['summary']['success_rate']}%")
    print(f"耗时: {report['duration']:.2f}秒")
    print("="*60)
    
    # 显示详细结果
    for result in report['results']:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['test_name']}: {result['message']}")
    
    print("="*60)
    
    # 返回退出码
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
