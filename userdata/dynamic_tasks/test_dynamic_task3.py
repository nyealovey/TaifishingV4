"""
动态任务: test_dynamic_task3
创建时间: 2025-09-12T15:09:14.036142
"""

from app import create_app, db
import logging

logger = logging.getLogger(__name__)

def execute_task():
    from app import create_app, db
    import logging
    
    logger = logging.getLogger(__name__)
    app = create_app()
    with app.app_context():
        try:
            logger.info('测试任务开始执行')
            
            # 示例：查询用户数量
            from app.models.user import User
            user_count = User.query.count()
            
            result = f'当前用户数量: {user_count}'
            logger.info(result)
            return result
            
        except Exception as e:
            logger.error(f'任务执行失败: {e}')
            return f'任务执行失败: {e}'

def task_wrapper():
    """任务包装器"""
    try:
        logger.info(f"开始执行动态任务: test_dynamic_task3")
        result = execute_task()
        logger.info(f"动态任务 test_dynamic_task3 执行完成: {result}")
        return result
    except Exception as e:
        logger.error(f"动态任务 test_dynamic_task3 执行失败: {e}")
        return f"任务执行失败: {e}"
