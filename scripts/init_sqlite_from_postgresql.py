#!/usr/bin/env python3
"""
SQLite 数据库初始化脚本
基于 init_postgresql.sql 文档重新初始化 SQLite 数据库
"""

import os
import sqlite3
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def init_sqlite_database():
    """初始化 SQLite 数据库"""

    # 数据库文件路径
    db_path = "userdata/taifish_dev.db"

    # 备份现有数据库
    if os.path.exists(db_path):
        backup_path = f"userdata/backups/taifish_dev_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.makedirs("userdata/backups", exist_ok=True)
        os.rename(db_path, backup_path)
        print(f"✅ 已备份现有数据库到: {backup_path}")

    # 创建新的数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 开始初始化 SQLite 数据库...")

    try:
        # 1. 创建用户表
        print("📝 创建用户表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at TIMESTAMP NOT NULL,
            last_login TIMESTAMP,
            is_active BOOLEAN NOT NULL
        )
        """
        )

        # 2. 创建数据库类型配置表
        print("📝 创建数据库类型配置表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS database_type_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            display_name VARCHAR(100) NOT NULL,
            driver VARCHAR(50) NOT NULL,
            default_port INTEGER NOT NULL,
            default_schema VARCHAR(50) NOT NULL,
            connection_timeout INTEGER,
            description TEXT,
            icon VARCHAR(50),
            color VARCHAR(20),
            features TEXT,
            is_active BOOLEAN,
            is_system BOOLEAN,
            sort_order INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
        )

        # 3. 创建凭据表
        print("📝 创建凭据表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            credential_type VARCHAR(50) NOT NULL,
            db_type VARCHAR(50),
            username VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            description TEXT,
            instance_ids TEXT,
            category_id INTEGER,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            deleted_at TIMESTAMP
        )
        """
        )

        # 4. 创建实例表
        print("📝 创建实例表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            db_type VARCHAR(50) NOT NULL,
            host VARCHAR(255) NOT NULL,
            port INTEGER NOT NULL,
            database_name VARCHAR(255),
            database_version VARCHAR(100),
            environment VARCHAR(20) NOT NULL,
            sync_count INTEGER NOT NULL DEFAULT 0,
            credential_id INTEGER,
            description TEXT,
            tags TEXT,
            status VARCHAR(20),
            is_active BOOLEAN NOT NULL,
            last_connected TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            deleted_at TIMESTAMP,
            FOREIGN KEY (credential_id) REFERENCES credentials(id)
        )
        """
        )

        # 5. 创建账户表
        print("📝 创建账户表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id INTEGER NOT NULL,
            username VARCHAR(255) NOT NULL,
            host VARCHAR(255),
            database_name VARCHAR(255),
            account_type VARCHAR(50),
            plugin VARCHAR(100),
            password_expired BOOLEAN DEFAULT FALSE,
            password_last_changed TIMESTAMP,
            is_locked BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            last_login TIMESTAMP,
            permissions TEXT,
            is_superuser BOOLEAN DEFAULT FALSE,
            can_grant BOOLEAN DEFAULT FALSE,
            user_id INTEGER,
            lock_date TIMESTAMP,
            expiry_date TIMESTAMP,
            default_tablespace VARCHAR(100),
            account_created_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instance_id) REFERENCES instances(id)
        )
        """
        )

        # 6. 创建账户分类表
        print("📝 创建账户分类表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS account_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            risk_level VARCHAR(20) NOT NULL,
            color VARCHAR(20),
            priority INTEGER,
            is_system BOOLEAN NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
        )

        # 7. 创建分类规则表
        print("📝 创建分类规则表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS classification_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification_id INTEGER NOT NULL,
            db_type VARCHAR(20) NOT NULL,
            rule_name VARCHAR(100) NOT NULL,
            rule_expression TEXT NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (classification_id) REFERENCES account_classifications(id)
        )
        """
        )

        # 8. 创建账户分类分配表
        print("📝 创建账户分类分配表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS account_classification_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            classification_id INTEGER NOT NULL,
            assigned_by INTEGER,
            assignment_type VARCHAR(20) NOT NULL DEFAULT 'auto',
            confidence_score REAL,
            notes TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (classification_id) REFERENCES account_classifications(id),
            FOREIGN KEY (assigned_by) REFERENCES users(id),
            UNIQUE(account_id, classification_id)
        )
        """
        )

        # 9. 创建权限配置表
        print("📝 创建权限配置表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS permission_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            db_type VARCHAR(50) NOT NULL,
            category VARCHAR(50) NOT NULL,
            permission_name VARCHAR(255) NOT NULL,
            description TEXT,
            is_active BOOLEAN,
            sort_order INTEGER,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            UNIQUE(db_type, category, permission_name)
        )
        """
        )

        # 10. 创建任务表
        print("📝 创建任务表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            task_type VARCHAR(50) NOT NULL,
            db_type VARCHAR(50) NOT NULL,
            schedule VARCHAR(100),
            description TEXT,
            python_code TEXT,
            config TEXT,
            is_active BOOLEAN NOT NULL,
            is_builtin BOOLEAN NOT NULL,
            last_run TIMESTAMP,
            last_run_at TIMESTAMP,
            last_status VARCHAR(20),
            last_message TEXT,
            run_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
        )

        # 11. 创建同步数据表
        print("📝 创建同步数据表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS sync_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type VARCHAR(50) NOT NULL,
            instance_id INTEGER,
            task_id INTEGER,
            data TEXT,
            sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'success',
            message TEXT,
            synced_count INTEGER DEFAULT 0,
            added_count INTEGER DEFAULT 0,
            removed_count INTEGER DEFAULT 0,
            modified_count INTEGER DEFAULT 0,
            error_message TEXT,
            records_count INTEGER DEFAULT 0,
            FOREIGN KEY (instance_id) REFERENCES instances(id),
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
        """
        )

        # 12. 创建账户变化表
        print("📝 创建账户变化表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS account_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_data_id INTEGER NOT NULL,
            instance_id INTEGER NOT NULL,
            change_type VARCHAR(20) NOT NULL,
            account_data TEXT NOT NULL,
            change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sync_data_id) REFERENCES sync_data(id),
            FOREIGN KEY (instance_id) REFERENCES instances(id)
        )
        """
        )

        # 13. 创建日志表
        print("📝 创建日志表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level VARCHAR(20) NOT NULL,
            log_type VARCHAR(50) NOT NULL,
            module VARCHAR(100),
            message TEXT NOT NULL,
            details TEXT,
            user_id INTEGER,
            ip_address VARCHAR(45),
            user_agent TEXT,
            source VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
        )

        # 14. 创建全局参数表
        print("📝 创建全局参数表...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS global_params (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            value TEXT,
            description TEXT,
            param_type VARCHAR(50) DEFAULT 'string',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # 创建索引
        print("📝 创建索引...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS ix_credentials_credential_type ON credentials(credential_type)",
            "CREATE INDEX IF NOT EXISTS ix_credentials_db_type ON credentials(db_type)",
            "CREATE INDEX IF NOT EXISTS ix_credentials_name ON credentials(name)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_instances_name ON instances(name)",
            "CREATE INDEX IF NOT EXISTS ix_instances_status ON instances(status)",
            "CREATE INDEX IF NOT EXISTS ix_instances_db_type ON instances(db_type)",
            "CREATE INDEX IF NOT EXISTS ix_instances_environment ON instances(environment)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_instance_id ON accounts(instance_id)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_is_active ON accounts(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_is_superuser ON accounts(is_superuser)",
            "CREATE INDEX IF NOT EXISTS idx_account_classification_assignments_account_id ON account_classification_assignments(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_classification_assignments_classification_id ON account_classification_assignments(classification_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_classification_assignments_is_active ON account_classification_assignments(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_permission_config_db_type ON permission_configs(db_type)",
            "CREATE INDEX IF NOT EXISTS idx_permission_config_category ON permission_configs(category)",
            "CREATE INDEX IF NOT EXISTS ix_tasks_db_type ON tasks(db_type)",
            "CREATE INDEX IF NOT EXISTS ix_tasks_task_type ON tasks(task_type)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_tasks_name ON tasks(name)",
            "CREATE INDEX IF NOT EXISTS idx_sync_data_sync_type ON sync_data(sync_type)",
            "CREATE INDEX IF NOT EXISTS idx_sync_data_instance_id ON sync_data(instance_id)",
            "CREATE INDEX IF NOT EXISTS idx_sync_data_task_id ON sync_data(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_sync_data_sync_time ON sync_data(sync_time)",
            "CREATE INDEX IF NOT EXISTS idx_sync_data_status ON sync_data(status)",
            "CREATE INDEX IF NOT EXISTS idx_account_changes_sync_data_id ON account_changes(sync_data_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_changes_instance_id ON account_changes(instance_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_changes_change_type ON account_changes(change_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_changes_change_time ON account_changes(change_time)",
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)",
            "CREATE INDEX IF NOT EXISTS idx_logs_log_type ON logs(log_type)",
            "CREATE INDEX IF NOT EXISTS idx_logs_module ON logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source)",
            "CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        print("✅ 数据库表结构创建完成！")

        # 提交事务
        conn.commit()
        print("🎉 SQLite 数据库初始化完成！")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_sqlite_database()
