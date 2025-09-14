"""
泰摸鱼吧 - 账户分类管理服务
"""

import json
from datetime import datetime
from typing import Any

from app import db
from app.models.account import Account
from app.models.account_classification import (
    AccountClassification,
    AccountClassificationAssignment,
    ClassificationRule,
)
from app.models.instance import Instance
from app.services.classification_batch_service import ClassificationBatchService
from app.utils.structlog_config import log_error, log_info, log_warning


class AccountClassificationService:
    """账户分类管理服务"""

    def __init__(self) -> None:
        """初始化账户分类服务"""
        # 使用统一日志系统，不需要单独的logger

    def create_classification(
        self,
        name: str,
        description: str = None,
        risk_level: str = "medium",
        color: str = None,
        priority: int = 0,
    ) -> dict[str, Any]:
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

            log_info(
                "创建账户分类",
                module="account_classification",
                classification_id=classification.id,
                classification_name=name,
                risk_level=risk_level,
            )

            return {
                "success": True,
                "message": f'账户分类 "{name}" 创建成功',
                "classification": classification.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            log_error(f"创建账户分类失败: {e}", module="account_classification")
            return {"success": False, "error": f"创建账户分类失败: {str(e)}"}

    def update_classification(self, classification_id: int, **kwargs) -> dict[str, Any]:
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

            log_info(
                "更新账户分类",
                module="account_classification",
                classification_id=classification_id,
                updated_fields=list(kwargs.keys()),
            )

            return {
                "success": True,
                "message": f'账户分类 "{classification.name}" 更新成功',
                "classification": classification.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            log_error(f"更新账户分类失败: {e}", module="account_classification")
            return {"success": False, "error": f"更新账户分类失败: {str(e)}"}

    def delete_classification(self, classification_id: int) -> dict[str, Any]:
        """删除账户分类"""
        try:
            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {"success": False, "error": "分类不存在"}

            # 检查是否为系统分类
            if classification.is_system:
                return {"success": False, "error": "系统分类不能删除"}

            # 检查是否有关联的账户分配
            assignments_count = classification.account_assignments.filter_by(is_active=True).count()
            if assignments_count > 0:
                return {
                    "success": False,
                    "error": f"无法删除分类，还有 {assignments_count} 个账户正在使用此分类",
                }

            classification_name = classification.name
            db.session.delete(classification)
            db.session.commit()

            log_info(
                "删除账户分类",
                module="account_classification",
                classification_id=classification_id,
                classification_name=classification_name,
            )

            return {
                "success": True,
                "message": f'账户分类 "{classification_name}" 删除成功',
            }

        except Exception as e:
            db.session.rollback()
            log_error(f"删除账户分类失败: {e}", module="account_classification")
            return {"success": False, "error": f"删除账户分类失败: {str(e)}"}

    def create_rule(
        self,
        classification_id: int,
        db_type: str,
        rule_name: str,
        rule_expression: dict[str, Any],
    ) -> dict[str, Any]:
        """创建分类规则"""
        try:
            # 验证参数
            if not classification_id or not db_type or not rule_name or not rule_expression:
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

            log_info(
                "创建分类规则",
                module="account_classification",
                rule_id=rule.id,
                classification_id=classification_id,
                db_type=db_type,
                rule_name=rule_name,
            )

            return {
                "success": True,
                "message": f'规则 "{rule_name}" 创建成功',
                "rule": rule.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            log_error(f"创建分类规则失败: {e}", module="account_classification")
            return {"success": False, "error": f"创建分类规则失败: {str(e)}"}

    def update_rule(self, rule_id: int, **kwargs) -> dict[str, Any]:
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

            log_info(
                "更新分类规则", module="account_classification", rule_id=rule_id, updated_fields=list(kwargs.keys())
            )

            return {
                "success": True,
                "message": f'规则 "{rule.rule_name}" 更新成功',
                "rule": rule.to_dict(),
            }

        except Exception as e:
            db.session.rollback()
            log_error(f"更新分类规则失败: {e}", module="account_classification")
            return {"success": False, "error": f"更新分类规则失败: {str(e)}"}

    def delete_rule(self, rule_id: int) -> dict[str, Any]:
        """删除分类规则"""
        try:
            rule = ClassificationRule.query.get(rule_id)
            if not rule:
                return {"success": False, "error": "规则不存在"}

            rule_name = rule.rule_name
            db.session.delete(rule)
            db.session.commit()

            log_info("删除分类规则", module="account_classification", rule_id=rule_id, rule_name=rule_name)

            return {"success": True, "message": f'规则 "{rule_name}" 删除成功'}

        except Exception as e:
            db.session.rollback()
            log_error(f"删除分类规则失败: {e}", module="account_classification")
            return {"success": False, "error": f"删除分类规则失败: {str(e)}"}

    def get_classifications(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        """获取所有账户分类"""
        try:
            query = AccountClassification.query
            if not include_inactive:
                query = query.filter_by(is_active=True)

            classifications = query.order_by(AccountClassification.priority.desc(), AccountClassification.name).all()

            return [classification.to_dict() for classification in classifications]

        except Exception as e:
            log_error(f"获取账户分类失败: {e}", module="account_classification")
            return []

    def get_classification_rules(self, classification_id: int = None, db_type: str = None) -> list[dict[str, Any]]:
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
            log_error(f"获取分类规则失败: {e}", module="account_classification")
            return []

    def get_all_rules(self) -> list[dict[str, Any]]:
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
            log_error(f"获取所有规则失败: {e}", module="account_classification")
            return []

    def classify_account(
        self,
        account_id: int,
        classification_id: int,
        assignment_type: str = "manual",
        assigned_by: int = None,
        notes: str = None,
        batch_id: str = None,
        skip_log: bool = False,
    ) -> dict[str, Any]:
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
                    existing_assignment.batch_id = batch_id
                    existing_assignment.updated_at = datetime.utcnow()
                else:
                    # 如果记录已存在且活跃，更新信息
                    existing_assignment.assigned_by = assigned_by
                    existing_assignment.assignment_type = assignment_type
                    existing_assignment.notes = notes
                    existing_assignment.batch_id = batch_id
                    existing_assignment.updated_at = datetime.utcnow()
            else:
                # 创建新分配
                assignment = AccountClassificationAssignment(
                    account_id=account_id,
                    classification_id=classification_id,
                    assigned_by=assigned_by,
                    assignment_type=assignment_type,
                    notes=notes,
                    batch_id=batch_id,
                )
                db.session.add(assignment)

            db.session.commit()

            if not skip_log:
                log_info(
                    "分配账户分类",
                    module="account_classification",
                    account_id=account_id,
                    classification_id=classification_id,
                    assignment_type=assignment_type,
                )

            return {
                "success": True,
                "message": f'账户 "{account.username}" 已分配到分类 "{classification.name}"',
            }

        except Exception as e:
            db.session.rollback()
            log_error(f"分配账户分类失败: {e}", module="account_classification")
            return {"success": False, "error": f"分配账户分类失败: {str(e)}"}

    def auto_classify_accounts(
        self, instance_id: int = None, batch_type: str = "manual", created_by: int = None
    ) -> dict[str, Any]:
        """自动分类账户"""
        batch_id = None
        try:
            # 获取所有活跃的分类规则
            rules = ClassificationRule.query.filter_by(is_active=True).all()

            if not rules:
                return {"success": False, "error": "没有可用的分类规则"}

            # 获取需要分类的账户（只包括活跃实例的账户）
            query = Account.query.join(Instance).filter(
                Instance.is_active == True,
                Instance.deleted_at.is_(None),  # 排除已删除的实例
            )
            if instance_id:
                query = query.filter_by(instance_id=instance_id)

            accounts = query.all()

            # 创建批次记录
            batch_id = ClassificationBatchService.create_batch(
                batch_type=batch_type, created_by=created_by, total_rules=len(rules), active_rules=len(rules)
            )

            classified_accounts = 0  # 实际匹配的账户数（去重）
            total_matches = 0  # 总匹配次数
            failed_count = 0
            errors = []

            for account in accounts:
                try:
                    # 根据账户的数据库类型获取对应的规则，按优先级排序
                    account_rules = [rule for rule in rules if rule.db_type == account.instance.db_type]

                    if not account_rules:
                        continue

                    # 按分类优先级排序规则（优先级高的先匹配）
                    account_rules.sort(
                        key=lambda r: (r.classification.priority if r.classification else 0),
                        reverse=True,
                    )

                    # 获取当前账户的分类分配
                    current_assignments = AccountClassificationAssignment.query.filter_by(
                        account_id=account.id, is_active=True
                    ).all()
                    current_classification_ids = {assignment.classification_id for assignment in current_assignments}

                    # 应用规则进行自动分类，收集新的分类
                    new_classification_ids = set()
                    account_matched = False
                    for rule in account_rules:
                        if self._evaluate_rule(account, rule):
                            new_classification_ids.add(rule.classification_id)
                            total_matches += 1
                            if not account_matched:
                                classified_accounts += 1
                                account_matched = True

                    # 比较当前分类和新分类
                    if current_classification_ids != new_classification_ids:
                        # 分类有变化，更新账户记录
                        account.last_classified_at = datetime.utcnow()
                        account.last_classification_batch_id = batch_id

                        # 清除当前所有分类
                        for assignment in current_assignments:
                            assignment.is_active = False
                            assignment.updated_at = datetime.utcnow()

                        # 记录分类变化日志
                        if new_classification_ids:
                            classification_names = []
                            for cid in new_classification_ids:
                                classification = AccountClassification.query.get(cid)
                                if classification:
                                    classification_names.append(classification.name)

                            log_info(
                                f"账户 {account.username} 分类已更新: {', '.join(classification_names)}",
                                module="account_classification",
                                batch_id=batch_id,
                                account_id=account.id,
                                old_classifications=list(current_classification_ids),
                                new_classifications=list(new_classification_ids),
                            )
                        else:
                            log_info(
                                f"账户 {account.username} 已移除所有分类",
                                module="account_classification",
                                batch_id=batch_id,
                                account_id=account.id,
                                old_classifications=list(current_classification_ids),
                            )
                    else:
                        # 分类没有变化，不更新账户记录，但为了批次记录完整性，仍然记录当前分类
                        log_info(
                            f"账户 {account.username} 分类无变化，保持现有分类",
                            module="account_classification",
                            batch_id=batch_id,
                            account_id=account.id,
                            current_classifications=list(current_classification_ids),
                        )

                    # 无论分类是否有变化，都创建新的批次记录以保持批次完整性
                    # 先清除该账户的所有现有批次记录，避免重复
                    existing_batch_assignments = AccountClassificationAssignment.query.filter_by(
                        account_id=account.id, batch_id=batch_id
                    ).all()
                    for assignment in existing_batch_assignments:
                        db.session.delete(assignment)

                    # 创建新的批次记录
                    for classification_id in new_classification_ids:
                        assignment = AccountClassificationAssignment(
                            account_id=account.id,
                            classification_id=classification_id,
                            assigned_by=None,  # 自动分类
                            assignment_type="auto",
                            notes=None,
                            batch_id=batch_id,
                        )
                        db.session.add(assignment)

                except Exception as e:
                    failed_count += 1
                    error_msg = f"账户 {account.username}: {str(e)}"
                    errors.append(error_msg)
                    log_error(
                        f"账户分类失败: {error_msg}",
                        module="account_classification",
                        batch_id=batch_id,
                        account_id=account.id,
                        error=str(e),
                    )

            # 提交数据库事务
            db.session.commit()

            # 更新批次统计信息
            ClassificationBatchService.update_batch_stats(
                batch_id=batch_id,
                total_accounts=len(accounts),
                matched_accounts=classified_accounts,  # 使用实际匹配的账户数
                failed_accounts=failed_count,
            )

            # 完成批次
            ClassificationBatchService.complete_batch(
                batch_id=batch_id,
                status="completed" if not errors else "failed",
                error_message="; ".join(errors) if errors else None,
                batch_details={
                    "instance_id": instance_id,
                    "total_rules": len(rules),
                    "active_rules": len(rules),
                    "errors": errors,
                },
            )

            log_info(
                "自动分类账户完成",
                module="account_classification",
                batch_id=batch_id,
                instance_id=instance_id,
                classified_accounts=classified_accounts,
                total_matches=total_matches,
                failed_count=failed_count,
                total_accounts=len(accounts),
            )

            return {
                "success": True,
                "message": f"自动分类完成，成功分类 {classified_accounts} 个账户，共 {total_matches} 次匹配",
                "batch_id": batch_id,
                "classified_accounts": classified_accounts,
                "total_matches": total_matches,
                "failed_count": failed_count,
                "total_accounts": len(accounts),
                "errors": errors,
            }

        except Exception as e:
            # 如果批次已创建，标记为失败
            if batch_id:
                ClassificationBatchService.complete_batch(batch_id=batch_id, status="failed", error_message=str(e))

            log_error(f"自动分类账户失败: {e}", module="account_classification", batch_id=batch_id, error=str(e))
            return {"success": False, "error": f"自动分类账户失败: {str(e)}", "batch_id": batch_id}

    def evaluate_rule(self, rule: ClassificationRule, account: Account) -> bool:
        """评估规则是否匹配账户 - 公共方法"""
        return self._evaluate_rule(account, rule)

    def _evaluate_rule(self, account: Account, rule: ClassificationRule) -> bool:
        """评估规则是否匹配账户"""
        try:
            # 首先检查账户的数据库类型是否与规则的数据库类型匹配
            if account.instance.db_type != rule.db_type:
                return False

            rule_expression = rule.get_rule_expression()
            if not rule_expression:
                # 处理旧格式的规则表达式（字符串格式）
                return self._evaluate_legacy_rule(account, rule)

            # 根据规则类型进行不同的匹配逻辑
            if rule_expression.get("type") == "mysql_permissions":
                return self._evaluate_mysql_rule(account, rule_expression)
            if rule_expression.get("type") == "sqlserver_permissions":
                return self._evaluate_sqlserver_rule(account, rule_expression)
            if rule_expression.get("type") == "postgresql_permissions":
                return self._evaluate_postgresql_rule(account, rule_expression)
            if rule_expression.get("type") == "oracle_permissions":
                return self._evaluate_oracle_rule(account, rule_expression)
            log_warning(f"不支持的规则类型: {rule_expression.get('type')}", module="account_classification")
            return False

        except Exception as e:
            log_error(f"评估规则失败: {e}", module="account_classification")
            return False

    def _evaluate_legacy_rule(self, account: Account, rule: ClassificationRule) -> bool:
        """评估旧格式规则（字符串格式）"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                log_info(f"账户 {account.username} 没有权限信息", module="account_classification")
                return False

            permissions = json.loads(account.permissions)
            rule_expression = rule.rule_expression  # 直接使用字符串格式

            # 根据数据库类型和规则表达式进行匹配
            if rule.db_type == "sqlserver":
                if rule_expression == "server_roles.sysadmin":
                    # 检查是否有sysadmin角色
                    server_roles = permissions.get("server_roles", [])
                    if isinstance(server_roles, list) and "sysadmin" in server_roles:
                        log_info(
                            f"账户 {account.username} 匹配SQL Server规则: {rule_expression}",
                            module="account_classification",
                        )
                        return True
                elif rule_expression == "database_roles.db_owner":
                    # 检查是否有db_owner角色
                    database_roles = permissions.get("database_roles", {})
                    if isinstance(database_roles, dict):
                        for db_name, roles in database_roles.items():
                            if isinstance(roles, list) and "db_owner" in roles:
                                log_info(
                                    f"账户 {account.username} 匹配SQL Server规则: {rule_expression}",
                                    module="account_classification",
                                )
                                return True
                elif rule_expression.startswith("server_permissions."):
                    # 检查服务器权限
                    perm_name = rule_expression.split(".", 1)[1]
                    server_permissions = permissions.get("server_permissions", [])
                    if isinstance(server_permissions, list) and perm_name in server_permissions:
                        log_info(
                            f"账户 {account.username} 匹配SQL Server规则: {rule_expression}",
                            module="account_classification",
                        )
                        return True

            elif rule.db_type == "mysql":
                if rule_expression == "global_privileges.SUPER":
                    # 检查是否有SUPER权限
                    global_privileges = permissions.get("global_privileges", [])
                    if isinstance(global_privileges, list):
                        for perm in global_privileges:
                            if (
                                isinstance(perm, dict)
                                and perm.get("privilege") == "SUPER"
                                and perm.get("granted", False)
                            ):
                                log_info(
                                    f"账户 {account.username} 匹配MySQL规则: {rule_expression}",
                                    module="account_classification",
                                )
                                return True

            elif rule.db_type == "postgresql":
                if rule_expression == "role_attributes.CREATEROLE":
                    # 检查是否有CREATEROLE属性
                    role_attributes = permissions.get("role_attributes", [])
                    if isinstance(role_attributes, list) and "CREATEROLE" in role_attributes:
                        log_info(
                            f"账户 {account.username} 匹配PostgreSQL规则: {rule_expression}",
                            module="account_classification",
                        )
                        return True

            elif rule.db_type == "oracle":
                if rule_expression == "system_privileges.GRANT ANY PRIVILEGE":
                    # 检查是否有GRANT ANY PRIVILEGE权限
                    system_privileges = permissions.get("system_privileges", [])
                    if isinstance(system_privileges, list) and "GRANT ANY PRIVILEGE" in system_privileges:
                        log_info(
                            f"账户 {account.username} 匹配Oracle规则: {rule_expression}",
                            module="account_classification",
                        )
                        return True

            log_info(f"账户 {account.username} 不匹配规则: {rule_expression}", module="account_classification")
            return False

        except Exception as e:
            log_error(f"评估旧格式规则失败: {e}", module="account_classification")
            return False

    def _evaluate_mysql_rule(self, account: Account, rule_expression: dict) -> bool:
        """评估MySQL规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                return False

            permissions = json.loads(account.permissions)

            # 检查全局权限
            required_global = rule_expression.get("global_privileges", [])
            if required_global:
                actual_global = [
                    p["privilege"] for p in permissions.get("global_privileges", []) if p.get("granted", False)
                ]
                if not all(perm in actual_global for perm in required_global):
                    return False

            # 检查数据库权限
            required_db = rule_expression.get("database_privileges", [])
            if required_db:
                # 获取所有数据库的权限
                all_db_permissions = set()
                for db_perm in permissions.get("database_privileges", []):
                    all_db_permissions.update(db_perm.get("privileges", []))

                if not all(perm in all_db_permissions for perm in required_db):
                    return False

            # 只有匹配成功时才记录日志
            log_info(f"账户 {account.username} 满足MySQL规则要求", module="account_classification")
            return True

        except Exception as e:
            log_error(f"评估MySQL规则失败: {e}", module="account_classification")
            return False

    def _evaluate_sqlserver_rule(self, account: Account, rule_expression: dict) -> bool:
        """评估SQL Server规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                return False

            permissions = json.loads(account.permissions)
            operator = rule_expression.get("operator", "OR")  # 默认为OR逻辑

            # 收集所有匹配结果
            match_results = []

            # 检查服务器权限
            required_server_perms = rule_expression.get("server_permissions", [])
            if required_server_perms:
                # 处理两种格式：字符串数组或对象数组
                server_perms_data = permissions.get("server_permissions", [])
                if server_perms_data and isinstance(server_perms_data[0], str):
                    # 字符串数组格式
                    actual_server_perms = server_perms_data
                else:
                    # 对象数组格式
                    actual_server_perms = [
                        p["permission"] if isinstance(p, dict) else p
                        for p in server_perms_data
                        if isinstance(p, dict) and p.get("granted", False)
                    ]

                server_perms_match = all(perm in actual_server_perms for perm in required_server_perms)
                match_results.append(server_perms_match)

                if server_perms_match:
                    log_info(
                        f"账户 {account.username} 满足服务器权限要求: {required_server_perms}",
                        module="account_classification",
                    )

            # 检查服务器角色
            required_server_roles = rule_expression.get("server_roles", [])
            if required_server_roles:
                # 处理两种格式：字符串数组或对象数组
                server_roles_data = permissions.get("server_roles", [])
                if server_roles_data and isinstance(server_roles_data[0], str):
                    # 字符串数组格式
                    actual_server_roles = server_roles_data
                else:
                    # 对象数组格式
                    actual_server_roles = [r["role"] if isinstance(r, dict) else r for r in server_roles_data]

                server_roles_match = all(role in actual_server_roles for role in required_server_roles)
                match_results.append(server_roles_match)

                if server_roles_match:
                    log_info(
                        f"账户 {account.username} 满足服务器角色要求: {required_server_roles}",
                        module="account_classification",
                    )

            # 检查数据库角色
            required_db_roles = rule_expression.get("database_roles", [])
            if required_db_roles:
                # 获取所有数据库的角色
                all_db_roles = set()
                database_roles_data = permissions.get("database_roles", {})

                # 处理字典格式：{database: [roles]}
                if isinstance(database_roles_data, dict):
                    for db_name, roles in database_roles_data.items():
                        if isinstance(roles, list):
                            all_db_roles.update(roles)
                # 处理数组格式：[{database: db_name, roles: [roles]}]
                elif isinstance(database_roles_data, list):
                    for db_role in database_roles_data:
                        if isinstance(db_role, dict):
                            all_db_roles.update(db_role.get("roles", []))

                db_roles_match = all(role in all_db_roles for role in required_db_roles)
                match_results.append(db_roles_match)

                if db_roles_match:
                    log_info(
                        f"账户 {account.username} 满足数据库角色要求: {required_db_roles}",
                        module="account_classification",
                    )

            # 检查数据库权限
            required_db_privs = rule_expression.get("database_privileges", [])
            if required_db_privs:
                # 获取所有数据库的权限
                all_db_permissions = set()
                database_privileges_data = permissions.get("database_privileges", {})

                # 处理字典格式：{database: [privileges]}
                if isinstance(database_privileges_data, dict):
                    for db_name, privileges in database_privileges_data.items():
                        if isinstance(privileges, list):
                            all_db_permissions.update(privileges)
                # 处理数组格式：[{database: db_name, privileges: [privileges]}]
                elif isinstance(database_privileges_data, list):
                    for db_perm in database_privileges_data:
                        if isinstance(db_perm, dict):
                            all_db_permissions.update(db_perm.get("privileges", []))

                db_privs_match = all(perm in all_db_permissions for perm in required_db_privs)
                match_results.append(db_privs_match)

                if db_privs_match:
                    log_info(
                        f"账户 {account.username} 满足数据库权限要求: {required_db_privs}",
                        module="account_classification",
                    )

            # 根据操作符决定匹配逻辑
            if not match_results:
                # 如果没有任何要求，默认匹配
                log_info(f"账户 {account.username} 匹配SQL Server规则（无特定要求）", module="account_classification")
                return True

            if operator.upper() == "AND":
                # AND逻辑：所有条件都必须满足
                result = all(match_results)
            else:
                # OR逻辑：任一条件满足即可
                result = any(match_results)

            # 只有匹配成功时才记录日志
            if result:
                log_info(f"账户 {account.username} 满足SQL Server规则要求", module="account_classification")

            return result

        except Exception as e:
            log_error(f"评估SQL Server规则失败: {e}", module="account_classification")
            return False

    def _clear_account_classifications(self, account_id: int) -> bool:
        """清除账户的所有现有分类"""
        try:
            from app.models.account_classification import (
                AccountClassificationAssignment,
            )

            # 删除该账户的所有活跃分类分配
            assignments = AccountClassificationAssignment.query.filter_by(account_id=account_id, is_active=True).all()

            for assignment in assignments:
                assignment.is_active = False
                assignment.updated_at = datetime.utcnow()

            db.session.commit()
            return True

        except Exception as e:
            log_error(f"清除账户分类失败: {e}", module="account_classification")
            db.session.rollback()
            return False

    def get_account_classifications(self, account_id: int = None) -> list[dict[str, Any]]:
        """获取账户分类分配"""
        try:
            query = AccountClassificationAssignment.query.filter_by(is_active=True)

            if account_id:
                query = query.filter_by(account_id=account_id)

            assignments = query.all()

            return [assignment.to_dict() for assignment in assignments]

        except Exception as e:
            log_error(f"获取账户分类分配失败: {e}", module="account_classification")
            return []

    def remove_account_classification(self, assignment_id: int) -> dict[str, Any]:
        """移除账户分类分配"""
        try:
            assignment = AccountClassificationAssignment.query.get(assignment_id)
            if not assignment:
                return {"success": False, "error": "分配记录不存在"}

            assignment.is_active = False
            assignment.updated_at = datetime.utcnow()
            db.session.commit()

            log_info(
                "移除账户分类分配",
                module="account_classification",
                assignment_id=assignment_id,
                account_id=assignment.account_id,
                classification_id=assignment.classification_id,
            )

            return {"success": True, "message": "账户分类分配已移除"}

        except Exception as e:
            db.session.rollback()
            log_error(f"移除账户分类分配失败: {e}", module="account_classification")
            return {"success": False, "error": f"移除账户分类分配失败: {str(e)}"}

    def get_rule_matched_accounts_count(self, rule_id: int) -> int:
        """获取规则匹配的账户数量"""
        try:
            from app.models.account import Account
            from app.models.account_classification import (
                ClassificationRule,
            )

            # 获取规则
            rule = ClassificationRule.query.get(rule_id)
            if not rule:
                return 0

            # 获取规则对应的分类
            classification = rule.classification
            if not classification:
                return 0

            # 重新运行规则评估，统计真正匹配该规则的账户数量（只包括活跃实例的账户）
            matched_count = 0
            accounts = (
                Account.query.join(Instance)
                .filter(
                    Instance.is_active == True,
                    Instance.deleted_at.is_(None),  # 排除已删除的实例
                )
                .all()
            )

            for account in accounts:
                if self._evaluate_rule(account, rule):
                    matched_count += 1

            return matched_count

        except Exception as e:
            log_error(f"获取规则匹配账户数量失败: {e}", module="account_classification")
            return 0

    def _evaluate_postgresql_rule(self, account: Account, rule_expression: dict) -> bool:
        """评估PostgreSQL规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                return False

            permissions = json.loads(account.permissions)

            # 检查角色属性权限
            required_role_attrs = rule_expression.get("role_attributes", [])
            for required_attr in required_role_attrs:
                if required_attr not in permissions.get("role_attributes", []):
                    return False

            # 检查数据库权限
            required_db_perms = rule_expression.get("database_privileges", [])
            for required_perm in required_db_perms:
                if required_perm not in permissions.get("database_privileges", []):
                    return False

            # 检查表空间权限
            required_tablespace_perms = rule_expression.get("tablespace_privileges", [])
            for required_perm in required_tablespace_perms:
                if required_perm not in permissions.get("tablespace_privileges", []):
                    return False

            # 只有匹配成功时才记录日志
            log_info(f"账户 {account.username} 匹配PostgreSQL规则", module="account_classification")
            return True

        except Exception as e:
            log_error(f"评估PostgreSQL规则失败: {e}", module="account_classification")
            return False

    def _evaluate_oracle_rule(self, account: Account, rule_expression: dict) -> bool:
        """评估Oracle规则"""
        try:
            import json

            # 从本地数据库获取权限信息
            if not account.permissions:
                return False

            permissions = json.loads(account.permissions)

            # 检查角色
            required_roles = rule_expression.get("roles", [])
            if required_roles:
                account_roles = permissions.get("roles", [])
                for required_role in required_roles:
                    if required_role not in account_roles:
                        return False

            # 检查系统权限
            required_system_perms = rule_expression.get("system_privileges", [])
            if required_system_perms:
                account_system_perms = permissions.get("system_privileges", [])
                for required_perm in required_system_perms:
                    if required_perm not in account_system_perms:
                        return False

            # 检查表空间权限
            required_tablespace_perms = rule_expression.get("tablespace_privileges", [])
            if required_tablespace_perms:
                account_tablespace_perms = permissions.get("tablespace_privileges", [])
                for required_perm in required_tablespace_perms:
                    if required_perm not in account_tablespace_perms:
                        return False

            # 检查表空间配额
            required_tablespace_quotas = rule_expression.get("tablespace_quotas", [])
            if required_tablespace_quotas:
                account_tablespace_quotas = permissions.get("tablespace_quotas", [])
                for required_quota in required_tablespace_quotas:
                    if required_quota not in account_tablespace_quotas:
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
                log_info(f"账户 {account.username} 匹配Oracle规则（无特定要求）", module="account_classification")
                return True

            # 只有匹配成功时才记录日志
            log_info(f"账户 {account.username} 匹配Oracle规则", module="account_classification")
            return True

        except Exception as e:
            log_error(f"评估Oracle规则失败: {e}", module="account_classification")
            return False


# 全局实例
account_classification_service = AccountClassificationService()
