#!/usr/bin/env python3
"""测试PostgreSQL规则匹配"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Account, Instance, ClassificationRule
from app.services.account_classification_service import AccountClassificationService
import json

def test_pgsql_rule_matching():
    app = create_app()
    with app.app_context():
        # 获取PostgreSQL规则
        pgsql_rule = ClassificationRule.query.filter_by(db_type='postgresql').first()
        if not pgsql_rule:
            print("没有找到PostgreSQL规则")
            return
        
        print(f"PostgreSQL规则: {pgsql_rule.rule_name}")
        print(f"规则表达式: {pgsql_rule.rule_expression}")
        
        # 获取PostgreSQL实例
        pgsql_instances = Instance.query.filter_by(db_type='postgresql').all()
        if not pgsql_instances:
            print("没有找到PostgreSQL实例")
            return
        
        # 获取PostgreSQL账户
        pgsql_accounts = Account.query.join(Instance).filter(Instance.db_type == 'postgresql').all()
        print(f"找到 {len(pgsql_accounts)} 个PostgreSQL账户")
        
        # 测试规则匹配
        service = AccountClassificationService()
        rule_expression = json.loads(pgsql_rule.rule_expression)
        
        matched_accounts = []
        for account in pgsql_accounts:
            print(f"\n测试账户: {account.username}")
            if account.permissions:
                permissions = json.loads(account.permissions)
                print(f"  角色属性: {permissions.get('role_attributes', [])}")
                print(f"  数据库权限: {permissions.get('database_privileges', [])}")
                print(f"  表空间权限: {permissions.get('tablespace_privileges', [])}")
                
                # 测试匹配
                is_match = service._evaluate_postgresql_rule(account, rule_expression)
                print(f"  匹配结果: {is_match}")
                
                if is_match:
                    matched_accounts.append(account.username)
            else:
                print(f"  无权限信息")
        
        print(f"\n匹配的账户: {matched_accounts}")

if __name__ == "__main__":
    test_pgsql_rule_matching()
