# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户分类管理路由
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from app.services.account_classification_service import account_classification_service
from app.models.account_classification import AccountClassification, ClassificationRule
from app.models.account import Account
from app.models.instance import Instance
from app import db
import json

account_classification_bp = Blueprint(
    "account_classification", __name__, url_prefix="/account-classification"
)


@account_classification_bp.route("/")
@login_required
def index():
    """账户分类管理首页"""
    try:
        # 获取所有分类
        classifications = account_classification_service.get_classifications()

        # 获取所有实例
        instances = Instance.query.filter_by(is_active=True).all()

        # 获取数据库类型统计
        db_types = ["mysql", "postgresql", "sqlserver", "oracle"]
        db_type_stats = {}

        for db_type in db_types:
            rules_count = ClassificationRule.query.filter_by(
                db_type=db_type, is_active=True
            ).count()
            db_type_stats[db_type] = rules_count

        return render_template(
            "account_classification/index.html",
            classifications=classifications,
            instances=instances,
            db_type_stats=db_type_stats,
        )

    except Exception as e:
        flash(f"加载页面失败: {str(e)}", "error")
        return render_template(
            "account_classification/index.html",
            classifications=[],
            instances=[],
            db_type_stats={},
        )


@account_classification_bp.route("/rules-page")
@login_required
def rules():
    """规则管理页面"""
    try:
        # 获取所有规则
        all_rules = account_classification_service.get_all_rules()

        # 按数据库类型分组
        rules_by_db_type = {}
        for rule in all_rules:
            db_type = rule.get("db_type", "unknown")
            if db_type not in rules_by_db_type:
                rules_by_db_type[db_type] = []
            rules_by_db_type[db_type].append(rule)

        return render_template(
            "account_classification/rules.html", rules_by_db_type=rules_by_db_type
        )

    except Exception as e:
        flash(f"加载规则页面失败: {str(e)}", "error")
        return render_template("account_classification/rules.html", rules_by_db_type={})


@account_classification_bp.route("/classifications")
@login_required
def get_classifications():
    """获取所有账户分类"""
    try:
        classifications = account_classification_service.get_classifications()
        return jsonify({"success": True, "classifications": classifications})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/classifications", methods=["POST"])
@login_required
def create_classification():
    """创建账户分类"""
    try:
        data = request.get_json()

        result = account_classification_service.create_classification(
            name=data.get("name"),
            description=data.get("description"),
            risk_level=data.get("risk_level", "medium"),
            color=data.get("color"),
            priority=data.get("priority", 0),
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"创建分类失败: {str(e)}"})


@account_classification_bp.route("/classifications/<int:classification_id>")
@login_required
def get_classification(classification_id):
    """获取单个账户分类"""
    try:
        classification = AccountClassification.query.get(classification_id)
        if not classification:
            return jsonify({"success": False, "error": "分类不存在"})

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
                    "created_at": (
                        classification.created_at.isoformat()
                        if classification.created_at
                        else None
                    ),
                    "updated_at": (
                        classification.updated_at.isoformat()
                        if classification.updated_at
                        else None
                    ),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"获取分类失败: {str(e)}"})


@account_classification_bp.route(
    "/classifications/<int:classification_id>", methods=["PUT"]
)
@login_required
def update_classification(classification_id):
    """更新账户分类"""
    try:
        data = request.get_json()

        result = account_classification_service.update_classification(
            classification_id, **data
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"更新分类失败: {str(e)}"})


@account_classification_bp.route(
    "/classifications/<int:classification_id>", methods=["DELETE"]
)
@login_required
def delete_classification(classification_id):
    """删除账户分类"""
    try:
        result = account_classification_service.delete_classification(classification_id)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"删除分类失败: {str(e)}"})


@account_classification_bp.route("/rules/filter")
@login_required
def get_rules():
    """获取分类规则"""
    try:
        classification_id = request.args.get("classification_id", type=int)
        db_type = request.args.get("db_type")

        rules = account_classification_service.get_classification_rules(
            classification_id=classification_id, db_type=db_type
        )

        return jsonify({"success": True, "rules": rules})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules")
@login_required
def list_rules():
    """获取所有规则列表（按数据库类型分组）"""
    try:
        # 获取所有规则
        all_rules = account_classification_service.get_all_rules()

        # 为每个规则添加匹配的账户数量
        for rule in all_rules:
            rule_id = rule.get("id")
            if rule_id:
                matched_count = (
                    account_classification_service.get_rule_matched_accounts_count(
                        rule_id
                    )
                )
                rule["matched_accounts_count"] = matched_count
            else:
                rule["matched_accounts_count"] = 0

        # 按数据库类型分组
        rules_by_db_type = {}
        for rule in all_rules:
            db_type = rule.get("db_type", "unknown")
            if db_type not in rules_by_db_type:
                rules_by_db_type[db_type] = []
            rules_by_db_type[db_type].append(rule)

        return jsonify({"success": True, "rules_by_db_type": rules_by_db_type})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/rules", methods=["POST"])
