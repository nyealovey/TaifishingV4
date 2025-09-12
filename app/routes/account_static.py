"""
泰摸鱼吧 - 账户统计路由
"""

import logging
from collections import defaultdict
from datetime import timedelta

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.models.account import Account
from app.models.account_classification import AccountClassification, AccountClassificationAssignment
from app.models.instance import Instance
from app.models.sync_data import SyncData
from app.utils.timezone import now

# 创建蓝图
account_static_bp = Blueprint("account_static", __name__)


@account_static_bp.route("/")
@login_required
def index():
    """账户统计首页"""
    # 获取统计信息
    stats = get_account_statistics()

    # 获取最近同步记录
    recent_syncs = SyncData.query.order_by(SyncData.sync_time.desc()).limit(10).all()

    # 获取实例列表
    instances = Instance.query.filter_by(is_active=True).all()

    if request.is_json:
        return jsonify(
            {
                "stats": stats,
                "recent_syncs": [sync.to_dict() for sync in recent_syncs],
                "instances": [instance.to_dict() for instance in instances],
            }
        )

    return render_template(
        "accounts/index.html",
        stats=stats,
        recent_syncs=recent_syncs,
        instances=instances,
    )


@account_static_bp.route("/account-statistics")
@login_required
def account_statistics():
    """账户统计API"""
    try:
        stats = get_account_statistics()
        return jsonify(
            {
                "success": True,
                "stats": stats,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"获取统计信息失败: {str(e)}"}), 500


@account_static_bp.route("/api/statistics")
@login_required
def api_statistics():
    """API: 获取账户统计信息"""
    try:
        stats = get_account_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"success": False, "error": f"获取统计信息失败: {str(e)}"}), 500


def get_account_statistics():
    """获取账户统计信息"""
    try:
        # 基础统计
        total_accounts = Account.query.count()

        # 按数据库类型统计
        db_type_stats = {}
        for db_type in ["mysql", "postgresql", "oracle", "sqlserver"]:
            total_count = Account.query.join(Instance).filter(Instance.db_type == db_type).count()
            locked_count = Account.query.join(Instance).filter(Instance.db_type == db_type, Account.is_locked).count()
            active_count = total_count - locked_count

            db_type_stats[db_type] = {"total": total_count, "active": active_count, "locked": locked_count}

        # 按实例统计
        instance_stats = []
        instances = Instance.query.filter_by(is_active=True).all()
        for instance in instances:
            total_count = Account.query.filter_by(instance_id=instance.id).count()
            locked_count = Account.query.filter_by(instance_id=instance.id, is_locked=True).count()
            active_count = total_count - locked_count

            instance_stats.append(
                {
                    "name": instance.name,
                    "db_type": instance.db_type,
                    "environment": instance.environment or "unknown",
                    "total_accounts": total_count,
                    "active_accounts": active_count,
                    "locked_accounts": locked_count,
                    "host": instance.host,
                }
            )

        # 按环境统计
        environment_stats = defaultdict(lambda: {"total": 0, "active": 0, "locked": 0})
        for instance in instances:
            env = instance.environment or "unknown"
            total_count = Account.query.filter_by(instance_id=instance.id).count()
            locked_count = Account.query.filter_by(instance_id=instance.id, is_locked=True).count()
            active_count = total_count - locked_count

            environment_stats[env]["total"] += total_count
            environment_stats[env]["active"] += active_count
            environment_stats[env]["locked"] += locked_count

        # 按分类统计
        classification_stats = {}
        classifications = AccountClassification.query.all()
        for classification in classifications:
            assignment_count = AccountClassificationAssignment.query.filter_by(
                classification_id=classification.id
            ).count()
            classification_stats[classification.name] = {
                "classification_name": classification.name,
                "account_count": assignment_count,
                "color": classification.color,
            }

        # 按状态统计
        locked_accounts = Account.query.filter_by(is_locked=True).count()
        superuser_accounts = Account.query.filter_by(is_superuser=True).count()
        active_accounts = total_accounts - locked_accounts  # 活跃账户 = 总账户 - 锁定账户
        database_instances = len(instances)  # 数据库实例数

        # 最近7天新增账户趋势
        end_date = now()
        start_date = end_date - timedelta(days=7)

        trend_data = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)

            count = Account.query.filter(Account.created_at >= date, Account.created_at < next_date).count()

            trend_data.append({"date": date.strftime("%Y-%m-%d"), "count": count})

        # 最近账户活动 - 获取最近创建的10个账户
        recent_accounts_query = Account.query.join(Instance).order_by(Account.created_at.desc()).limit(10).all()

        # 转换为字典格式
        recent_accounts = []
        for account in recent_accounts_query:
            recent_accounts.append(
                {
                    "id": account.id,
                    "username": account.username,
                    "instance_name": account.instance.name if account.instance else "Unknown",
                    "db_type": account.instance.db_type if account.instance else "Unknown",
                    "is_locked": account.is_locked,
                    "created_at": account.created_at.isoformat() if account.created_at else None,
                    "last_login": account.last_login.isoformat() if account.last_login else None,
                }
            )

        # 按权限类型统计
        permission_stats = defaultdict(int)
        accounts_with_permissions = Account.query.filter(Account.permissions.isnot(None)).all()

        for account in accounts_with_permissions:
            if account.permissions:
                try:
                    import json

                    permissions = json.loads(account.permissions)
                    if isinstance(permissions, dict):
                        # 统计各种权限类型
                        if permissions.get("is_superuser"):
                            permission_stats["superuser"] += 1
                        if permissions.get("can_grant"):
                            permission_stats["can_grant"] += 1
                        if permissions.get("can_login"):
                            permission_stats["can_login"] += 1
                        if permissions.get("can_create_db"):
                            permission_stats["can_create_db"] += 1
                        if permissions.get("can_create_role"):
                            permission_stats["can_create_role"] += 1
                except (json.JSONDecodeError, TypeError):
                    continue

        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "locked_accounts": locked_accounts,
            "database_instances": database_instances,
            "db_type_stats": db_type_stats,
            "instance_stats": instance_stats,
            "environment_stats": dict(environment_stats),
            "classification_stats": classification_stats,
            "superuser_accounts": superuser_accounts,
            "trend_data": trend_data,
            "recent_accounts": recent_accounts,
            "permission_stats": dict(permission_stats),
            "accounts_with_permissions": len(accounts_with_permissions),
        }

    except Exception as e:
        logging.error(f"获取账户统计信息失败: {e}")
        return {
            "total_accounts": 0,
            "active_accounts": 0,
            "locked_accounts": 0,
            "database_instances": 0,
            "db_type_stats": {},
            "instance_stats": [],
            "environment_stats": {},
            "classification_stats": {},
            "superuser_accounts": 0,
            "trend_data": [],
            "recent_accounts": [],
            "permission_stats": {},
            "accounts_with_permissions": 0,
        }
