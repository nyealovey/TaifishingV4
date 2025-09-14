#!/usr/bin/env python3
"""
创建Oracle和SQL Server测试数据脚本
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from app import create_app, db
from app.models.account import Account
from app.models.credential import Credential
from app.models.instance import Instance
from app.models.sync_data import SyncData
from app.models.sync_instance_record import SyncInstanceRecord
from app.models.sync_session import SyncSession


def create_test_data():
    """创建测试数据"""
    app = create_app()

    with app.app_context():
        print("🔧 创建Oracle和SQL Server测试数据...")

        # 1. 创建Oracle凭据
        print("📝 创建Oracle凭据...")
        oracle_credential = Credential(
            name="Oracle测试凭据",
            credential_type="database",
            db_type="oracle",
            username="system",
            password="Oracle123",
            description="Oracle XE测试凭据",
        )
        db.session.add(oracle_credential)
        db.session.flush()  # 获取ID

        # 2. 创建SQL Server凭据
        print("📝 创建SQL Server凭据...")
        sqlserver_credential = Credential(
            name="SQL Server测试凭据",
            credential_type="database",
            db_type="sqlserver",
            username="sa",
            password="SqlServer123!",
            description="SQL Server Express测试凭据",
        )
        db.session.add(sqlserver_credential)
        db.session.flush()  # 获取ID

        # 3. 创建Oracle实例
        print("📝 创建Oracle实例...")
        oracle_instance = Instance(
            name="Oracle测试实例",
            db_type="oracle",
            host="localhost",
            port=1521,
            database_name="XE",
            credential_id=oracle_credential.id,
            description="Oracle XE测试实例",
        )
        db.session.add(oracle_instance)
        db.session.flush()  # 获取ID

        # 4. 创建SQL Server实例
        print("📝 创建SQL Server实例...")
        sqlserver_instance = Instance(
            name="SQL Server测试实例",
            db_type="sqlserver",
            host="localhost",
            port=1433,
            database_name="master",
            credential_id=sqlserver_credential.id,
            description="SQL Server Express测试实例",
        )
        db.session.add(sqlserver_instance)
        db.session.flush()  # 获取ID

        # 5. 创建一些测试账户（模拟同步后的数据）
        print("📝 创建测试账户...")

        # Oracle测试账户
        oracle_accounts = [
            Account(
                instance_id=oracle_instance.id,
                username="SYSTEM",
                host="localhost",
                is_active=True,
                permissions_json='{"roles": ["DBA"], "system_privileges": ["CREATE USER", "DROP USER", "GRANT ANY PRIVILEGE"]}',
                is_superuser=True,
                can_grant=True,
                last_sync_time=datetime.utcnow(),
            ),
            Account(
                instance_id=oracle_instance.id,
                username="SYS",
                host="localhost",
                is_active=True,
                permissions_json='{"roles": ["DBA"], "system_privileges": ["CREATE USER", "DROP USER", "GRANT ANY PRIVILEGE"]}',
                is_superuser=True,
                can_grant=True,
                last_sync_time=datetime.utcnow(),
            ),
        ]

        for account in oracle_accounts:
            db.session.add(account)

        # SQL Server测试账户
        sqlserver_accounts = [
            Account(
                instance_id=sqlserver_instance.id,
                username="sa",
                host="localhost",
                is_active=True,
                permissions_json='{"server_roles": ["sysadmin"], "server_permissions": ["CONTROL SERVER"]}',
                is_superuser=True,
                can_grant=True,
                last_sync_time=datetime.utcnow(),
            ),
            Account(
                instance_id=sqlserver_instance.id,
                username="BUILTIN\\Administrators",
                host="localhost",
                is_active=True,
                permissions_json='{"server_roles": ["sysadmin"], "server_permissions": ["CONTROL SERVER"]}',
                is_superuser=True,
                can_grant=True,
                last_sync_time=datetime.utcnow(),
            ),
        ]

        for account in sqlserver_accounts:
            db.session.add(account)

        # 6. 创建同步会话记录
        print("📝 创建同步会话记录...")
        sync_session = SyncSession(
            session_id="test-oracle-sqlserver-session",
            sync_type="manual_batch",
            sync_category="account",
            status="completed",
            created_by=1,  # admin用户
            total_instances=2,
            success_count=2,
            failed_count=0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )
        db.session.add(sync_session)
        db.session.flush()  # 获取ID

        # 7. 创建同步实例记录
        print("📝 创建同步实例记录...")
        oracle_record = SyncInstanceRecord(
            session_id=sync_session.session_id,
            instance_id=oracle_instance.id,
            instance_name=oracle_instance.name,
            status="completed",
            accounts_synced=2,
            accounts_created=2,
            accounts_updated=0,
            accounts_deleted=0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )
        db.session.add(oracle_record)

        sqlserver_record = SyncInstanceRecord(
            session_id=sync_session.session_id,
            instance_id=sqlserver_instance.id,
            instance_name=sqlserver_instance.name,
            status="completed",
            accounts_synced=2,
            accounts_created=2,
            accounts_updated=0,
            accounts_deleted=0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
        )
        db.session.add(sqlserver_record)

        # 8. 创建同步数据记录
        print("📝 创建同步数据记录...")
        oracle_sync_data = SyncData(
            sync_type="batch",
            instance_id=oracle_instance.id,
            task_id=None,
            data={"db_type": "oracle", "instance_name": oracle_instance.name, "session_id": sync_session.session_id},
            status="completed",
            message="成功同步 2 个ORACLE账户",
            synced_count=2,
            added_count=2,
            removed_count=0,
            modified_count=0,
            records_count=2,
            session_id=sync_session.session_id,
            sync_category="account",
        )
        db.session.add(oracle_sync_data)

        sqlserver_sync_data = SyncData(
            sync_type="batch",
            instance_id=sqlserver_instance.id,
            task_id=None,
            data={
                "db_type": "sqlserver",
                "instance_name": sqlserver_instance.name,
                "session_id": sync_session.session_id,
            },
            status="completed",
            message="成功同步 2 个SQLSERVER账户",
            synced_count=2,
            added_count=2,
            removed_count=0,
            modified_count=0,
            records_count=2,
            session_id=sync_session.session_id,
            sync_category="account",
        )
        db.session.add(sqlserver_sync_data)

        # 提交所有更改
        db.session.commit()

        print("✅ Oracle和SQL Server测试数据创建完成！")
        print(f"📊 创建了 {len(oracle_accounts)} 个Oracle账户")
        print(f"📊 创建了 {len(sqlserver_accounts)} 个SQL Server账户")
        print("📊 创建了 1 个同步会话")
        print("📊 创建了 2 个同步实例记录")
        print("📊 创建了 2 个同步数据记录")


if __name__ == "__main__":
    create_test_data()
