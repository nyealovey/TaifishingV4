#!/usr/bin/env python3
"""
创建SQL Server和Oracle测试数据脚本
"""

import sys
import os
import signal
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Instance, Credential, db
from datetime import datetime

class TimeoutError(Exception):
    """超时异常"""
    pass

def timeout_handler(signum, frame):
    """超时处理函数"""
    raise TimeoutError("操作超时")

def with_timeout(seconds):
    """超时装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 设置信号处理器
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
                return result
            except TimeoutError:
                print(f"❌ 操作超时 ({seconds}秒)")
                return None
            finally:
                # 恢复原来的信号处理器
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

def create_test_data():
    """创建测试数据"""
    try:
        print("🔄 正在初始化应用...")
        app = create_app()
        
        with app.app_context():
            print("✅ 应用上下文已创建")
            print("🚀 开始创建SQL Server和Oracle测试数据...")
            
            # 1. 创建SQL Server实例
            print("📊 创建SQL Server实例...")
            sqlserver_instance = Instance(
                name="SQL Server测试实例",
                db_type="sqlserver",
                host="localhost",
                port=1433,
                database_name="master",
                description="SQL Server 2022 Express测试实例"
            )
            
            # 检查是否已存在
            existing_sqlserver = Instance.query.filter_by(
                name=sqlserver_instance.name,
                db_type="sqlserver"
            ).first()
            
            if not existing_sqlserver:
                db.session.add(sqlserver_instance)
                db.session.flush()  # 获取ID
                print(f"  ✅ SQL Server实例已创建 (ID: {sqlserver_instance.id})")
            else:
                sqlserver_instance = existing_sqlserver
                print(f"  ℹ️  SQL Server实例已存在 (ID: {sqlserver_instance.id})")
            
            # 2. 创建SQL Server凭据
            print("🔑 创建SQL Server凭据...")
            sqlserver_credential = Credential(
                instance_id=sqlserver_instance.id,
                username="sa",
                password="SqlServer2024!",
                description="SQL Server SA账户凭据"
            )
            
            # 检查是否已存在
            existing_sqlserver_cred = Credential.query.filter_by(
                instance_id=sqlserver_instance.id,
                username="sa"
            ).first()
            
            if not existing_sqlserver_cred:
                db.session.add(sqlserver_credential)
                print(f"  ✅ SQL Server凭据已创建 (ID: {sqlserver_credential.id})")
            else:
                print(f"  ℹ️  SQL Server凭据已存在 (ID: {existing_sqlserver_cred.id})")
            
            # 3. 创建Oracle实例
            print("📊 创建Oracle实例...")
            oracle_instance = Instance(
                name="Oracle测试实例",
                db_type="oracle",
                host="localhost",
                port=1521,
                database_name="XE",
                description="Oracle 21c Express Edition测试实例"
            )
            
            # 检查是否已存在
            existing_oracle = Instance.query.filter_by(
                name=oracle_instance.name,
                db_type="oracle"
            ).first()
            
            if not existing_oracle:
                db.session.add(oracle_instance)
                db.session.flush()  # 获取ID
                print(f"  ✅ Oracle实例已创建 (ID: {oracle_instance.id})")
            else:
                oracle_instance = existing_oracle
                print(f"  ℹ️  Oracle实例已存在 (ID: {oracle_instance.id})")
            
            # 4. 创建Oracle凭据
            print("🔑 创建Oracle凭据...")
            oracle_credential = Credential(
                instance_id=oracle_instance.id,
                username="system",
                password="oracle_pass",
                description="Oracle SYSTEM账户凭据"
            )
            
            # 检查是否已存在
            existing_oracle_cred = Credential.query.filter_by(
                instance_id=oracle_instance.id,
                username="system"
            ).first()
            
            if not existing_oracle_cred:
                db.session.add(oracle_credential)
                print(f"  ✅ Oracle凭据已创建 (ID: {oracle_credential.id})")
            else:
                print(f"  ℹ️  Oracle凭据已存在 (ID: {existing_oracle_cred.id})")
            
            # 提交所有更改
            print("💾 提交数据库更改...")
            db.session.commit()
            print("🎉 所有测试数据创建完成！")
            
            # 显示创建的实例
            print("\n📋 创建的实例列表:")
            instances = Instance.query.filter(
                Instance.name.in_(["SQL Server测试实例", "Oracle测试实例"])
            ).all()
            
            for instance in instances:
                print(f"  - {instance.name} ({instance.db_type}) - ID: {instance.id}")
                
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        if 'db' in locals():
            db.session.rollback()
        raise

if __name__ == "__main__":
    try:
        # 设置30秒超时
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        create_test_data()
        
        # 取消超时
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        
    except TimeoutError:
        print("❌ 脚本执行超时 (30秒)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 脚本执行失败: {e}")
        sys.exit(1)