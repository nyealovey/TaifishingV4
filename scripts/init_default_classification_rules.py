#!/usr/bin/env python3

"""
泰摸鱼吧 - 初始化默认分类规则
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from app import create_app, db
from app.models.account_classification import AccountClassification, ClassificationRule


def init_default_classification_rules():
    """初始化默认分类规则"""
    app = create_app()

    with app.app_context():
        print("开始初始化默认分类规则...")

        # 清空现有分类规则和分类
        print("清空现有分类规则和分类...")
        ClassificationRule.query.delete()
        AccountClassification.query.delete()
        db.session.commit()

        # 创建默认分类
        print("创建默认分类...")

        # Oracle分类
        oracle_super_classification = AccountClassification(
            name="oracle_super",
            description="Oracle特权账户",
            risk_level="critical",
            color="#dc3545",
            priority=90,
            is_system=True,
            is_active=True,
        )
        db.session.add(oracle_super_classification)

        oracle_grant_classification = AccountClassification(
            name="oracle_grant",
            description="Oracle高风险账户",
            risk_level="high",
            color="#fd7e14",
            priority=95,
            is_system=True,
            is_active=True,
        )
        db.session.add(oracle_grant_classification)

        # PostgreSQL分类
        postgresql_super_classification = AccountClassification(
            name="postgresql_super",
            description="PostgreSQL特权账户",
            risk_level="critical",
            color="#dc3545",
            priority=90,
            is_system=True,
            is_active=True,
        )
        db.session.add(postgresql_super_classification)

        postgresql_grant_classification = AccountClassification(
            name="postgresql_grant",
            description="PostgreSQL高风险账户",
            risk_level="high",
            color="#fd7e14",
            priority=95,
            is_system=True,
            is_active=True,
        )
        db.session.add(postgresql_grant_classification)

        # MySQL分类
        mysql_super_classification = AccountClassification(
            name="mysql_super",
            description="MySQL特权账户",
            risk_level="critical",
            color="#dc3545",
            priority=90,
            is_system=True,
            is_active=True,
        )
        db.session.add(mysql_super_classification)

        mysql_grant_classification = AccountClassification(
            name="mysql_grant",
            description="MySQL高风险账户",
            risk_level="high",
            color="#fd7e14",
            priority=95,
            is_system=True,
            is_active=True,
        )
        db.session.add(mysql_grant_classification)

        # SQL Server分类
        sqlserver_super_classification = AccountClassification(
            name="sqlserver_super",
            description="SQL Server特权账户",
            risk_level="critical",
            color="#dc3545",
            priority=90,
            is_system=True,
            is_active=True,
        )
        db.session.add(sqlserver_super_classification)

        sqlserver_grant_classification = AccountClassification(
            name="sqlserver_grant",
            description="SQL Server高风险账户",
            risk_level="high",
            color="#fd7e14",
            priority=95,
            is_system=True,
            is_active=True,
        )
        db.session.add(sqlserver_grant_classification)

        db.session.commit()
        print("✅ 默认分类创建完成")

        # 创建默认分类规则
        print("创建默认分类规则...")

        # Oracle规则
        oracle_super_rule = ClassificationRule(
            classification_id=oracle_super_classification.id,
            rule_name="oracle_super_rule",
            db_type="oracle",
            rule_expression="roles.DBA",
            is_active=True,
        )
        db.session.add(oracle_super_rule)

        oracle_grant_rule = ClassificationRule(
            classification_id=oracle_grant_classification.id,
            rule_name="oracle_grant_rule",
            db_type="oracle",
            rule_expression="system_privileges.GRANT ANY PRIVILEGE",
            is_active=True,
        )
        db.session.add(oracle_grant_rule)

        # PostgreSQL规则
        postgresql_super_rule = ClassificationRule(
            classification_id=postgresql_super_classification.id,
            rule_name="postgresql_super_rule",
            db_type="postgresql",
            rule_expression="role_attributes.SUPERUSER",
            is_active=True,
        )
        db.session.add(postgresql_super_rule)

        postgresql_grant_rule = ClassificationRule(
            classification_id=postgresql_grant_classification.id,
            rule_name="postgresql_grant_rule",
            db_type="postgresql",
            rule_expression="role_attributes.CREATEROLE",
            is_active=True,
        )
        db.session.add(postgresql_grant_rule)

        # MySQL规则
        mysql_super_rule = ClassificationRule(
            classification_id=mysql_super_classification.id,
            rule_name="mysql_super_rule",
            db_type="mysql",
            rule_expression="global_privileges.SUPER",
            is_active=True,
        )
        db.session.add(mysql_super_rule)

        mysql_grant_rule = ClassificationRule(
            classification_id=mysql_grant_classification.id,
            rule_name="mysql_grant_rule",
            db_type="mysql",
            rule_expression="global_privileges.GRANT OPTION",
            is_active=True,
        )
        db.session.add(mysql_grant_rule)

        # SQL Server规则
        sqlserver_super_rule = ClassificationRule(
            classification_id=sqlserver_super_classification.id,
            rule_name="sqlserver_super_rule",
            db_type="sqlserver",
            rule_expression="server_roles.sysadmin",
            is_active=True,
        )
        db.session.add(sqlserver_super_rule)

        sqlserver_grant_rule = ClassificationRule(
            classification_id=sqlserver_grant_classification.id,
            rule_name="sqlserver_grant_rule",
            db_type="sqlserver",
            rule_expression="database_roles.db_owner",
            is_active=True,
        )
        db.session.add(sqlserver_grant_rule)

        db.session.commit()
        print("✅ 默认分类规则创建完成")

        # 验证结果
        print("\n=== 初始化结果验证 ===")
        classifications = AccountClassification.query.all()
        print(f"分类数量: {len(classifications)}")
        for cls in classifications:
            print(f"- {cls.name}: {cls.description} (风险级别: {cls.risk_level})")

        rules = ClassificationRule.query.all()
        print(f"\n规则数量: {len(rules)}")
        for rule in rules:
            print(f"- {rule.rule_name} (数据库类型: {rule.db_type})")

        print("\n✅ 默认分类规则初始化完成！")


if __name__ == "__main__":
    init_default_classification_rules()
