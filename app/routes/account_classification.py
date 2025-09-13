"""
泰摸鱼吧 - 账户分类管理路由
"""

import json

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

from app import db
from app.models.account_classification import (
    AccountClassification,
    AccountClassificationAssignment,
    ClassificationRule,
)
from app.services.account_classification_service import AccountClassificationService
from app.utils.decorators import create_required, delete_required, update_required, view_required
from app.utils.structlog_config import log_info, log_error, log_warning

account_classification_bp = Blueprint("account_classification", __name__, url_prefix="/account-classification")


@account_classification_bp.route("/")
@login_required
@view_required
def index() -> str:
    """账户分类管理首页"""
    return render_template("account_classification/index.html")


@account_classification_bp.route("/rules-page")
@login_required
@view_required
def rules() -> str:
    """规则管理页面"""
    return render_template("account_classification/rules.html")


@account_classification_bp.route("/classifications")
@login_required
@view_required
def get_classifications() -> "Response":
    """获取所有账户分类"""
    try:
        classifications = (
            AccountClassification.query.filter_by(is_active=True)
            .order_by(
                AccountClassification.priority.desc(),
                AccountClassification.created_at.desc(),
            )
            .all()
        )

        result = []
        for classification in classifications:
            # 计算该分类的规则数量
            rules_count = ClassificationRule.query.filter_by(
                classification_id=classification.id, is_active=True
            ).count()

            result.append(
                {
                    "id": classification.id,
                    "name": classification.name,
                    "description": classification.description,
                    "risk_level": classification.risk_level,
                    "color": classification.color,
                    "priority": classification.priority,
                    "is_system": classification.is_system,
                    "rules_count": rules_count,
                    "created_at": (classification.created_at.isoformat() if classification.created_at else None),
                    "updated_at": (classification.updated_at.isoformat() if classification.updated_at else None),
                }
            )

        return jsonify({"success": True, "classifications": result})

    except Exception as e:
        current_app.logger.error(f"获取账户分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/classifications", methods=["POST"])
