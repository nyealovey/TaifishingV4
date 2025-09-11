# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户统计路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.instance import Instance
from app.models.credential import Credential
from app.models.sync_data import SyncData
from app.models.account import Account
from app.models.account_classification import AccountClassification
from app.models.account_classification_assignment import AccountClassificationAssignment
from app import db
from app.services.database_service import DatabaseService
import logging
from datetime import datetime, timedelta
from app.utils.timezone import now
from collections import defaultdict

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
        return jsonify({
            "success": True,
            "stats": stats,
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取统计信息失败: {str(e)}"
        }), 500


@account_static_bp.route("/api/statistics")
@login_required
def api_statistics():
    """API: 获取账户统计信息"""
    try:
        stats = get_account_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取统计信息失败: {str(e)}"
        }), 500


def get_account_statistics():
    """获取账户统计信息"""
    try:
        # 基础统计
        total_accounts = Account.query.count()
        
        # 按数据库类型统计
        db_type_stats = {}
        for db_type in ['mysql', 'postgresql', 'oracle', 'sqlserver']:
            count = Account.query.join(Instance).filter(Instance.db_type == db_type).count()
            db_type_stats[db_type] = count
        
        # 按实例统计
        instance_stats = []
        instances = Instance.query.filter_by(is_active=True).all()
        for instance in instances:
            account_count = Account.query.filter_by(instance_id=instance.id).count()
            instance_stats.append({
                'instance_name': instance.name,
                'db_type': instance.db_type,
                'account_count': account_count,
                'host': instance.host,
            })
        
        # 按环境统计
        environment_stats = defaultdict(int)
        for instance in instances:
            env = instance.environment or 'unknown'
            account_count = Account.query.filter_by(instance_id=instance.id).count()
            environment_stats[env] += account_count
        
        # 按分类统计
        classification_stats = []
        classifications = AccountClassification.query.all()
        for classification in classifications:
            assignment_count = AccountClassificationAssignment.query.filter_by(
                classification_id=classification.id
            ).count()
            classification_stats.append({
                'classification_name': classification.name,
                'account_count': assignment_count,
                'color': classification.color,
            })
        
        # 按状态统计
        locked_accounts = Account.query.filter_by(is_locked=True).count()
        superuser_accounts = Account.query.filter_by(is_superuser=True).count()
        
        # 最近7天新增账户趋势
        end_date = now()
        start_date = end_date - timedelta(days=7)
        
        trend_data = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            count = Account.query.filter(
                Account.created_at >= date,
                Account.created_at < next_date
            ).count()
            
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
        
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
                        if permissions.get('is_superuser'):
                            permission_stats['superuser'] += 1
                        if permissions.get('can_grant'):
                            permission_stats['can_grant'] += 1
                        if permissions.get('can_login'):
                            permission_stats['can_login'] += 1
                        if permissions.get('can_create_db'):
                            permission_stats['can_create_db'] += 1
                        if permissions.get('can_create_role'):
                            permission_stats['can_create_role'] += 1
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return {
            "total_accounts": total_accounts,
            "db_type_stats": db_type_stats,
            "instance_stats": instance_stats,
            "environment_stats": dict(environment_stats),
            "classification_stats": classification_stats,
            "locked_accounts": locked_accounts,
            "superuser_accounts": superuser_accounts,
            "trend_data": trend_data,
            "permission_stats": dict(permission_stats),
            "accounts_with_permissions": len(accounts_with_permissions),
        }
        
    except Exception as e:
        logging.error(f"获取账户统计信息失败: {e}")
        return {
            "total_accounts": 0,
            "db_type_stats": {},
            "instance_stats": [],
            "environment_stats": {},
            "classification_stats": [],
            "locked_accounts": 0,
            "superuser_accounts": 0,
            "trend_data": [],
            "permission_stats": {},
            "accounts_with_permissions": 0,
        }
