#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 简化测试脚本
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_basic_imports():
    """测试基本导入"""
    try:
        logger.info("测试基本导入...")
        
        # 测试模型导入
        from app.models.user import User
        from app.models.instance import Instance
        from app.models.credential import Credential
        from app.models.task import Task
        logger.info("✅ 模型导入成功")
        
        # 测试工具导入
        from app.utils.timezone import get_china_time
        from app.utils.validation import InputValidator
        from app.utils.cache_manager import CacheManager
        logger.info("✅ 工具模块导入成功")
        
        # 测试服务导入
        from app.services.database_service import DatabaseService
        from app.services.task_executor import TaskExecutor
        logger.info("✅ 服务模块导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 导入测试失败: {e}")
        return False

def test_database_operations():
    """测试数据库操作"""
    try:
        logger.info("测试数据库操作...")
        
        from app import create_app, db
        from app.models.user import User
        
        # 创建测试应用
        app = create_app('testing')
        
        with app.app_context():
            # 创建表
            db.create_all()
            
            # 测试用户创建
            user = User(
                username='test_user',
                password='test_password'
            )
            db.session.add(user)
            db.session.commit()
            
            # 测试查询
            found_user = User.query.filter_by(username='test_user').first()
            assert found_user is not None
            assert found_user.username == 'test_user'
            
            # 清理
            db.session.delete(found_user)
            db.session.commit()
            
            logger.info("✅ 数据库操作测试成功")
            return True
            
    except Exception as e:
        logger.error(f"❌ 数据库操作测试失败: {e}")
        return False

def test_utility_functions():
    """测试工具函数"""
    try:
        logger.info("测试工具函数...")
        
        from app.utils.timezone import get_china_time, format_china_time
        from app.utils.validation import InputValidator
        from datetime import datetime
        
        # 测试时区函数
        now = now()
        china_time = get_china_time()
        formatted_time = format_china_time(now)
        
        assert china_time is not None
        assert formatted_time is not None
        
        # 测试验证函数
        validator = InputValidator()
        valid_string = validator.validate_string('test', min_length=1, max_length=10)
        assert valid_string == 'test'
        
        valid_email = validator.validate_email('test@example.com')
        assert valid_email == 'test@example.com'
        
        logger.info("✅ 工具函数测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 工具函数测试失败: {e}")
        return False

def test_service_classes():
    """测试服务类"""
    try:
        logger.info("测试服务类...")
        
        from app.services.database_service import DatabaseService
        from app.services.task_executor import TaskExecutor
        from app.utils.cache_manager import CacheManager
        from app.utils.retry_manager import RetryManager
        
        # 测试服务类实例化
        db_service = DatabaseService()
        task_executor = TaskExecutor()
        from app import cache
        cache_manager = CacheManager(cache)
        retry_manager = RetryManager()
        
        assert db_service is not None
        assert task_executor is not None
        assert cache_manager is not None
        assert retry_manager is not None
        
        logger.info("✅ 服务类测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务类测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("泰摸鱼吧 - 简化测试开始")
    logger.info("=" * 60)
    
    tests = [
        ("基本导入测试", test_basic_imports),
        ("数据库操作测试", test_database_operations),
        ("工具函数测试", test_utility_functions),
        ("服务类测试", test_service_classes)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n运行测试: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 通过")
            else:
                failed += 1
                logger.error(f"❌ {test_name} 失败")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name} 异常: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    logger.info(f"总测试数: {len(tests)}")
    logger.info(f"通过数: {passed}")
    logger.info(f"失败数: {failed}")
    logger.info(f"成功率: {passed/len(tests)*100:.1f}%")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！")
        return True
    else:
        logger.error("❌ 部分测试失败")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
