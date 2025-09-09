#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 最小化测试脚本
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

def test_models():
    """测试模型"""
    try:
        logger.info("测试模型...")
        
        # 直接导入模型，不通过app
        from app.models.user import User
        from app.models.instance import Instance
        from app.models.credential import Credential
        from app.models.task import Task
        from app.models.account import Account
        from app.models.log import Log
        from app.models.sync_data import SyncData
        
        logger.info("✅ 模型导入成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型测试失败: {e}")
        return False

def test_utils():
    """测试工具模块"""
    try:
        logger.info("测试工具模块...")
        
        from app.utils.timezone import get_china_time, format_china_time
        from app.utils.validation import InputValidator
        from app.utils.cache_manager import CacheManager
        from app.utils.retry_manager import RetryManager
        from app.utils.query_optimizer import QueryOptimizer
        from app.utils.api_response import APIResponse
        from app.utils.config_manager import AppConfigManager
        
        # 测试时区函数
        from datetime import datetime
        now = now()
        china_time = get_china_time(now)
        formatted_time = format_china_time(now)
        
        assert china_time is not None
        assert formatted_time is not None
        
        # 测试验证器
        validator = InputValidator()
        valid_string = validator.validate_string('test', min_length=1, max_length=10)
        assert valid_string == 'test'
        
        # 测试缓存管理器
        cache_manager = CacheManager()
        cache_manager.set('test_key', 'test_value')
        value = cache_manager.get('test_key')
        assert value == 'test_value'
        
        logger.info("✅ 工具模块测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 工具模块测试失败: {e}")
        return False

def test_services():
    """测试服务模块"""
    try:
        logger.info("测试服务模块...")
        
        from app.services.database_service import DatabaseService
        from app.services.task_executor import TaskExecutor
        
        # 测试服务实例化
        db_service = DatabaseService()
        task_executor = TaskExecutor()
        
        assert db_service is not None
        assert task_executor is not None
        
        logger.info("✅ 服务模块测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 服务模块测试失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        logger.info("测试数据库连接...")
        
        # 直接测试数据库连接，不通过Flask应用
        import sqlite3
        from pathlib import Path
        
        # 创建测试数据库
        test_db_path = Path('userdata/test.db')
        test_db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(test_db_path))
        cursor = conn.cursor()
        
        # 创建测试表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        
        # 插入测试数据
        cursor.execute('INSERT INTO test_table (name) VALUES (?)', ('test',))
        conn.commit()
        
        # 查询测试数据
        cursor.execute('SELECT * FROM test_table WHERE name = ?', ('test',))
        result = cursor.fetchone()
        assert result is not None
        assert result[1] == 'test'
        
        # 清理
        cursor.execute('DROP TABLE test_table')
        conn.close()
        test_db_path.unlink()
        
        logger.info("✅ 数据库连接测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    try:
        logger.info("测试文件结构...")
        
        required_files = [
            'app/__init__.py',
            'app/models/user.py',
            'app/models/instance.py',
            'app/models/credential.py',
            'app/models/task.py',
            'app/services/database_service.py',
            'app/services/task_executor.py',
            'app/utils/timezone.py',
            'app/utils/validation.py',
            'app/utils/cache_manager.py',
            'app/utils/retry_manager.py',
            'app/utils/query_optimizer.py',
            'app/utils/api_response.py',
            'app/utils/config_manager.py',
            'app/utils/test_runner.py',
            'requirements.txt',
            'README.md'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ 缺少文件: {missing_files}")
            return False
        
        logger.info("✅ 文件结构测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 文件结构测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("泰摸鱼吧 - 最小化测试开始")
    logger.info("=" * 60)
    
    tests = [
        ("文件结构测试", test_file_structure),
        ("模型测试", test_models),
        ("工具模块测试", test_utils),
        ("服务模块测试", test_services),
        ("数据库连接测试", test_database_connection)
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