@login_required
@create_required
def create_classification() -> "Response":
    """创建账户分类"""
    try:
        data = request.get_json()

        classification = AccountClassification(
            name=data["name"],
            description=data.get("description", ""),
            risk_level=data.get("risk_level", "medium"),
            color=data.get("color", "#6c757d"),
            priority=data.get("priority", 0),
            is_system=False,
        )

        db.session.add(classification)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "classification": {
                    "id": classification.id,
                    "name": classification.name,
                    "description": classification.description,
                    "risk_level": classification.risk_level,
                    "color": classification.color,
                    "priority": classification.priority,
                    "is_system": classification.is_system,
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建账户分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/classifications/<int:classification_id>")
@login_required
@view_required
def get_classification(classification_id: int) -> "Response":
    """获取单个账户分类"""
    try:
        classification = AccountClassification.query.get_or_404(classification_id)

        return jsonify(
            {
                "success": True,
                "classification": {
                    "id": classification.id,
                    "name": classification.name,
                    "description": classification.description,
                    "risk_level": classification.risk_level,
                    "color": classification.color,
                    "priority": classification.priority,
                    "is_system": classification.is_system,
                    "created_at": (classification.created_at.isoformat() if classification.created_at else None),
                    "updated_at": (classification.updated_at.isoformat() if classification.updated_at else None),
                },
            }
        )

    except Exception as e:
        current_app.logger.error(f"获取账户分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/classifications/<int:classification_id>", methods=["PUT"])
@login_required
@update_required
def update_classification(classification_id: int) -> "Response":
    """更新账户分类"""
    try:
        classification = AccountClassification.query.get_or_404(classification_id)
        data = request.get_json()

        classification.name = data["name"]
        classification.description = data.get("description", "")
        classification.risk_level = data.get("risk_level", "medium")
        classification.color = data.get("color", "#6c757d")
        classification.priority = data.get("priority", 0)

        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新账户分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/classifications/<int:classification_id>", methods=["DELETE"])
@login_required
@delete_required
def delete_classification(classification_id: int) -> "Response":
    """删除账户分类"""
    try:
        classification = AccountClassification.query.get_or_404(classification_id)

        # 系统分类不能删除
        if classification.is_system:
            return jsonify({"success": False, "error": "系统分类不能删除"})

        db.session.delete(classification)
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除账户分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules/filter")
@login_required
@view_required
def get_rules() -> "Response":
    """获取分类规则"""
    try:
        classification_id = request.args.get("classification_id", type=int)
        db_type = request.args.get("db_type")

        query = ClassificationRule.query.filter_by(is_active=True)

        if classification_id:
            query = query.filter_by(classification_id=classification_id)

        if db_type:
            query = query.filter_by(db_type=db_type)

        rules = query.order_by(ClassificationRule.created_at.desc()).all()

        result = []
        for rule in rules:
            result.append(
                {
                    "id": rule.id,
                    "rule_name": rule.rule_name,
                    "classification_id": rule.classification_id,
                    "classification_name": (rule.classification.name if rule.classification else None),
                    "db_type": rule.db_type,
                    "rule_expression": rule.rule_expression,
                    "is_active": rule.is_active,
                    "created_at": (rule.created_at.isoformat() if rule.created_at else None),
                    "updated_at": (rule.updated_at.isoformat() if rule.updated_at else None),
                }
            )

        return jsonify({"success": True, "rules": result})

    except Exception as e:
        current_app.logger.error(f"获取分类规则失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules")
@login_required
@view_required
def list_rules() -> "Response":
    """获取所有规则列表（按数据库类型分组）"""
    try:
        # 获取所有规则
        rules = ClassificationRule.query.filter_by(is_active=True).order_by(ClassificationRule.created_at.desc()).all()

        # 获取匹配账户数量
        service = AccountClassificationService()
        result = []
        for rule in rules:
            matched_count = service.get_rule_matched_accounts_count(rule.id)
            result.append(
                {
                    "id": rule.id,
                    "rule_name": rule.rule_name,
                    "classification_id": rule.classification_id,
                    "classification_name": (rule.classification.name if rule.classification else None),
                    "db_type": rule.db_type,
                    "rule_expression": rule.rule_expression,
                    "is_active": rule.is_active,
                    "matched_accounts_count": matched_count,
                    "created_at": (rule.created_at.isoformat() if rule.created_at else None),
                    "updated_at": (rule.updated_at.isoformat() if rule.updated_at else None),
                }
            )

        # 按数据库类型分组
        rules_by_db_type = {}
        for rule in result:
            db_type = rule.get("db_type", "unknown")
            if db_type not in rules_by_db_type:
                rules_by_db_type[db_type] = []
            rules_by_db_type[db_type].append(rule)

        return jsonify({"success": True, "rules_by_db_type": rules_by_db_type})

    except Exception as e:
        current_app.logger.error(f"获取规则列表失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules", methods=["POST"])
@login_required
@create_required
def create_rule() -> "Response":
    """创建分类规则"""
    try:
        data = request.get_json()

        # 将规则表达式对象转换为JSON字符串
        rule_expression_json = json.dumps(data["rule_expression"], ensure_ascii=False)

        rule = ClassificationRule(
            rule_name=data["rule_name"],
            classification_id=data["classification_id"],
            db_type=data["db_type"],
            rule_expression=rule_expression_json,
            is_active=True,
        )

        db.session.add(rule)
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建分类规则失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules/<int:rule_id>", methods=["GET"])
@login_required
@view_required
def get_rule(rule_id: int) -> "Response":
    """获取单个规则详情"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)

        # 解析规则表达式JSON字符串为对象
        try:
            rule_expression_obj = json.loads(rule.rule_expression) if rule.rule_expression else {}
        except (json.JSONDecodeError, TypeError):
            rule_expression_obj = {}

        rule_dict = {
            "id": rule.id,
            "rule_name": rule.rule_name,
            "classification_id": rule.classification_id,
            "classification_name": (rule.classification.name if rule.classification else None),
            "db_type": rule.db_type,
            "rule_expression": rule_expression_obj,  # 返回解析后的对象
            "is_active": rule.is_active,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
            "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
        }

        return jsonify({"success": True, "rule": rule_dict})

    except Exception as e:
        current_app.logger.error(f"获取规则详情失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules/<int:rule_id>", methods=["PUT"])
@login_required
@update_required
def update_rule(rule_id: int) -> "Response":
    """更新分类规则"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)
        data = request.get_json()

        # 将规则表达式对象转换为JSON字符串
        rule_expression_json = json.dumps(data["rule_expression"], ensure_ascii=False)

        rule.rule_name = data["rule_name"]
        rule.classification_id = data["classification_id"]
        rule.rule_expression = rule_expression_json
        rule.is_active = data.get("is_active", True)

        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新分类规则失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules/<int:rule_id>/matched-accounts", methods=["GET"])
@login_required
@view_required
def get_matched_accounts(rule_id: int) -> "Response":
    """获取规则匹配的账户"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)

        # 获取匹配的账户
        from app.services.account_classification_service import (
            AccountClassificationService,
        )

        classification_service = AccountClassificationService()

        # 获取所有账户
        from app.models.account import Account
        from app.models.instance import Instance

        all_accounts = (
            Account.query.join(Instance, Account.instance_id == Instance.id)
            .filter(Instance.db_type == rule.db_type)
            .all()
        )

        matched_accounts = []
        seen_accounts = set()  # 用于去重

        for account in all_accounts:
            # 检查账户是否匹配规则
            if classification_service.evaluate_rule(rule, account):
                # 对于MySQL，显示用户名@主机名
                if rule.db_type == "mysql" and account.host:
                    display_name = f"{account.username}@{account.host}"
                    # 使用用户名@主机名作为唯一标识
                    unique_key = f"{account.username}@{account.host}"
                else:
                    display_name = account.username
                    # 对于其他数据库类型，使用用户名作为唯一标识
                    unique_key = account.username

                # 避免重复显示
                if unique_key not in seen_accounts:
                    seen_accounts.add(unique_key)

                    # 获取账户的分类信息
                    account_classifications = []
                    if hasattr(account, "classifications") and account.classifications:
                        for classification in account.classifications:
                            account_classifications.append(
                                {"id": classification.id, "name": classification.name, "color": classification.color}
                            )

                    matched_accounts.append(
                        {
                            "id": account.id,
                            "username": account.username,  # 使用原始用户名
                            "display_name": display_name,  # 显示名称
                            "instance_name": (account.instance.name if account.instance else "未知实例"),
                            "instance_host": (account.instance.host if account.instance else "未知IP"),
                            "instance_environment": (account.instance.environment if account.instance else "unknown"),
                            "db_type": rule.db_type,
                            "is_locked": getattr(account, "is_locked", False),
                            "classifications": account_classifications,
                        }
                    )

        return jsonify({"success": True, "accounts": matched_accounts, "rule_name": rule.rule_name})

    except Exception as e:
        current_app.logger.error(f"获取匹配账户失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules/<int:rule_id>", methods=["DELETE"])
@login_required
@delete_required
def delete_rule(rule_id: int) -> "Response":
    """删除分类规则"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)

        db.session.delete(rule)
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除分类规则失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/assign", methods=["POST"])
@login_required
@update_required
def assign_classification() -> "Response":
    """分配账户分类"""
    try:
        data = request.get_json()

        service = AccountClassificationService()
        result = service.classify_account(data["account_id"], data["classification_id"], current_user.id)

        return jsonify({"success": True, "assignment_id": result})

    except Exception as e:
        current_app.logger.error(f"分配账户分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/auto-classify", methods=["POST"])
@login_required
@update_required
def auto_classify() -> "Response":
    """自动分类账户"""
    try:
        data = request.get_json()
        instance_id = data.get("instance_id")
        
        log_info("开始自动分类账户", module="account_classification", instance_id=instance_id)

        service = AccountClassificationService()
        result = service.auto_classify_accounts(instance_id)

        if result.get("success"):
            log_info(f"自动分类完成: {result.get('message', '分类成功')}", 
                    module="account_classification", 
                    instance_id=instance_id,
                    classified_count=result.get("classified_count", 0))
        else:
            log_error(f"自动分类失败: {result.get('error', '未知错误')}", 
                     module="account_classification", 
                     instance_id=instance_id)

        # 直接返回服务层的结果
        return jsonify(result)

    except Exception as e:
        log_error(f"自动分类异常: {str(e)}", module="account_classification", instance_id=instance_id)
        current_app.logger.error(f"自动分类失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/assignments")
@login_required
@view_required
def get_assignments() -> "Response":
    """获取账户分类分配"""
    try:
        assignments = (
            db.session.query(AccountClassificationAssignment, AccountClassification)
            .join(
                AccountClassification,
                AccountClassificationAssignment.classification_id == AccountClassification.id,
            )
            .filter(AccountClassificationAssignment.is_active)
            .all()
        )

        result = []
        for assignment, classification in assignments:
            result.append(
                {
                    "id": assignment.id,
                    "account_id": assignment.assigned_by,
                    "classification_id": assignment.classification_id,
                    "classification_name": classification.name,
                    "assigned_at": (assignment.assigned_at.isoformat() if assignment.assigned_at else None),
                }
            )

        return jsonify({"success": True, "assignments": result})

    except Exception as e:
        current_app.logger.error(f"获取账户分类分配失败: {e}")
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/assignments/<int:assignment_id>", methods=["DELETE"])
@login_required
@delete_required
def remove_assignment(assignment_id: int) -> "Response":
    """移除账户分类分配"""
    try:
        assignment = AccountClassificationAssignment.query.get_or_404(assignment_id)
        assignment.is_active = False
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"移除账户分类分配失败: {e}")
        return jsonify({"success": False, "error": f"移除分配失败: {str(e)}"})


@account_classification_bp.route("/permissions/<db_type>")
@login_required
@view_required
def get_permissions(db_type: str) -> "Response":
    """获取数据库权限列表"""
    try:
        permissions = _get_db_permissions(db_type)

        return jsonify({"success": True, "permissions": permissions})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def _get_db_permissions(db_type: str) -> dict:
    """获取数据库权限列表"""
    from app.models.permission_config import PermissionConfig

    # 从数据库获取权限配置
    permissions = PermissionConfig.get_permissions_by_db_type(db_type)

    return permissions
