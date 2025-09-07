# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 自动化测试工具
"""

import unittest
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from app import create_app, db
from app.models.user import User
from app.models.instance import Instance
from app.models.credential import Credential
from app.models.task import Task

logger = logging.getLogger(__name__)

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.app = create_app('testing')
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.start_time = time.time()
        
        with self.app.app_context():
            # 创建测试数据库
            db.create_all()
            
            try:
                # 运行单元测试
                unit_results = self._run_unit_tests()
                
                # 运行集成测试
                integration_results = self._run_integration_tests()
                
                # 运行性能测试
                performance_results = self._run_performance_tests()
                
                # 运行安全测试
                security_results = self._run_security_tests()
                
                self.end_time = time.time()
                
                return {
                    'success': True,
                    'total_time': self.end_time - self.start_time,
                    'unit_tests': unit_results,
                    'integration_tests': integration_results,
                    'performance_tests': performance_results,
                    'security_tests': security_results,
                    'summary': self._generate_summary()
                }
                
            finally:
                # 清理测试数据库
                db.drop_all()
    
    def _run_unit_tests(self) -> Dict[str, Any]:
        """运行单元测试"""
        logger.info("开始运行单元测试...")
        
        tests = [
            self._test_user_creation,
            self._test_instance_creation,
            self._test_credential_creation,
            self._test_task_creation,
            self._test_database_connections,
            self._test_validation_functions,
            self._test_utility_functions
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = test()
                if result['success']:
                    passed += 1
                else:
                    failed += 1
                results.append(result)
            except Exception as e:
                failed += 1
                results.append({
                    'name': test.__name__,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(tests),
            'passed': passed,
            'failed': failed,
            'results': results
        }
    
    def _run_integration_tests(self) -> Dict[str, Any]:
        """运行集成测试"""
        logger.info("开始运行集成测试...")
        
        tests = [
            self._test_user_workflow,
            self._test_instance_management,
            self._test_task_execution,
            self._test_api_endpoints,
            self._test_database_operations
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = test()
                if result['success']:
                    passed += 1
                else:
                    failed += 1
                results.append(result)
            except Exception as e:
                failed += 1
                results.append({
                    'name': test.__name__,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(tests),
            'passed': passed,
            'failed': failed,
            'results': results
        }
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """运行性能测试"""
        logger.info("开始运行性能测试...")
        
        tests = [
            self._test_database_query_performance,
            self._test_api_response_time,
            self._test_memory_usage,
            self._test_concurrent_operations
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = test()
                if result['success']:
                    passed += 1
                else:
                    failed += 1
                results.append(result)
            except Exception as e:
                failed += 1
                results.append({
                    'name': test.__name__,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(tests),
            'passed': passed,
            'failed': failed,
            'results': results
        }
    
    def _run_security_tests(self) -> Dict[str, Any]:
        """运行安全测试"""
        logger.info("开始运行安全测试...")
        
        tests = [
            self._test_input_validation,
            self._test_sql_injection_protection,
            self._test_authentication_security,
            self._test_authorization_checks,
            self._test_data_encryption
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                result = test()
                if result['success']:
                    passed += 1
                else:
                    failed += 1
                results.append(result)
            except Exception as e:
                failed += 1
                results.append({
                    'name': test.__name__,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(tests),
            'passed': passed,
            'failed': failed,
            'results': results
        }
    
    # 单元测试方法
    def _test_user_creation(self) -> Dict[str, Any]:
        """测试用户创建"""
        try:
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
            
            # 验证用户创建
            created_user = User.query.filter_by(username='testuser').first()
            assert created_user is not None
            assert created_user.email == 'test@example.com'
            
            return {'name': 'test_user_creation', 'success': True}
        except Exception as e:
            return {'name': 'test_user_creation', 'success': False, 'error': str(e)}
    
    def _test_instance_creation(self) -> Dict[str, Any]:
        """测试实例创建"""
        try:
            instance = Instance(
                name='test_instance',
                db_type='mysql',
                host='localhost',
                port=3306,
                database_name='test_db'
            )
            db.session.add(instance)
            db.session.commit()
            
            # 验证实例创建
            created_instance = Instance.query.filter_by(name='test_instance').first()
            assert created_instance is not None
            assert created_instance.db_type == 'mysql'
            
            return {'name': 'test_instance_creation', 'success': True}
        except Exception as e:
            return {'name': 'test_instance_creation', 'success': False, 'error': str(e)}
    
    def _test_credential_creation(self) -> Dict[str, Any]:
        """测试凭据创建"""
        try:
            credential = Credential(
                name='test_credential',
                username='test_user',
                password='test_password'
            )
            db.session.add(credential)
            db.session.commit()
            
            # 验证凭据创建
            created_credential = Credential.query.filter_by(name='test_credential').first()
            assert created_credential is not None
            assert created_credential.username == 'test_user'
            
            return {'name': 'test_credential_creation', 'success': True}
        except Exception as e:
            return {'name': 'test_credential_creation', 'success': False, 'error': str(e)}
    
    def _test_task_creation(self) -> Dict[str, Any]:
        """测试任务创建"""
        try:
            task = Task(
                name='test_task',
                task_type='sync_accounts',
                db_type='mysql',
                schedule='0 0 * * *',
                description='Test task'
            )
            db.session.add(task)
            db.session.commit()
            
            # 验证任务创建
            created_task = Task.query.filter_by(name='test_task').first()
            assert created_task is not None
            assert created_task.task_type == 'sync_accounts'
            
            return {'name': 'test_task_creation', 'success': True}
        except Exception as e:
            return {'name': 'test_task_creation', 'success': False, 'error': str(e)}
    
    def _test_database_connections(self) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            # 测试SQLite连接
            result = db.session.execute('SELECT 1').scalar()
            assert result == 1
            
            return {'name': 'test_database_connections', 'success': True}
        except Exception as e:
            return {'name': 'test_database_connections', 'success': False, 'error': str(e)}
    
    def _test_validation_functions(self) -> Dict[str, Any]:
        """测试验证函数"""
        try:
            from app.utils.validation import InputValidator
            
            # 测试字符串验证
            valid_string = InputValidator.validate_string('test', min_length=1, max_length=10)
            assert valid_string == 'test'
            
            # 测试整数验证
            valid_int = InputValidator.validate_integer('123', min_val=1, max_val=1000)
            assert valid_int == 123
            
            # 测试邮箱验证
            valid_email = InputValidator.validate_email('test@example.com')
            assert valid_email == 'test@example.com'
            
            return {'name': 'test_validation_functions', 'success': True}
        except Exception as e:
            return {'name': 'test_validation_functions', 'success': False, 'error': str(e)}
    
    def _test_utility_functions(self) -> Dict[str, Any]:
        """测试工具函数"""
        try:
            from app.utils.timezone import get_china_time, format_china_time
            from datetime import datetime
            
            # 测试时区转换
            now = datetime.utcnow()
            china_time = get_china_time(now)
            formatted_time = format_china_time(now)
            
            assert china_time is not None
            assert formatted_time is not None
            
            return {'name': 'test_utility_functions', 'success': True}
        except Exception as e:
            return {'name': 'test_utility_functions', 'success': False, 'error': str(e)}
    
    # 集成测试方法
    def _test_user_workflow(self) -> Dict[str, Any]:
        """测试用户工作流"""
        try:
            # 创建用户
            user = User(
                username='workflow_user',
                email='workflow@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
            
            # 创建实例
            instance = Instance(
                name='workflow_instance',
                db_type='mysql',
                host='localhost',
                port=3306,
                database_name='workflow_db'
            )
            db.session.add(instance)
            db.session.commit()
            
            # 创建凭据
            credential = Credential(
                name='workflow_credential',
                username='workflow_user',
                password='workflow_password'
            )
            db.session.add(credential)
            db.session.commit()
            
            # 关联实例和凭据
            instance.credential_id = credential.id
            db.session.commit()
            
            # 验证关联
            updated_instance = Instance.query.get(instance.id)
            assert updated_instance.credential_id == credential.id
            
            return {'name': 'test_user_workflow', 'success': True}
        except Exception as e:
            return {'name': 'test_user_workflow', 'success': False, 'error': str(e)}
    
    def _test_instance_management(self) -> Dict[str, Any]:
        """测试实例管理"""
        try:
            # 创建多个实例
            instances = []
            for i in range(5):
                instance = Instance(
                    name=f'instance_{i}',
                    db_type='mysql',
                    host='localhost',
                    port=3306 + i,
                    database_name=f'db_{i}'
                )
                db.session.add(instance)
                instances.append(instance)
            
            db.session.commit()
            
            # 测试查询
            all_instances = Instance.query.all()
            assert len(all_instances) >= 5
            
            # 测试过滤
            mysql_instances = Instance.query.filter_by(db_type='mysql').all()
            assert len(mysql_instances) >= 5
            
            return {'name': 'test_instance_management', 'success': True}
        except Exception as e:
            return {'name': 'test_instance_management', 'success': False, 'error': str(e)}
    
    def _test_task_execution(self) -> Dict[str, Any]:
        """测试任务执行"""
        try:
            from app.services.task_executor import TaskExecutor
            
            # 创建任务
            task = Task(
                name='test_execution_task',
                task_type='sync_accounts',
                db_type='mysql',
                schedule='0 0 * * *',
                description='Test execution task',
                is_active=True
            )
            db.session.add(task)
            db.session.commit()
            
            # 测试任务执行器
            executor = TaskExecutor()
            # 注意：这里不实际执行任务，只测试创建
            assert executor is not None
            
            return {'name': 'test_task_execution', 'success': True}
        except Exception as e:
            return {'name': 'test_task_execution', 'success': False, 'error': str(e)}
    
    def _test_api_endpoints(self) -> Dict[str, Any]:
        """测试API端点"""
        try:
            with self.app.test_client() as client:
                # 测试健康检查端点
                response = client.get('/api/health')
                assert response.status_code == 200
                
                data = response.get_json()
                assert data['status'] == 'healthy'
            
            return {'name': 'test_api_endpoints', 'success': True}
        except Exception as e:
            return {'name': 'test_api_endpoints', 'success': False, 'error': str(e)}
    
    def _test_database_operations(self) -> Dict[str, Any]:
        """测试数据库操作"""
        try:
            # 测试CRUD操作
            user = User(username='db_test', email='db@test.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            
            # 读取
            found_user = User.query.filter_by(username='db_test').first()
            assert found_user is not None
            
            # 更新
            found_user.email = 'updated@test.com'
            db.session.commit()
            
            updated_user = User.query.get(found_user.id)
            assert updated_user.email == 'updated@test.com'
            
            # 删除
            db.session.delete(updated_user)
            db.session.commit()
            
            deleted_user = User.query.get(found_user.id)
            assert deleted_user is None
            
            return {'name': 'test_database_operations', 'success': True}
        except Exception as e:
            return {'name': 'test_database_operations', 'success': False, 'error': str(e)}
    
    # 性能测试方法
    def _test_database_query_performance(self) -> Dict[str, Any]:
        """测试数据库查询性能"""
        try:
            import time
            
            # 创建测试数据
            users = []
            for i in range(100):
                user = User(
                    username=f'perf_user_{i}',
                    email=f'perf{i}@test.com',
                    password_hash='hash'
                )
                users.append(user)
            
            db.session.add_all(users)
            db.session.commit()
            
            # 测试查询性能
            start_time = time.time()
            all_users = User.query.all()
            query_time = time.time() - start_time
            
            # 性能要求：100条记录查询应在1秒内完成
            assert query_time < 1.0, f"查询时间过长: {query_time:.3f}秒"
            
            return {
                'name': 'test_database_query_performance',
                'success': True,
                'query_time': query_time,
                'record_count': len(all_users)
            }
        except Exception as e:
            return {'name': 'test_database_query_performance', 'success': False, 'error': str(e)}
    
    def _test_api_response_time(self) -> Dict[str, Any]:
        """测试API响应时间"""
        try:
            import time
            
            with self.app.test_client() as client:
                start_time = time.time()
                response = client.get('/api/health')
                response_time = time.time() - start_time
                
                # 性能要求：API响应应在100ms内完成
                assert response_time < 0.1, f"API响应时间过长: {response_time:.3f}秒"
                assert response.status_code == 200
            
            return {
                'name': 'test_api_response_time',
                'success': True,
                'response_time': response_time
            }
        except Exception as e:
            return {'name': 'test_api_response_time', 'success': False, 'error': str(e)}
    
    def _test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # 执行一些操作
            for i in range(1000):
                user = User(
                    username=f'memory_test_{i}',
                    email=f'memory{i}@test.com',
                    password_hash='hash'
                )
                db.session.add(user)
            
            db.session.commit()
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            
            # 内存增长不应超过50MB
            assert memory_increase < 50, f"内存增长过多: {memory_increase:.2f}MB"
            
            return {
                'name': 'test_memory_usage',
                'success': True,
                'memory_increase': memory_increase
            }
        except Exception as e:
            return {'name': 'test_memory_usage', 'success': False, 'error': str(e)}
    
    def _test_concurrent_operations(self) -> Dict[str, Any]:
        """测试并发操作"""
        try:
            import threading
            import time
            
            results = []
            errors = []
            
            def create_user(user_id):
                try:
                    user = User(
                        username=f'concurrent_user_{user_id}',
                        email=f'concurrent{user_id}@test.com',
                        password_hash='hash'
                    )
                    db.session.add(user)
                    db.session.commit()
                    results.append(user_id)
                except Exception as e:
                    errors.append(str(e))
            
            # 创建10个并发线程
            threads = []
            for i in range(10):
                thread = threading.Thread(target=create_user, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 验证结果
            assert len(errors) == 0, f"并发操作出现错误: {errors}"
            assert len(results) == 10, f"并发操作结果不完整: {len(results)}/10"
            
            return {
                'name': 'test_concurrent_operations',
                'success': True,
                'thread_count': 10,
                'success_count': len(results)
            }
        except Exception as e:
            return {'name': 'test_concurrent_operations', 'success': False, 'error': str(e)}
    
    # 安全测试方法
    def _test_input_validation(self) -> Dict[str, Any]:
        """测试输入验证"""
        try:
            from app.utils.validation import InputValidator
            
            # 测试SQL注入防护
            malicious_input = "'; DROP TABLE users; --"
            validated = InputValidator.validate_string(malicious_input)
            assert validated is not None  # 应该被转义而不是被拒绝
            
            # 测试XSS防护
            xss_input = "<script>alert('xss')</script>"
            validated = InputValidator.validate_string(xss_input)
            assert '<script>' not in validated  # 应该被转义
            
            return {'name': 'test_input_validation', 'success': True}
        except Exception as e:
            return {'name': 'test_input_validation', 'success': False, 'error': str(e)}
    
    def _test_sql_injection_protection(self) -> Dict[str, Any]:
        """测试SQL注入防护"""
        try:
            from app.services.database_service import DatabaseService
            
            service = DatabaseService()
            
            # 测试危险查询检测
            dangerous_query = "SELECT * FROM users; DROP TABLE users;"
            is_safe = service._is_safe_query(dangerous_query)
            assert not is_safe, "危险查询应该被检测出来"
            
            # 测试安全查询
            safe_query = "SELECT * FROM users WHERE id = %s"
            is_safe = service._is_safe_query(safe_query)
            assert is_safe, "安全查询应该被允许"
            
            return {'name': 'test_sql_injection_protection', 'success': True}
        except Exception as e:
            return {'name': 'test_sql_injection_protection', 'success': False, 'error': str(e)}
    
    def _test_authentication_security(self) -> Dict[str, Any]:
        """测试认证安全"""
        try:
            from app.models.user import User
            from app import bcrypt
            
            # 测试密码哈希
            password = 'test_password'
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # 验证密码
            is_valid = bcrypt.check_password_hash(password_hash, password)
            assert is_valid, "密码验证应该成功"
            
            # 验证错误密码
            is_invalid = bcrypt.check_password_hash(password_hash, 'wrong_password')
            assert not is_invalid, "错误密码应该验证失败"
            
            return {'name': 'test_authentication_security', 'success': True}
        except Exception as e:
            return {'name': 'test_authentication_security', 'success': False, 'error': str(e)}
    
    def _test_authorization_checks(self) -> Dict[str, Any]:
        """测试授权检查"""
        try:
            # 这里可以测试权限检查逻辑
            # 由于当前项目权限系统较简单，这里做基本测试
            
            user = User(
                username='auth_test',
                email='auth@test.com',
                password_hash='hash',
                role='user'
            )
            
            assert user.role == 'user'
            
            return {'name': 'test_authorization_checks', 'success': True}
        except Exception as e:
            return {'name': 'test_authorization_checks', 'success': False, 'error': str(e)}
    
    def _test_data_encryption(self) -> Dict[str, Any]:
        """测试数据加密"""
        try:
            from app import bcrypt
            
            # 测试敏感数据加密
            sensitive_data = 'sensitive_information'
            encrypted = bcrypt.generate_password_hash(sensitive_data).decode('utf-8')
            
            # 加密后的数据应该与原数据不同
            assert encrypted != sensitive_data
            
            # 应该能够验证加密数据
            is_valid = bcrypt.check_password_hash(encrypted, sensitive_data)
            assert is_valid
            
            return {'name': 'test_data_encryption', 'success': True}
        except Exception as e:
            return {'name': 'test_data_encryption', 'success': False, 'error': str(e)}
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for category in ['unit_tests', 'integration_tests', 'performance_tests', 'security_tests']:
            if hasattr(self, f'_{category}'):
                results = getattr(self, f'_{category}')()
                total_tests += results['total']
                total_passed += results['passed']
                total_failed += results['failed']
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'success_rate': success_rate,
            'execution_time': self.end_time - self.start_time if self.end_time and self.start_time else 0
        }

# 测试装饰器
def test_case(name: str = None):
    """测试用例装饰器"""
    def test_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            test_name = name or func.__name__
            logger.info(f"运行测试: {test_name}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(f"测试通过: {test_name} (耗时: {execution_time:.3f}秒)")
                return {
                    'name': test_name,
                    'success': True,
                    'execution_time': execution_time
                }
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"测试失败: {test_name} (耗时: {execution_time:.3f}秒) - {e}")
                return {
                    'name': test_name,
                    'success': False,
                    'error': str(e),
                    'execution_time': execution_time
                }
        
        return wrapper
    return test_decorator

# 性能测试装饰器
def performance_test(threshold: float = 1.0):
    """性能测试装饰器"""
    def test_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > threshold:
                logger.warning(f"性能测试失败: {func.__name__} 耗时 {execution_time:.3f}秒 (阈值: {threshold}秒)")
                return {
                    'name': func.__name__,
                    'success': False,
                    'error': f'执行时间超过阈值: {execution_time:.3f}s > {threshold}s',
                    'execution_time': execution_time
                }
            
            return {
                'name': func.__name__,
                'success': True,
                'execution_time': execution_time
            }
        
        return wrapper
    return test_decorator