@login_required
def create_rule():
    """创建分类规则"""
    try:
        data = request.get_json()

        result = account_classification_service.create_rule(
            classification_id=data.get("classification_id"),
            db_type=data.get("db_type"),
            rule_name=data.get("rule_name"),
            rule_expression=data.get("rule_expression"),
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"创建规则失败: {str(e)}"})


@account_classification_bp.route("/rules/<int:rule_id>", methods=["GET"])
@login_required
def get_rule(rule_id):
    """获取单个规则详情"""
    try:
        rule = ClassificationRule.query.get(rule_id)
        if not rule:
            return jsonify({"success": False, "error": "规则不存在"}), 404

        rule_dict = rule.to_dict()
        if rule.classification:
            rule_dict["classification_name"] = rule.classification.name

        # 解析规则表达式
        rule_dict["rule_expression"] = rule.get_rule_expression()

        return jsonify({"success": True, "rule": rule_dict})

    except Exception as e:
        return jsonify({"success": False, "error": f"获取规则失败: {str(e)}"})


@account_classification_bp.route("/rules/<int:rule_id>", methods=["PUT"])
@login_required
def update_rule(rule_id):
    """更新分类规则"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = [
            "classification_id",
            "db_type",
            "rule_name",
            "rule_expression",
        ]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"success": False, "error": f"缺少必填字段: {field}"}),
                    400,
                )

        result = account_classification_service.update_rule(
            rule_id=rule_id,
            classification_id=data.get("classification_id"),
            db_type=data.get("db_type"),
            rule_name=data.get("rule_name"),
            rule_expression=data.get("rule_expression"),
            is_active=data.get("is_active", True),
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"更新规则失败: {str(e)}"})


@account_classification_bp.route("/rules/<int:rule_id>", methods=["DELETE"])
@login_required
def delete_rule(rule_id):
    """删除分类规则"""
    try:
        result = account_classification_service.delete_rule(rule_id)
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"删除规则失败: {str(e)}"})


@account_classification_bp.route("/assign", methods=["POST"])
@login_required
def assign_classification():
    """分配账户分类"""
    try:
        data = request.get_json()

        result = account_classification_service.classify_account(
            account_id=data.get("account_id"),
            classification_id=data.get("classification_id"),
            assignment_type="manual",
            assigned_by=current_user.id,
            notes=data.get("notes"),
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"分配分类失败: {str(e)}"})


@account_classification_bp.route("/auto-classify", methods=["POST"])
@login_required
def auto_classify():
    """自动分类账户"""
    try:
        data = request.get_json()
        instance_id = data.get("instance_id")

        result = account_classification_service.auto_classify_accounts(instance_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"自动分类失败: {str(e)}"})


@account_classification_bp.route("/assignments")
@login_required
def get_assignments():
    """获取账户分类分配"""
    try:
        account_id = request.args.get("account_id", type=int)

        assignments = account_classification_service.get_account_classifications(
            account_id
        )

        return jsonify({"success": True, "assignments": assignments})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@account_classification_bp.route("/assignments/<int:assignment_id>", methods=["DELETE"])
@login_required
def remove_assignment(assignment_id):
    """移除账户分类分配"""
    try:
        result = account_classification_service.remove_account_classification(
            assignment_id
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"移除分配失败: {str(e)}"})


@account_classification_bp.route("/permissions/<db_type>")
@login_required
def get_permissions(db_type):
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

    return {
        "mysql": {
            "global_privileges": [
                {"name": "SUPER", "description": "超级权限，可以执行任何操作"},
                {
                    "name": "GRANT OPTION",
                    "description": "授权权限，可以授予其他用户权限",
                },
                {"name": "ALL PRIVILEGES", "description": "所有权限的简写"},
                {"name": "CREATE USER", "description": "创建用户权限"},
                {"name": "RELOAD", "description": "重载权限表"},
                {"name": "SHUTDOWN", "description": "关闭MySQL服务器"},
                {"name": "PROCESS", "description": "查看所有进程"},
                {"name": "FILE", "description": "文件操作权限"},
                {"name": "REPLICATION SLAVE", "description": "复制从库权限"},
                {"name": "REPLICATION CLIENT", "description": "复制客户端权限"},
                {"name": "SHOW DATABASES", "description": "显示所有数据库"},
                {"name": "USAGE", "description": "无权限，仅用于连接"},
            ],
            "database_privileges": [
                {"name": "CREATE", "description": "创建数据库和表"},
                {"name": "DROP", "description": "删除数据库和表"},
                {"name": "ALTER", "description": "修改表结构"},
                {"name": "INDEX", "description": "创建和删除索引"},
                {"name": "LOCK TABLES", "description": "锁定表"},
                {"name": "REFERENCES", "description": "外键权限"},
                {"name": "CREATE TEMPORARY TABLES", "description": "创建临时表"},
                {"name": "CREATE VIEW", "description": "创建视图"},
                {"name": "SHOW VIEW", "description": "显示视图"},
                {"name": "CREATE ROUTINE", "description": "创建存储过程和函数"},
                {"name": "ALTER ROUTINE", "description": "修改存储过程和函数"},
                {"name": "EXECUTE", "description": "执行存储过程和函数"},
                {"name": "TRIGGER", "description": "触发器权限"},
                {"name": "EVENT", "description": "事件权限"},
            ],
            "table_privileges": [
                {"name": "SELECT", "description": "查询数据"},
                {"name": "INSERT", "description": "插入数据"},
                {"name": "UPDATE", "description": "更新数据"},
                {"name": "DELETE", "description": "删除数据"},
            ],
        },
        "postgresql": {
            "role_attributes": [
                {"name": "SUPERUSER", "description": "超级用户"},
                {"name": "CREATEROLE", "description": "创建角色"},
                {"name": "CREATEDB", "description": "创建数据库"},
                {"name": "LOGIN", "description": "登录权限"},
                {"name": "REPLICATION", "description": "复制权限"},
                {"name": "BYPASSRLS", "description": "绕过行级安全"},
                {"name": "INHERIT", "description": "继承权限"},
                {"name": "CONNECTION LIMIT", "description": "连接限制"},
            ],
            "database_privileges": ["CONNECT", "CREATE", "TEMPORARY", "TEMP"],
            "schema_privileges": ["CREATE", "USAGE"],
            "table_privileges": [
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
                "TRUNCATE",
                "REFERENCES",
                "TRIGGER",
            ],
        },
        "sqlserver": {
            "global_privileges": [
                {"name": "CONTROL SERVER", "description": "控制服务器"},
                {"name": "ALTER ANY LOGIN", "description": "修改任意登录"},
                {"name": "ALTER ANY SERVER ROLE", "description": "修改任意服务器角色"},
                {"name": "CREATE ANY DATABASE", "description": "创建任意数据库"},
                {"name": "ALTER ANY DATABASE", "description": "修改任意数据库"},
                {"name": "VIEW SERVER STATE", "description": "查看服务器状态"},
                {"name": "ALTER SERVER STATE", "description": "修改服务器状态"},
                {"name": "ALTER SETTINGS", "description": "修改设置"},
                {"name": "ALTER TRACE", "description": "修改跟踪"},
                {"name": "AUTHENTICATE SERVER", "description": "服务器身份验证"},
                {"name": "BACKUP DATABASE", "description": "备份数据库"},
                {"name": "BACKUP LOG", "description": "备份日志"},
                {"name": "CHECKPOINT", "description": "检查点"},
                {"name": "CONNECT SQL", "description": "连接SQL"},
                {"name": "SHUTDOWN", "description": "关闭服务器"},
                {"name": "IMPERSONATE ANY LOGIN", "description": "模拟任意登录"},
                {"name": "VIEW ANY DEFINITION", "description": "查看任意定义"},
                {
                    "name": "VIEW ANY COLUMN ENCRYPTION KEY DEFINITION",
                    "description": "查看任意列加密密钥定义",
                },
                {
                    "name": "VIEW ANY COLUMN MASTER KEY DEFINITION",
                    "description": "查看任意列主密钥定义",
                },
            ],
            "server_roles": [
                {"name": "sysadmin", "description": "系统管理员"},
                {"name": "serveradmin", "description": "服务器管理员"},
                {"name": "securityadmin", "description": "安全管理员"},
                {"name": "processadmin", "description": "进程管理员"},
                {"name": "setupadmin", "description": "设置管理员"},
                {"name": "bulkadmin", "description": "批量操作管理员"},
                {"name": "diskadmin", "description": "磁盘管理员"},
                {"name": "dbcreator", "description": "数据库创建者"},
                {"name": "public", "description": "公共角色"},
            ],
            "database_roles": [
                {"name": "db_owner", "description": "数据库所有者"},
                {"name": "db_accessadmin", "description": "访问管理员"},
                {"name": "db_securityadmin", "description": "安全管理员"},
                {"name": "db_ddladmin", "description": "DDL管理员"},
                {"name": "db_backupoperator", "description": "备份操作员"},
                {"name": "db_datareader", "description": "数据读取者"},
                {"name": "db_datawriter", "description": "数据写入者"},
                {"name": "db_denydatareader", "description": "拒绝数据读取"},
                {"name": "db_denydatawriter", "description": "拒绝数据写入"},
            ],
            "database_privileges": [
                {"name": "SELECT", "description": "查询数据"},
                {"name": "INSERT", "description": "插入数据"},
                {"name": "UPDATE", "description": "更新数据"},
                {"name": "DELETE", "description": "删除数据"},
                {"name": "CREATE", "description": "创建对象"},
                {"name": "ALTER", "description": "修改/删除对象（包含DROP功能）"},
                {"name": "EXECUTE", "description": "执行存储过程"},
                {"name": "CONTROL", "description": "完全控制权限"},
                {"name": "REFERENCES", "description": "引用权限"},
                {"name": "VIEW DEFINITION", "description": "查看定义"},
                {"name": "TAKE OWNERSHIP", "description": "获取所有权"},
                {"name": "IMPERSONATE", "description": "模拟权限"},
                {"name": "CREATE SCHEMA", "description": "创建架构"},
                {"name": "ALTER ANY SCHEMA", "description": "修改任意架构"},
                {"name": "CREATE TABLE", "description": "创建表"},
                {"name": "CREATE VIEW", "description": "创建视图"},
                {"name": "CREATE PROCEDURE", "description": "创建存储过程"},
                {"name": "CREATE FUNCTION", "description": "创建函数"},
                {"name": "CREATE TRIGGER", "description": "创建触发器"},
                {"name": "BACKUP DATABASE", "description": "备份数据库"},
                {"name": "BACKUP LOG", "description": "备份日志"},
                {"name": "CONNECT", "description": "连接数据库"},
                {"name": "CONNECT REPLICATION", "description": "复制连接"},
            ],
        },
        "oracle": {
            "system_privileges": [
                {"name": "DBA", "description": "数据库管理员角色"},
                {"name": "SYSDBA", "description": "系统数据库管理员"},
                {"name": "SYSOPER", "description": "系统操作员"},
                {"name": "CREATE SESSION", "description": "创建会话"},
                {"name": "CREATE USER", "description": "创建用户"},
                {"name": "CREATE ROLE", "description": "创建角色"},
                {"name": "CREATE TABLE", "description": "创建表"},
                {"name": "CREATE VIEW", "description": "创建视图"},
                {"name": "CREATE PROCEDURE", "description": "创建存储过程"},
                {"name": "CREATE TRIGGER", "description": "创建触发器"},
                {"name": "CREATE SEQUENCE", "description": "创建序列"},
                {"name": "CREATE SYNONYM", "description": "创建同义词"},
                {"name": "CREATE DATABASE LINK", "description": "创建数据库链接"},
                {"name": "CREATE MATERIALIZED VIEW", "description": "创建物化视图"},
                {"name": "CREATE JOB", "description": "创建作业"},
                {"name": "CREATE ANY TABLE", "description": "创建任意表"},
                {"name": "CREATE ANY VIEW", "description": "创建任意视图"},
                {"name": "CREATE ANY PROCEDURE", "description": "创建任意存储过程"},
                {"name": "CREATE ANY TRIGGER", "description": "创建任意触发器"},
                {"name": "CREATE ANY SEQUENCE", "description": "创建任意序列"},
                {"name": "CREATE ANY SYNONYM", "description": "创建任意同义词"},
                {
                    "name": "CREATE ANY DATABASE LINK",
                    "description": "创建任意数据库链接",
                },
                {
                    "name": "CREATE ANY MATERIALIZED VIEW",
                    "description": "创建任意物化视图",
                },
                {"name": "CREATE ANY JOB", "description": "创建任意作业"},
                {"name": "ALTER USER", "description": "修改用户"},
                {"name": "ALTER ROLE", "description": "修改角色"},
                {"name": "ALTER SYSTEM", "description": "修改系统"},
                {"name": "ALTER DATABASE", "description": "修改数据库"},
                {"name": "ALTER ANY TABLE", "description": "修改任意表"},
                {"name": "ALTER ANY VIEW", "description": "修改任意视图"},
                {"name": "ALTER ANY PROCEDURE", "description": "修改任意存储过程"},
                {"name": "ALTER ANY TRIGGER", "description": "修改任意触发器"},
                {"name": "ALTER ANY SEQUENCE", "description": "修改任意序列"},
                {
                    "name": "ALTER ANY MATERIALIZED VIEW",
                    "description": "修改任意物化视图",
                },
                {"name": "DROP USER", "description": "删除用户"},
                {"name": "DROP ROLE", "description": "删除角色"},
                {"name": "DROP ANY TABLE", "description": "删除任意表"},
                {"name": "DROP ANY VIEW", "description": "删除任意视图"},
                {"name": "DROP ANY PROCEDURE", "description": "删除任意存储过程"},
                {"name": "DROP ANY TRIGGER", "description": "删除任意触发器"},
                {"name": "DROP ANY SEQUENCE", "description": "删除任意序列"},
                {"name": "DROP ANY SYNONYM", "description": "删除任意同义词"},
                {"name": "DROP ANY DATABASE LINK", "description": "删除任意数据库链接"},
                {
                    "name": "DROP ANY MATERIALIZED VIEW",
                    "description": "删除任意物化视图",
                },
                {"name": "DROP ANY JOB", "description": "删除任意作业"},
                {"name": "SELECT ANY TABLE", "description": "查询任意表"},
                {"name": "INSERT ANY TABLE", "description": "插入任意表"},
                {"name": "UPDATE ANY TABLE", "description": "更新任意表"},
                {"name": "DELETE ANY TABLE", "description": "删除任意表"},
                {"name": "EXECUTE ANY PROCEDURE", "description": "执行任意存储过程"},
                {"name": "EXECUTE ANY TYPE", "description": "执行任意类型"},
                {"name": "GRANT ANY PRIVILEGE", "description": "授予任意权限"},
                {"name": "GRANT ANY ROLE", "description": "授予任意角色"},
                {"name": "AUDIT ANY", "description": "审计任意对象"},
                {"name": "AUDIT SYSTEM", "description": "审计系统"},
                {"name": "BECOME USER", "description": "成为用户"},
                {"name": "CHANGE NOTIFICATION", "description": "变更通知"},
                {"name": "DEBUG CONNECT SESSION", "description": "调试连接会话"},
                {"name": "DEBUG ANY PROCEDURE", "description": "调试任意存储过程"},
                {"name": "EXEMPT ACCESS POLICY", "description": "豁免访问策略"},
                {"name": "EXEMPT REDACTION POLICY", "description": "豁免编辑策略"},
                {"name": "FLASHBACK ANY TABLE", "description": "闪回任意表"},
                {"name": "FLASHBACK ARCHIVE ADMINISTER", "description": "闪回归档管理"},
                {"name": "GLOBAL QUERY REWRITE", "description": "全局查询重写"},
                {"name": "INHERIT ANY PRIVILEGES", "description": "继承任意权限"},
                {"name": "KEEP DATE TIME", "description": "保持日期时间"},
                {"name": "LOGMINING", "description": "日志挖掘"},
                {"name": "MERGE ANY VIEW", "description": "合并任意视图"},
                {"name": "ON COMMIT REFRESH", "description": "提交时刷新"},
                {"name": "QUERY REWRITE", "description": "查询重写"},
                {"name": "READ ANY FILE GROUP", "description": "读取任意文件组"},
                {"name": "RESUMABLE", "description": "可恢复"},
                {"name": "SELECT ANY DICTIONARY", "description": "查询任意字典"},
                {"name": "SELECT ANY SEQUENCE", "description": "查询任意序列"},
                {"name": "SELECT ANY TRANSACTION", "description": "查询任意事务"},
                {"name": "SYSBACKUP", "description": "系统备份"},
                {"name": "SYSDG", "description": "系统数据卫士"},
                {"name": "SYSKM", "description": "系统密钥管理"},
                {"name": "SYSRAC", "description": "系统实时应用集群"},
                {"name": "TRANSLATE ANY SQL", "description": "翻译任意SQL"},
                {"name": "UNDER ANY TABLE", "description": "任意表下"},
                {"name": "UNDER ANY TYPE", "description": "任意类型下"},
                {"name": "UNDER ANY VIEW", "description": "任意视图下"},
                {"name": "UNLIMITED TABLESPACE", "description": "无限制表空间"},
                {"name": "USE ANY JOB RESOURCE", "description": "使用任意作业资源"},
                {"name": "WRITE ANY FILE GROUP", "description": "写入任意文件组"},
            ]
        },
    }

    return permissions.get(db_type, {})
