#!/usr/bin/env python3
"""测试Oracle规则匹配"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Account, Instance, ClassificationRule
from app.services.account_classification_service import AccountClassificationService
import json

def test_oracle_rule_matching():
    app = create_app()
    with app.app_context():
        # 获取Oracle规则
        oracle_rule = ClassificationRule.query.filter_by(db_type='oracle').first()
        if not oracle_rule:
            print("没有找到Oracle规则")
            return
        
        print(f"Oracle规则: {oracle_rule.rule_name}")
        print(f"规则表达式: {oracle_rule.rule_expression}")
        
        # 获取Oracle实例
        oracle_instances = Instance.query.filter_by(db_type='oracle').all()
        if not oracle_instances:
            print("没有找到Oracle实例")
            return
        
        # 获取Oracle账户
        oracle_accounts = Account.query.join(Instance).filter(Instance.db_type == 'oracle').all()
        print(f"找到 {len(oracle_accounts)} 个Oracle账户")
        
        # 测试规则匹配
        service = AccountClassificationService()
        rule_expression = json.loads(oracle_rule.rule_expression)
        
        matched_accounts = []
        for account in oracle_accounts:
            print(f"\n测试账户: {account.username}")
            if account.permissions:
                permissions = json.loads(account.permissions)
                print(f"  角色: {permissions.get('roles', [])}")
                print(f"  系统权限: {permissions.get('system_privileges', [])[:5]}...")  # 只显示前5个
                
                # 测试匹配
                is_match = service._evaluate_oracle_rule(account, rule_expression)
                print(f"  匹配结果: {is_match}")
                
                if is_match:
                    matched_accounts.append(account.username)
            else:
                print(f"  无权限信息")
        
        print(f"\n匹配的账户: {matched_accounts}")

if __name__ == "__main__":
    test_oracle_rule_matching()
