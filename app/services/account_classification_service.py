# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户分类管理服务
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from app import db
from app.models.account_classification import (
    AccountClassification,
    ClassificationRule,
    AccountClassificationAssignment,
)
from app.models.account import Account
from app.models.instance import Instance
from app.models.user import User
from app.utils.enhanced_logger import log_operation


class AccountClassificationService:
    """账户分类管理服务"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_classification(
        self,
        name: str,
        description: str = None,
        risk_level: str = "medium",
        color: str = None,
        priority: int = 0,
    ) -> Dict[str, Any]:
        """创建账户分类"""
        try:
            # 检查分类名称是否已存在
            existing = AccountClassification.query.filter_by(name=name).first()
            if existing:
                return {"success": False, "error": f'分类名称 "{name}" 已存在'}

            classification = AccountClassification(
                name=name,
                description=description,
                risk_level=risk_level,
                color=color,
                priority=priority,
            )

            db.session.add(classification)
            db.session.commit()

            log_operation(
                "CREATE_CLASSIFICATION",
                details={
                    "classification_id": classification.id,
                    "classification_name": name,
                    "risk_level": risk_level,
                },
            )

            return {
                "success": True,
                "message": f'账户分类 "{name}" 创建成功',
                "classification": classification.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"创建账户分类失败: {e}")
            return {"success": False, "error": f"创建账户分类失败: {str(e)}"}

    def update_classification(self, classification_id: int, **kwargs) -> Dict[str, Any]:
        """更新账户分类"""
        try:
            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {"success": False, "error": "分类不存在"}

            # 更新字段
            for key, value in kwargs.items():
                if hasattr(classification, key):
                    setattr(classification, key, value)

            classification.updated_at = datetime.utcnow()
            db.session.commit()

            log_operation(
                "UPDATE_CLASSIFICATION",
                details={
                    "classification_id": classification_id,
                    "updated_fields": list(kwargs.keys()),
                },
            )

            return {
                "success": True,
                "message": f'账户分类 "{classification.name}" 更新成功',
                "classification": classification.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"更新账户分类失败: {e}")
            return {"success": False, "error": f"更新账户分类失败: {str(e)}"}

    def delete_classification(self, classification_id: int) -> Dict[str, Any]:
        """删除账户分类"""
        try:
            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {"success": False, "error": "分类不存在"}

            # 检查是否为系统分类
            if classification.is_system:
                return {"success": False, "error": "系统分类不能删除"}

            # 检查是否有关联的账户分配
            assignments_count = classification.account_assignments.filter_by(
                is_active=True
            ).count()
            if assignments_count > 0:
                return {
                    "success": False,
                    "error": f"无法删除分类，还有 {assignments_count} 个账户正在使用此分类",
                }

            classification_name = classification.name
            db.session.delete(classification)
            db.session.commit()

            log_operation(
                "DELETE_CLASSIFICATION",
                details={
                    "classification_id": classification_id,
                    "classification_name": classification_name,
                },
            )

            return {
                "success": True,
                "message": f'账户分类 "{classification_name}" 删除成功',
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"删除账户分类失败: {e}")
            return {"success": False, "error": f"删除账户分类失败: {str(e)}"}

    def create_rule(
        self,
        classification_id: int,
        db_type: str,
        rule_name: str,
        rule_expression: Dict[str, Any],
    ) -> Dict[str, Any]:
        """创建分类规则"""
        try:
            # 验证参数
            if (
                not classification_id
                or not db_type
                or not rule_name
                or not rule_expression
            ):
                return {"success": False, "error": "缺少必要参数"}

            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {"success": False, "error": "分类不存在"}

            # 检查规则名称是否已存在
            existing_rule = ClassificationRule.query.filter_by(
                rule_name=rule_name, db_type=db_type, is_active=True
            ).first()

            if existing_rule:
                return {"success": False, "error": f'规则名称 "{rule_name}" 已存在'}

            rule = ClassificationRule(
                classification_id=classification_id,
                db_type=db_type,
                rule_name=rule_name,
                rule_expression=json.dumps(rule_expression, ensure_ascii=False),
            )

            db.session.add(rule)
            db.session.commit()

            log_operation(
                "CREATE_CLASSIFICATION_RULE",
                details={
                    "rule_id": rule.id,
                    "classification_id": classification_id,
                    "db_type": db_type,
                    "rule_name": rule_name,
                },
            )

            return {
                "success": True,
                "message": f'规则 "{rule_name}" 创建成功',
                "rule": rule.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"创建分类规则失败: {e}")
            return {"success": False, "error": f"创建分类规则失败: {str(e)}"}

    def update_rule(self, rule_id: int, **kwargs) -> Dict[str, Any]:
        """更新分类规则"""
        try:
            rule = ClassificationRule.query.get(rule_id)
            if not rule:
                return {"success": False, "error": "规则不存在"}

            # 更新字段
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    if key == "rule_expression" and isinstance(value, dict):
                        rule.set_rule_expression(value)
                    else:
                        setattr(rule, key, value)

            rule.updated_at = datetime.utcnow()
            db.session.commit()

            log_operation(
                "UPDATE_CLASSIFICATION_RULE",
                details={"rule_id": rule_id, "updated_fields": list(kwargs.keys())},
            )

            return {
                "success": True,
                "message": f'规则 "{rule.rule_name}" 更新成功',
                "rule": rule.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"更新分类规则失败: {e}")
            return {"success": False, "error": f"更新分类规则失败: {str(e)}"}

    def delete_rule(self, rule_id: int) -> Dict[str, Any]:
        """删除分类规则"""
        try:
            rule = ClassificationRule.query.get(rule_id)
            if not rule:
                return {"success": False, "error": "规则不存在"}

            rule_name = rule.rule_name
            db.session.delete(rule)
            db.session.commit()

            log_operation(
                "DELETE_CLASSIFICATION_RULE",
                details={"rule_id": rule_id, "rule_name": rule_name},
            )

            return {"success": True, "message": f'规则 "{rule_name}" 删除成功'}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"删除分类规则失败: {e}")
            return {"success": False, "error": f"删除分类规则失败: {str(e)}"}

    def get_classifications(
        self, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """获取所有账户分类"""
        try:
            query = AccountClassification.query
            if not include_inactive:
                query = query.filter_by(is_active=True)

            classifications = query.order_by(
                AccountClassification.priority.desc(), AccountClassification.name
            ).all()

            return [classification.to_dict() for classification in classifications]

        except Exception as e:
            self.logger.error(f"获取账户分类失败: {e}")
            return []

    def get_classification_rules(
        self, classification_id: int = None, db_type: str = None
    ) -> List[Dict[str, Any]]:
        """获取分类规则"""
        try:
            query = ClassificationRule.query.filter_by(is_active=True)

            if classification_id:
                query = query.filter_by(classification_id=classification_id)

            if db_type:
                query = query.filter_by(db_type=db_type)

            rules = query.order_by(ClassificationRule.created_at.desc()).all()

            return [rule.to_dict() for rule in rules]

        except Exception as e:
            self.logger.error(f"获取分类规则失败: {e}")
            return []

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        try:
            rules = ClassificationRule.query.filter_by(is_active=True).all()

            result = []
            for rule in rules:
                rule_dict = rule.to_dict()
                # 添加分类名称
                if rule.classification:
                    rule_dict["classification_name"] = rule.classification.name
                result.append(rule_dict)

            return result

        except Exception as e:
            self.logger.error(f"获取所有规则失败: {e}")
            return []

    def classify_account(
        self,
        account_id: int,
        classification_id: int,
        assignment_type: str = "manual",
        assigned_by: int = None,
        notes: str = None,
    ) -> Dict[str, Any]:
        """为账户分配分类"""
        try:
            account = Account.query.get(account_id)
            if not account:
                return {"success": False, "error": "账户不存在"}

            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {"success": False, "error": "分类不存在"}

            # 检查是否已有该账户和分类的组合记录（包括非活跃的）
            existing_assignment = AccountClassificationAssignment.query.filter_by(
                account_id=account_id, classification_id=classification_id
            ).first()

            if existing_assignment:
                # 如果记录存在但非活跃，重新激活它
                if not existing_assignment.is_active:
                    existing_assignment.is_active = True
                    existing_assignment.assigned_by = assigned_by
                    existing_assignment.assignment_type = assignment_type
                    existing_assignment.notes = notes
                    existing_assignment.updated_at = datetime.utcnow()
                else:
                    # 如果记录已存在且活跃，更新信息
                    existing_assignment.assigned_by = assigned_by
                    existing_assignment.assignment_type = assignment_type
                    existing_assignment.notes = notes
                    existing_assignment.updated_at = datetime.utcnow()
            else:
                # 创建新分配
                assignment = AccountClassificationAssignment(
                    account_id=account_id,
                    classification_id=classification_id,
                    assigned_by=assigned_by,
                    assignment_type=assignment_type,
                    notes=notes,
                )
                db.session.add(assignment)

            db.session.commit()

            log_operation(
                "ASSIGN_ACCOUNT_CLASSIFICATION",
                details={
                    "account_id": account_id,
                    "classification_id": classification_id,
                    "assignment_type": assignment_type,
                },
            )

            return {
                "success": True,
                "message": f'账户 "{account.username}" 已分配到分类 "{classification.name}"',
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"分配账户分类失败: {e}")
            return {"success": False, "error": f"分配账户分类失败: {str(e)}"}

    def auto_classify_accounts(self, instance_id: int = None) -> Dict[str, Any]:
        """自动分类账户"""
        try:
            # 获取所有活跃的分类规则
            rules = ClassificationRule.query.filter_by(is_active=True).all()

            if not rules:
                return {"success": False, "error": "没有可用的分类规则"}

            # 获取需要分类的账户（包括已禁用的账户）
            query = Account.query
            if instance_id:
                query = query.filter_by(instance_id=instance_id)

            accounts = query.all()

            classified_count = 0
            errors = []

            for account in accounts:
                try:
                    # 先清除该账户的所有现有分类
                    self._clear_account_classifications(account.id)

                    # 根据账户的数据库类型获取对应的规则，按优先级排序
                    account_rules = [
                        rule
                        for rule in rules
                        if rule.db_type == account.instance.db_type
                    ]

                    if not account_rules:
                        continue

                    # 按分类优先级排序规则（优先级高的先匹配）
                    account_rules.sort(
                        key=lambda r: (
                            r.classification.priority if r.classification else 0
                        ),
                        reverse=True,
                    )

                    # 应用规则进行自动分类
                    classified = False
                    for rule in account_rules:
                        if self._evaluate_rule(account, rule):
                            # 分配分类
                            result = self.classify_account(
                                account.id,
                                rule.classification_id,
                                "auto",
                                None,  # assigned_by
                            )
                            if result["success"]:
                                classified_count += 1
                                classified = True
                                self.logger.info(
                                    f"账户 {account.username} 按优先级 {rule.classification.priority if rule.classification else 0} 的规则 {rule.rule_name} 分类到 {rule.classification.name if rule.classification else '未知分类'}"
                                )
                            # 移除break，允许匹配多个规则

                    # 如果没有规则匹配，账户保持未分类状态（已清除现有分类）
                    if not classified:
                        self.logger.debug(
                            f"账户 {account.username} 不满足任何规则，设置为未分类"
                        )

                except Exception as e:
                    errors.append(f"账户 {account.username}: {str(e)}")

            log_operation(
                "AUTO_CLASSIFY_ACCOUNTS",
                details={
                    "instance_id": instance_id,
                    "classified_count": classified_count,
                    "total_accounts": len(accounts),
                },
            )

            return {
                "success": True,
                "message": f"自动分类完成，成功分类 {classified_count} 个账户",
                "classified_count": classified_count,
                "total_accounts": len(accounts),
                "errors": errors,
            }

        except Exception as e:
            self.logger.error(f"自动分类账户失败: {e}")
            return {"success": False, "error": f"自动分类账户失败: {str(e)}"}

    def evaluate_rule(self, rule: ClassificationRule, account: Account) -> bool:
        """评估规则是否匹配账户 - 公共方法"""
        return self._evaluate_rule(account, rule)

    def _evaluate_rule(self, account: Account, rule: ClassificationRule) -> bool:
        """评估规则是否匹配账户"""
        try:
            rule_expression = rule.get_rule_expression()
            if not rule_expression:
                return False

            # 根据规则类型进行不同的匹配逻辑
            if rule_expression.get("type") == "mysql_permissions":
                return self._evaluate_mysql_rule(account, rule_expression)
            elif rule_expression.get("type") == "sqlserver_permissions":
                return self._evaluate_sqlserver_rule(account, rule_expression)
            elif rule_expression.get("type") == "postgresql_permissions":
                return self._evaluate_postgresql_rule(account, rule_expression)
            elif rule_expression.get("type") == "oracle_permissions":
                return self._evaluate_oracle_rule(account, rule_expression)
            else:
                self.logger.warning(f"不支持的规则类型: {rule_expression.get('type')}")
                return False

        except Exception as e:
            self.logger.error(f"评估规则失败: {e}")
            return False

    def _evaluate_mysql_rule(self, account: Account, rule_expression: dict) -> bool:
        """评估MySQL规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                self.logger.debug(f"账户 {account.username} 没有权限信息")
                return False

            permissions = json.loads(account.permissions)

            # 检查全局权限
            required_global = rule_expression.get("global_privileges", [])
            if required_global:
                actual_global = [
                    p["privilege"]
                    for p in permissions.get("global", [])
                    if p.get("granted", False)
                ]
                if not all(perm in actual_global for perm in required_global):
                    self.logger.debug(
                        f"账户 {account.username} 不满足全局权限要求: 需要 {required_global}, 实际 {actual_global}"
                    )
                    return False

            # 检查数据库权限
            required_db = rule_expression.get("database_privileges", [])
            if required_db:
                # 获取所有数据库的权限
                all_db_permissions = set()
                for db_perm in permissions.get("database", []):
                    all_db_permissions.update(db_perm.get("privileges", []))

                if not all(perm in all_db_permissions for perm in required_db):
                    self.logger.debug(
                        f"账户 {account.username} 不满足数据库权限要求: 需要 {required_db}, 实际 {list(all_db_permissions)}"
                    )
                    return False

            self.logger.info(f"账户 {account.username} 满足MySQL规则要求")
            return True

        except Exception as e:
            self.logger.error(f"评估MySQL规则失败: {e}")
            return False

    def _evaluate_sqlserver_rule(self, account: Account, rule_expression: dict) -> bool:
        """评估SQL Server规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                self.logger.debug(f"账户 {account.username} 没有权限信息")
                return False

            permissions = json.loads(account.permissions)

            # 检查服务器权限
            required_server_perms = rule_expression.get("server_permissions", [])
            if required_server_perms:
                actual_server_perms = [
                    p["permission"]
                    for p in permissions.get("server_permissions", [])
                    if p.get("granted", False)
                ]
                if not all(
                    perm in actual_server_perms for perm in required_server_perms
                ):
                    self.logger.debug(
                        f"账户 {account.username} 不满足服务器权限要求: 需要 {required_server_perms}, 实际 {actual_server_perms}"
                    )
                    return False

            # 检查服务器角色
            required_server_roles = rule_expression.get("server_roles", [])
            if required_server_roles:
                actual_server_roles = [
                    r["role"] for r in permissions.get("server_roles", [])
                ]
                if not all(
                    role in actual_server_roles for role in required_server_roles
                ):
                    self.logger.debug(
                        f"账户 {account.username} 不满足服务器角色要求: 需要 {required_server_roles}, 实际 {actual_server_roles}"
                    )
                    return False

            # 检查数据库角色
            required_db_roles = rule_expression.get("database_roles", [])
            if required_db_roles:
                # 获取所有数据库的角色
                all_db_roles = set()
                for db_role in permissions.get("database_roles", []):
                    all_db_roles.update(db_role.get("roles", []))

                if not all(role in all_db_roles for role in required_db_roles):
                    self.logger.debug(
                        f"账户 {account.username} 不满足数据库角色要求: 需要 {required_db_roles}, 实际 {list(all_db_roles)}"
                    )
                    return False

            # 检查数据库权限
            required_db_privs = rule_expression.get("database_privileges", [])
            if required_db_privs:
                # 获取所有数据库的权限
                all_db_permissions = set()
                for db_perm in permissions.get("database", []):
                    all_db_permissions.update(db_perm.get("privileges", []))

                if not all(perm in all_db_permissions for perm in required_db_privs):
                    self.logger.debug(
                        f"账户 {account.username} 不满足数据库权限要求: 需要 {required_db_privs}, 实际 {list(all_db_permissions)}"
                    )
                    return False

            self.logger.info(f"账户 {account.username} 满足SQL Server规则要求")
            return True

        except Exception as e:
            self.logger.error(f"评估SQL Server规则失败: {e}")
            return False

    def _clear_account_classifications(self, account_id: int) -> bool:
        """清除账户的所有现有分类"""
        try:
            from app.models.account_classification import (
                AccountClassificationAssignment,
            )

            # 删除该账户的所有活跃分类分配
            assignments = AccountClassificationAssignment.query.filter_by(
                account_id=account_id, is_active=True
            ).all()

            for assignment in assignments:
                assignment.is_active = False
                assignment.updated_at = datetime.utcnow()

            db.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"清除账户分类失败: {e}")
            db.session.rollback()
            return False

    def get_account_classifications(
        self, account_id: int = None
    ) -> List[Dict[str, Any]]:
        """获取账户分类分配"""
        try:
            query = AccountClassificationAssignment.query.filter_by(is_active=True)

            if account_id:
                query = query.filter_by(account_id=account_id)

            assignments = query.all()

            return [assignment.to_dict() for assignment in assignments]

        except Exception as e:
            self.logger.error(f"获取账户分类分配失败: {e}")
            return []

    def remove_account_classification(self, assignment_id: int) -> Dict[str, Any]:
        """移除账户分类分配"""
        try:
            assignment = AccountClassificationAssignment.query.get(assignment_id)
            if not assignment:
                return {"success": False, "error": "分配记录不存在"}

            assignment.is_active = False
            assignment.updated_at = datetime.utcnow()
            db.session.commit()

            log_operation(
                "REMOVE_ACCOUNT_CLASSIFICATION",
                details={
                    "assignment_id": assignment_id,
                    "account_id": assignment.account_id,
                    "classification_id": assignment.classification_id,
                },
            )

            return {"success": True, "message": "账户分类分配已移除"}

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"移除账户分类分配失败: {e}")
            return {"success": False, "error": f"移除账户分类分配失败: {str(e)}"}

    def get_rule_matched_accounts_count(self, rule_id):
        """获取规则匹配的账户数量"""
        try:
            from app.models.account import Account
            from app.models.account_classification import (
                ClassificationRule,
                AccountClassificationAssignment,
            )

            # 获取规则
            rule = ClassificationRule.query.get(rule_id)
            if not rule:
                return 0

            # 获取规则对应的分类
            classification = rule.classification
            if not classification:
                return 0

            # 重新运行规则评估，统计真正匹配该规则的账户数量
            matched_count = 0
            accounts = Account.query.all()

            for account in accounts:
                if self._evaluate_rule(account, rule):
                    matched_count += 1

            return matched_count

        except Exception as e:
            self.logger.error(f"获取规则匹配账户数量失败: {e}")
            return 0

    def _evaluate_postgresql_rule(
        self, account: Account, rule_expression: dict
    ) -> bool:
        """评估PostgreSQL规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                self.logger.debug(f"账户 {account.username} 没有权限信息")
                return False

            permissions = json.loads(account.permissions)

            # 检查角色属性权限
            required_role_attrs = rule_expression.get("role_attributes", [])
            for required_attr in required_role_attrs:
                if required_attr not in permissions.get("role_attributes", []):
                    self.logger.debug(
                        f"账户 {account.username} 缺少角色属性: {required_attr}"
                    )
                    return False

            # 检查数据库权限
            required_db_perms = rule_expression.get("database_privileges", [])
            for required_perm in required_db_perms:
                if required_perm not in permissions.get("database_privileges", []):
                    self.logger.debug(
                        f"账户 {account.username} 缺少数据库权限: {required_perm}"
                    )
                    return False

            # 检查表空间权限
            required_tablespace_perms = rule_expression.get("tablespace_privileges", [])
            for required_perm in required_tablespace_perms:
                if required_perm not in permissions.get("tablespace_privileges", []):
                    self.logger.debug(
                        f"账户 {account.username} 缺少表空间权限: {required_perm}"
                    )
                    return False

            self.logger.debug(f"账户 {account.username} 匹配PostgreSQL规则")
            return True

        except Exception as e:
            self.logger.error(f"评估PostgreSQL规则失败: {e}")
            return False

    def _evaluate_oracle_rule(self, account: Account, rule_expression: dict) -> bool:
        """评估Oracle规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                self.logger.debug(f"账户 {account.username} 没有权限信息")
                return False

            permissions = json.loads(account.permissions)

            # 检查角色
            required_roles = rule_expression.get("roles", [])
            if required_roles:
                account_roles = permissions.get("roles", [])
                for required_role in required_roles:
                    if required_role not in account_roles:
                        self.logger.debug(
                            f"账户 {account.username} 缺少角色: {required_role}"
                        )
                        return False

            # 检查系统权限
            required_system_perms = rule_expression.get("system_privileges", [])
            if required_system_perms:
                account_system_perms = permissions.get("system_privileges", [])
                for required_perm in required_system_perms:
                    if required_perm not in account_system_perms:
                        self.logger.debug(
                            f"账户 {account.username} 缺少系统权限: {required_perm}"
                        )
                        return False

            # 检查表空间权限
            required_tablespace_perms = rule_expression.get("tablespace_privileges", [])
            if required_tablespace_perms:
                account_tablespace_perms = permissions.get("tablespace_privileges", [])
                for required_perm in required_tablespace_perms:
                    if required_perm not in account_tablespace_perms:
                        self.logger.debug(
                            f"账户 {account.username} 缺少表空间权限: {required_perm}"
                        )
                        return False

            # 检查表空间配额
            required_tablespace_quotas = rule_expression.get("tablespace_quotas", [])
            if required_tablespace_quotas:
                account_tablespace_quotas = permissions.get("tablespace_quotas", [])
                for required_quota in required_tablespace_quotas:
                    if required_quota not in account_tablespace_quotas:
                        self.logger.debug(
                            f"账户 {account.username} 缺少表空间配额: {required_quota}"
                        )
                        return False

            # 如果没有任何要求，则默认匹配
            if not any(
                [
                    required_roles,
                    required_system_perms,
                    required_tablespace_perms,
                    required_tablespace_quotas,
                ]
            ):
                self.logger.debug(
                    f"账户 {account.username} 匹配Oracle规则（无特定要求）"
                )
                return True

            self.logger.debug(f"账户 {account.username} 匹配Oracle规则")
            return True

        except Exception as e:
            self.logger.error(f"评估Oracle规则失败: {e}")
            return False


# 全局实例
account_classification_service = AccountClassificationService()
