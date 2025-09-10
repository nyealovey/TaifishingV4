#!/usr/bin/env python3
"""运行PostgreSQL自动分类"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.account_classification_service import AccountClassificationService

def run_pgsql_classification():
    app = create_app()
    with app.app_context():
        service = AccountClassificationService()
        
        # 只对PostgreSQL实例进行自动分类
        from app.models import Instance
        pgsql_instances = Instance.query.filter_by(db_type='postgresql').all()
        
        for instance in pgsql_instances:
            print(f"对PostgreSQL实例 {instance.name} 进行自动分类...")
            result = service.auto_classify_accounts(instance.id)
            print(f"  结果: {result.get('message', '')}")
            if 'stats' in result:
                stats = result['stats']
                print(f"  处理账户数: {stats.get('total_accounts', 0)}")
                print(f"  匹配规则数: {stats.get('matched_rules', 0)}")
                print(f"  更新分类数: {stats.get('updated_classifications', 0)}")

if __name__ == "__main__":
    run_pgsql_classification()
