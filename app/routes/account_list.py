# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.instance import Instance
from app.models.credential import Credential
from app.models.sync_data import SyncData
from app.models.account import Account
from app import db
from app.services.database_service import DatabaseService
import logging
from datetime import datetime, timedelta
from app.utils.timezone import now
from app.utils.enhanced_logger import api_logger, log_api_error, log_exception

# 创建蓝图
account_list_bp = Blueprint("account_list", __name__)


@account_list_bp.route("/")
@account_list_bp.route("/<db_type>")
@login_required
def list_accounts(db_type=None):
    """账户列表页面"""
    # 获取查询参数
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()
    instance_id = request.args.get("instance_id", type=int)
    is_locked = request.args.get("is_locked")
    is_superuser = request.args.get("is_superuser")
    plugin = request.args.get("plugin", "").strip()
    environment = request.args.get("environment", "").strip()
    classification = request.args.get("classification", "").strip()

    # 构建查询
    query = Account.query

    # 数据库类型过滤
    if db_type and db_type != "all":
        query = query.join(Instance).filter(Instance.db_type == db_type)

    # 实例过滤
    if instance_id:
        query = query.filter(Account.instance_id == instance_id)

    # 搜索过滤
    if search:
        query = query.filter(Account.username.contains(search))

    # 锁定状态过滤
    if is_locked is not None:
        query = query.filter(Account.is_locked == (is_locked == "true"))

    # 超级用户过滤
    if is_superuser is not None:
        query = query.filter(Account.is_superuser == (is_superuser == "true"))

    # 排序
    query = query.order_by(Account.username.asc())

    # 分页
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 获取实例列表用于过滤
    instances = Instance.query.filter_by(is_active=True).all()

    # 获取统计信息
    stats = {
        "total": Account.query.count(),
        "mysql": Account.query.join(Instance).filter(Instance.db_type == "mysql").count(),
        "postgresql": Account.query.join(Instance).filter(Instance.db_type == "postgresql").count(),
        "oracle": Account.query.join(Instance).filter(Instance.db_type == "oracle").count(),
        "sqlserver": Account.query.join(Instance).filter(Instance.db_type == "sqlserver").count(),
    }

    # 构建过滤选项
    filter_options = {
        "db_types": [
            {"value": "mysql", "label": "MySQL"},
            {"value": "postgresql", "label": "PostgreSQL"},
            {"value": "oracle", "label": "Oracle"},
            {"value": "sqlserver", "label": "SQL Server"},
        ],
        "environments": [
            {"value": "production", "label": "生产环境"},
            {"value": "staging", "label": "测试环境"},
            {"value": "development", "label": "开发环境"},
        ],
        "classifications": [
            {"value": "admin", "label": "管理员"},
            {"value": "user", "label": "普通用户"},
            {"value": "readonly", "label": "只读用户"},
        ],
    }

    # 获取账户分类信息
    from app.models.account_classification import AccountClassification, AccountClassificationAssignment
    
    classifications = {}
    if pagination.items:
        account_ids = [account.id for account in pagination.items]
        assignments = AccountClassificationAssignment.query.filter(
            AccountClassificationAssignment.account_id.in_(account_ids)
        ).all()
        
        for assignment in assignments:
            if assignment.account_id not in classifications:
                classifications[assignment.account_id] = []
            classifications[assignment.account_id].append({
                "name": assignment.classification.name,
                "color": assignment.classification.color,
            })

    if request.is_json:
        return jsonify({
            "accounts": [account.to_dict() for account in pagination.items],
            "pagination": {
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
            "stats": stats,
            "instances": [instance.to_dict() for instance in instances],
        })

    return render_template(
        "accounts/list.html",
        accounts=pagination,
        pagination=pagination,
        db_type=db_type or "all",
        current_db_type=db_type,
        search=search,
        instance_id=instance_id,
        is_locked=is_locked,
        is_superuser=is_superuser,
        plugin=plugin,
        environment=environment,
        classification=classification,
        instances=instances,
        stats=stats,
        filter_options=filter_options,
        classifications=classifications,
    )


@account_list_bp.route("/export")
@login_required
def export_accounts():
    """导出账户数据为CSV"""
    import csv
    import io
    from flask import Response
    from datetime import datetime

    # 获取查询参数（与list_accounts方法保持一致）
    db_type = request.args.get("db_type", type=str)
    search = request.args.get("search", "").strip()
    instance_id = request.args.get("instance_id", type=int)
    is_locked = request.args.get("is_locked")
    is_superuser = request.args.get("is_superuser")
    plugin = request.args.get("plugin", "").strip()
    environment = request.args.get("environment", "").strip()
    classification = request.args.get("classification", "").strip()

    # 构建查询（与list_accounts方法保持一致）
    query = Account.query

    # 数据库类型过滤
    if db_type and db_type != "all":
        query = query.join(Instance).filter(Instance.db_type == db_type)

    # 实例过滤
    if instance_id:
        query = query.filter(Account.instance_id == instance_id)

    # 搜索过滤
    if search:
        query = query.filter(Account.username.contains(search))

    # 锁定状态过滤
    if is_locked is not None:
        query = query.filter(Account.is_locked == (is_locked == "true"))

    # 超级用户过滤
    if is_superuser is not None:
        query = query.filter(Account.is_superuser == (is_superuser == "true"))

    # 排序
    query = query.order_by(Account.username.asc())

    # 获取所有账户数据
    accounts = query.all()

    # 获取账户分类信息
    from app.models.account_classification import AccountClassification, AccountClassificationAssignment
    
    classifications = {}
    if accounts:
        account_ids = [account.id for account in accounts]
        assignments = AccountClassificationAssignment.query.filter(
            AccountClassificationAssignment.account_id.in_(account_ids)
        ).all()
        
        for assignment in assignments:
            if assignment.account_id not in classifications:
                classifications[assignment.account_id] = []
            classifications[assignment.account_id].append(assignment.classification.name)

    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow([
        "ID",
        "用户名",
        "主机",
        "数据库类型",
        "实例名称",
        "插件",
        "是否锁定",
        "是否超级用户",
        "账户分类",
        "创建时间",
        "更新时间"
    ])

    # 写入账户数据
    for account in accounts:
        # 获取实例信息
        instance = Instance.query.get(account.instance_id) if account.instance_id else None
        
        # 获取分类信息
        account_classifications = classifications.get(account.id, [])
        classification_str = ", ".join(account_classifications) if account_classifications else ""
        
        writer.writerow([
            account.id,
            account.username,
            account.host or "",
            instance.db_type if instance else "",
            instance.name if instance else "",
            account.plugin or "",
            "是" if account.is_locked else "否",
            "是" if account.is_superuser else "否",
            classification_str,
            account.created_at.strftime("%Y-%m-%d %H:%M:%S") if account.created_at else "",
            account.updated_at.strftime("%Y-%m-%d %H:%M:%S") if account.updated_at else ""
        ])

    # 创建响应
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"accounts_export_{timestamp}.csv"
    
    response = Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

    return response


@account_list_bp.route("/sync/<int:instance_id>", methods=["POST"])
@login_required
def sync_accounts(instance_id):
    """同步单个实例的账户"""
    try:
        instance = Instance.query.get_or_404(instance_id)
        
        # 使用数据库服务进行同步
        db_service = DatabaseService()
        result = db_service.sync_accounts(instance)
        
        if result["success"]:
            # 记录同步成功
            sync_record = SyncData(
                instance_id=instance_id,
                sync_type="manual",
                status="success",
                message=result.get("message", "同步成功"),
                synced_count=result.get("synced_count", 0),
                added_count=result.get("added_count", 0),
                removed_count=result.get("removed_count", 0),
                modified_count=result.get("modified_count", 0),
            )
            db.session.add(sync_record)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": result.get("message", "同步成功"),
                "synced_count": result.get("synced_count", 0),
            })
        else:
            # 记录同步失败
            sync_record = SyncData(
                instance_id=instance_id,
                sync_type="manual",
                status="failed",
                message=result.get("error", "同步失败"),
                synced_count=0,
            )
            db.session.add(sync_record)
            db.session.commit()
            
            return jsonify({
                "success": False,
                "error": result.get("error", "同步失败"),
            }), 400
            
    except Exception as e:
        # 记录详细的错误日志
        log_api_error("sync_accounts", e, "account_list", 
                     f"实例ID: {instance_id}, 用户: {current_user.id if current_user else 'unknown'}")
        
        # 记录同步失败
        sync_record = SyncData(
            instance_id=instance_id,
            sync_type="manual",
            status="failed",
            message=f"同步失败: {str(e)}",
            synced_count=0,
        )
        db.session.add(sync_record)
        db.session.commit()
        
        return jsonify({
            "success": False,
            "error": f"同步失败: {str(e)}",
        }), 500


@account_list_bp.route("/<int:account_id>/permissions")
@login_required
def get_account_permissions(account_id):
    """获取账户权限详情"""
    try:
        account = Account.query.get_or_404(account_id)
        
        if not account.permissions:
            return jsonify({
                "success": False,
                "error": "该账户没有权限信息"
            }), 404

        import json
        permissions = json.loads(account.permissions)
        
        return jsonify({
            "success": True,
            "permissions": {
                "permissions": permissions  # 嵌套结构，与instances.py保持一致
            },
            "account": {
                "id": account.id,
                "username": account.username,
                "host": account.host,
                "plugin": account.plugin,
                "db_type": account.instance.db_type if account.instance else "",
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取权限失败: {str(e)}"
        }), 500


@account_list_bp.route("/api/sync/<int:instance_id>")
@login_required
def api_sync_accounts(instance_id):
    """API: 同步单个实例的账户"""
    try:
        instance = Instance.query.get_or_404(instance_id)
        
        # 使用数据库服务进行同步
        db_service = DatabaseService()
        result = db_service.sync_accounts(instance)
        
        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"同步失败: {str(e)}"
        }), 500
