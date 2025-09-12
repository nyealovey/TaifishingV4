#!/usr/bin/env python3
"""
泰摸鱼吧 - 数据库索引优化脚本
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app, db


def add_database_indexes():
    """添加数据库索引以优化查询性能"""

    app = create_app()
    with app.app_context():
        try:
            # 用户表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
            """
                )
            )

            # 实例表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_instances_db_type ON instances(db_type);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_instances_is_active ON instances(is_active);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_instances_credential_id ON instances(credential_id);
            """
                )
            )

            # 凭据表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_credentials_credential_type ON credentials(credential_type);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_credentials_db_type ON credentials(db_type);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_credentials_is_active ON credentials(is_active);
            """
                )
            )

            # 日志表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_logs_log_type ON logs(log_type);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module);
            """
                )
            )

            # 任务表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_tasks_instance_id ON tasks(instance_id);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_tasks_is_active ON tasks(is_active);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
            """
                )
            )

            # 同步数据表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_sync_data_instance_id ON sync_data(instance_id);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_sync_data_sync_time ON sync_data(sync_time);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_sync_data_status ON sync_data(status);
            """
                )
            )

            # 账户表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_accounts_instance_id ON accounts(instance_id);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username);
            """
                )
            )

            # 参数表索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_params_param_type ON params(param_type);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_params_is_active ON params(is_active);
            """
                )
            )

            # 复合索引
            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_logs_user_created ON logs(user_id, created_at);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_logs_type_created ON logs(log_type, created_at);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_instances_type_active ON instances(db_type, is_active);
            """
                )
            )

            db.session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_tasks_instance_active ON tasks(instance_id, is_active);
            """
                )
            )

            db.session.commit()
            print("✅ 数据库索引添加成功")

        except Exception as e:
            db.session.rollback()
            print(f"❌ 添加索引失败: {e}")
            raise


def analyze_query_performance():
    """分析查询性能"""

    app = create_app()
    with app.app_context():
        try:
            # 分析表统计信息
            result = db.session.execute(
                text(
                    """
                SELECT name FROM sqlite_master WHERE type='table';
            """
                )
            )

            tables = [row[0] for row in result.fetchall()]

            print("\n📊 数据库表分析:")
            for table in tables:
                if table.startswith("sqlite_"):
                    continue

                # 获取表行数
                count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                row_count = count_result.fetchone()[0]

                # 获取索引信息
                index_result = db.session.execute(
                    text(
                        f"""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND tbl_name='{table}'
                    AND name NOT LIKE 'sqlite_%';
                """
                    )
                )

                indexes = [row[0] for row in index_result.fetchall()]

                print(f"  📋 {table}: {row_count} 行, {len(indexes)} 个索引")
                for index in indexes:
                    print(f"    🔍 {index}")

        except Exception as e:
            print(f"❌ 分析查询性能失败: {e}")


if __name__ == "__main__":
    print("🚀 开始优化数据库性能...")
    add_database_indexes()
    analyze_query_performance()
    print("✅ 数据库性能优化完成")
