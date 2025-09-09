#!/usr/bin/env python3
"""
初始化账户分类模板数据
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.account_classification import ClassificationTemplate, ClassificationRule, AccountClassification

def init_templates():
    """初始化分类模板"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建基础分类
            classifications = [
                {
                    'name': '特权账户',
                    'description': '具有高权限的数据库账户',
                    'risk_level': 'high',
                    'color': '#dc3545',
                    'priority': 90
                },
                {
                    'name': '普通账户',
                    'description': '普通业务账户',
                    'risk_level': 'medium',
                    'color': '#ffc107',
                    'priority': 50
                },
                {
                    'name': '只读账户',
                    'description': '仅具有查询权限的账户',
                    'risk_level': 'low',
                    'color': '#28a745',
                    'priority': 10
                },
                {
                    'name': '系统账户',
                    'description': '系统内部使用的账户',
                    'risk_level': 'critical',
                    'color': '#6f42c1',
                    'priority': 95
                }
            ]
            
            # 创建分类
            created_classifications = {}
            for cls_data in classifications:
                existing = AccountClassification.query.filter_by(name=cls_data['name']).first()
                if not existing:
                    classification = AccountClassification(
                        name=cls_data['name'],
                        description=cls_data['description'],
                        risk_level=cls_data['risk_level'],
                        color=cls_data['color'],
                        priority=cls_data['priority'],
                        is_active=True
                    )
                    db.session.add(classification)
                    db.session.flush()  # 获取ID
                    created_classifications[cls_data['name']] = classification.id
                    print(f"创建分类: {cls_data['name']}")
                else:
                    created_classifications[cls_data['name']] = existing.id
                    print(f"分类已存在: {cls_data['name']}")
            
            db.session.commit()
            
            # 创建MySQL模板
            mysql_template = ClassificationTemplate(
                name='MySQL安全分类模板',
                description='基于MySQL权限的安全分类规则模板',
                db_type='mysql',
                template_data='{"version": "1.0", "rules_count": 3}',
                is_active=True
            )
            db.session.add(mysql_template)
            db.session.flush()
            
            # MySQL规则
            mysql_rules = [
                {
                    'name': 'MySQL特权账户检测',
                    'description': '检测具有SUPER、CREATE USER、RELOAD等特权权限的账户',
                    'rule_config': {
                        'permissions': ['SUPER', 'CREATE USER', 'RELOAD', 'SHUTDOWN'],
                        'match_type': 'any'
                    },
                    'classification_name': '特权账户'
                },
                {
                    'name': 'MySQL只读账户检测',
                    'description': '检测仅具有SELECT权限的账户',
                    'rule_config': {
                        'permissions': ['SELECT'],
                        'exclude_permissions': ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER'],
                        'match_type': 'only'
                    },
                    'classification_name': '只读账户'
                },
                {
                    'name': 'MySQL系统账户检测',
                    'description': '检测系统内置账户',
                    'rule_config': {
                        'usernames': ['root', 'mysql.sys', 'mysql.session', 'mysql.infoschema'],
                        'match_type': 'exact'
                    },
                    'classification_name': '系统账户'
                }
            ]
            
            for rule_data in mysql_rules:
                rule = ClassificationRule(
                    rule_name=rule_data['name'],
                    db_type='mysql',
                    classification_id=created_classifications[rule_data['classification_name']],
                    rule_expression=json.dumps(rule_data['rule_config'], ensure_ascii=False),
                    is_active=True
                )
                db.session.add(rule)
            
            # 创建SQL Server模板
            sqlserver_template = ClassificationTemplate(
                name='SQL Server安全分类模板',
                description='基于SQL Server权限的安全分类规则模板',
                db_type='sqlserver',
                template_data='{"version": "1.0", "rules_count": 3}',
                is_active=True
            )
            db.session.add(sqlserver_template)
            db.session.flush()
            
            # SQL Server规则
            sqlserver_rules = [
                {
                    'name': 'SQL Server特权账户检测',
                    'description': '检测具有sysadmin、serveradmin等服务器角色的账户',
                    'rule_config': {
                        'roles': ['sysadmin', 'serveradmin', 'securityadmin'],
                        'match_type': 'any'
                    },
                    'classification_name': '特权账户'
                },
                {
                    'name': 'SQL Server只读账户检测',
                    'description': '检测仅具有db_datareader角色的账户',
                    'rule_config': {
                        'roles': ['db_datareader'],
                        'exclude_roles': ['db_datawriter', 'db_ddladmin', 'db_owner'],
                        'match_type': 'only'
                    },
                    'classification_name': '只读账户'
                },
                {
                    'name': 'SQL Server系统账户检测',
                    'description': '检测系统内置账户',
                    'rule_config': {
                        'usernames': ['sa', 'NT AUTHORITY\\SYSTEM', 'BUILTIN\\Administrators'],
                        'match_type': 'exact'
                    },
                    'classification_name': '系统账户'
                }
            ]
            
            for rule_data in sqlserver_rules:
                rule = ClassificationRule(
                    rule_name=rule_data['name'],
                    db_type='sqlserver',
                    classification_id=created_classifications[rule_data['classification_name']],
                    rule_expression=json.dumps(rule_data['rule_config'], ensure_ascii=False),
                    is_active=True
                )
                db.session.add(rule)
            
            db.session.commit()
            print("✅ 模板初始化完成！")
            print(f"创建了 {len(classifications)} 个分类")
            print(f"创建了 2 个模板")
            print(f"MySQL模板包含 {len(mysql_rules)} 个规则")
            print(f"SQL Server模板包含 {len(sqlserver_rules)} 个规则")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 初始化失败: {str(e)}")
            raise

if __name__ == '__main__':
    init_templates()
