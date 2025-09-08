#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 数据库性能优化索引
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def add_performance_indexes():
    """添加性能优化索引"""
    app = create_app()
    
    with app.app_context():
        try:
            # 日志表索引
            print("添加日志表性能索引...")
            
            # 复合索引：按时间范围查询
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_created_at_level 
                ON logs (created_at DESC, level)
            """))
            
            # 复合索引：按用户和时间查询
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_user_created_at 
                ON logs (user_id, created_at DESC)
            """))
            
            # 复合索引：按类型和时间查询
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_logs_type_created_at 
                ON logs (log_type, created_at DESC)
            """))
            
            # SQLite不支持全文搜索索引，跳过
            print("⚠ SQLite不支持全文搜索索引，跳过")
            
            # 用户表索引
            print("添加用户表性能索引...")
            
            # 用户名索引（已存在，但确保唯一性）
            db.session.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique 
                ON users (username)
            """))
            
            # 角色索引
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role 
                ON users (role)
            """))
            
            # 活跃状态索引
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_active 
                ON users (is_active)
            """))
            
            # 任务表索引（检查表是否存在）
            print("检查任务表索引...")
            try:
                # 检查任务表是否存在
                result = db.session.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='tasks'
                """))
                if result.fetchone():
                    # 任务创建时间索引
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_tasks_created_at 
                        ON tasks (created_at DESC)
                    """))
                    
                    # 任务用户索引
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_tasks_user_id 
                        ON tasks (user_id)
                    """))
                    print("✓ 任务表索引添加成功")
                else:
                    print("⚠ 任务表不存在，跳过任务索引")
            except Exception as e:
                print(f"⚠ 任务表索引创建失败: {e}")
            
            # 实例表索引（检查表是否存在）
            print("检查实例表索引...")
            try:
                # 检查实例表是否存在
                result = db.session.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='instances'
                """))
                if result.fetchone():
                    # 实例类型索引
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_instances_type 
                        ON instances (instance_type)
                    """))
                    
                    # 实例用户索引
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_instances_user_id 
                        ON instances (user_id)
                    """))
                    print("✓ 实例表索引添加成功")
                else:
                    print("⚠ 实例表不存在，跳过实例索引")
            except Exception as e:
                print(f"⚠ 实例表索引创建失败: {e}")
            
            # 提交事务
            db.session.commit()
            print("✓ 所有性能索引添加成功！")
            
            # 显示索引统计（SQLite版本）
            print("\n📊 索引统计信息:")
            result = db.session.execute(text("""
                SELECT name, sql
                FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
                ORDER BY name
            """))
            
            for row in result:
                print(f"  {row.name}")
            
        except Exception as e:
            print(f"❌ 添加索引失败: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    add_performance_indexes()
