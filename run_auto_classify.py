#!/usr/bin/env python3
"""运行自动分类"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.account_classification_service import AccountClassificationService

def run_auto_classify():
    app = create_app()
    with app.app_context():
        service = AccountClassificationService()
        result = service.auto_classify_accounts()
        print("自动分类结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  消息: {result.get('message', '')}")
        if 'stats' in result:
            stats = result['stats']
            print(f"  处理账户数: {stats.get('total_accounts', 0)}")
            print(f"  匹配规则数: {stats.get('matched_rules', 0)}")
            print(f"  更新分类数: {stats.get('updated_classifications', 0)}")

if __name__ == "__main__":
    run_auto_classify()
