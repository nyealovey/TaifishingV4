#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试CSV数据验证
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.utils.validation import InputValidator
from app.models.credential import Credential

def test_csv_data():
    """测试CSV数据验证"""
    app = create_app()
    
    with app.app_context():
        print("=== 测试CSV数据验证 ===")
        
        # 您的原始数据（有问题）
        original_data = [
            ("mysql-prod-01", "oracle", "10.10.100.207", "1521", "production", "production", "生产环境MySQL主库", "1"),
            ("mysql-dev-01", "sqlserver", "10.10.14.142", "1433", "development", "development", "开发环境MySQL", "2"),
            ("postgres-test-01", "postgresql", "10.10.102.180", "5432", "testing", "testing", "测试环境PostgreSQL", "3")
        ]
        
        # 修正后的数据
        corrected_data = [
            ("mysql-prod-01", "mysql", "10.10.100.207", "3306", "production", "production", "生产环境MySQL主库", "1"),
            ("sqlserver-dev-01", "sqlserver", "10.10.14.142", "1433", "development", "development", "开发环境SQL Server", "2"),
            ("postgres-test-01", "postgresql", "10.10.102.180", "5432", "testing", "testing", "测试环境PostgreSQL", "3")
        ]
        
        print("\n--- 原始数据验证 ---")
        for i, (name, db_type, host, port, database_name, environment, description, credential_id) in enumerate(original_data):
            print(f"\n第 {i+1} 个实例: {name}")
            
            # 验证数据库类型
            validated_db_type = InputValidator.validate_db_type(db_type)
            if validated_db_type:
                print(f"  ✅ 数据库类型: {db_type} -> {validated_db_type}")
            else:
                print(f"  ❌ 数据库类型: {db_type} -> 验证失败")
            
            # 验证端口
            try:
                port_int = int(port)
                print(f"  ✅ 端口: {port}")
            except ValueError:
                print(f"  ❌ 端口: {port} -> 无效")
            
            # 验证凭据ID
            try:
                cred_id = int(credential_id)
                cred = Credential.query.get(cred_id)
                if cred:
                    print(f"  ✅ 凭据ID: {credential_id} -> {cred.name}")
                else:
                    print(f"  ❌ 凭据ID: {credential_id} -> 不存在")
            except ValueError:
                print(f"  ❌ 凭据ID: {credential_id} -> 无效")
        
        print("\n--- 修正后数据验证 ---")
        for i, (name, db_type, host, port, database_name, environment, description, credential_id) in enumerate(corrected_data):
            print(f"\n第 {i+1} 个实例: {name}")
            
            # 验证数据库类型
            validated_db_type = InputValidator.validate_db_type(db_type)
            if validated_db_type:
                print(f"  ✅ 数据库类型: {db_type} -> {validated_db_type}")
            else:
                print(f"  ❌ 数据库类型: {db_type} -> 验证失败")
            
            # 验证端口
            try:
                port_int = int(port)
                print(f"  ✅ 端口: {port}")
            except ValueError:
                print(f"  ❌ 端口: {port} -> 无效")
            
            # 验证凭据ID
            try:
                cred_id = int(credential_id)
                cred = Credential.query.get(cred_id)
                if cred:
                    print(f"  ✅ 凭据ID: {credential_id} -> {cred.name}")
                else:
                    print(f"  ❌ 凭据ID: {credential_id} -> 不存在")
            except ValueError:
                print(f"  ❌ 凭据ID: {credential_id} -> 无效")

if __name__ == '__main__':
    test_csv_data()
