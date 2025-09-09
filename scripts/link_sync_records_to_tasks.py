#!/usr/bin/env python3
"""
泰摸鱼吧 - 关联同步记录到任务脚本
用于将未关联任务ID的同步记录关联到对应的任务
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app import db
from app.models.task import Task
from app.models.sync_data import SyncData
from app.models.instance import Instance

def link_sync_records_to_tasks():
    """关联同步记录到任务"""
    app = create_app()
    with app.app_context():
        print('=== 关联同步记录到任务 ===')
        
        # 获取所有任务
        tasks = Task.query.all()
        print(f'总任务数: {len(tasks)}')
        
        for task in tasks:
            print(f'\\n处理任务: {task.name} (ID: {task.id})')
            print(f'  类型: {task.task_type}')
            print(f'  数据库类型: {task.db_type}')
            
            # 根据任务类型和数据库类型查找对应的实例
            if task.task_type == 'sync_accounts':
                # 查找相同数据库类型的实例
                instances = Instance.query.filter_by(db_type=task.db_type).all()
                instance_ids = [inst.id for inst in instances]
                
                print(f'  找到 {len(instances)} 个{task.db_type}实例: {[inst.name for inst in instances]}')
                
                # 查找这些实例的未关联同步记录
                unlinked_syncs = SyncData.query.filter(
                    SyncData.sync_type == 'task',
                    SyncData.instance_id.in_(instance_ids),
                    SyncData.task_id.is_(None)
                ).all()
                
                print(f'  找到 {len(unlinked_syncs)} 条未关联的同步记录')
                
                # 关联到当前任务
                linked_count = 0
                for sync in unlinked_syncs:
                    sync.task_id = task.id
                    linked_count += 1
                    print(f'    关联记录ID {sync.id}: {sync.sync_time} - {sync.status}')
                
                if linked_count > 0:
                    db.session.commit()
                    print(f'  ✅ 成功关联 {linked_count} 条记录到任务 {task.name}')
                else:
                    print(f'  ℹ️  没有需要关联的记录')
            else:
                print(f'  ℹ️  跳过非账户同步任务')
        
        # 验证结果
        print('\\n=== 验证关联结果 ===')
        for task in tasks:
            if task.task_type == 'sync_accounts':
                task_executions = SyncData.query.filter(
                    SyncData.sync_type == 'task',
                    SyncData.task_id == task.id
                ).count()
                
                print(f'{task.name}: {task_executions} 条执行记录')
        
        print('\\n关联完成！')

if __name__ == '__main__':
    link_sync_records_to_tasks()
