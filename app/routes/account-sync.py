# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户同步记录路由
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
from app.services.account_sync_service import account_sync_service
import logging
from datetime import datetime, timedelta
from app.utils.timezone import now
from collections import defaultdict

# 创建蓝图
account_sync_bp = Blueprint("account_sync", __name__)


@account_sync_bp.route("/sync-all", methods=["POST"])
@login_required
def sync_all_accounts():
    """同步所有实例的账户"""
    try:
        # 获取所有活跃实例
        instances = Instance.query.filter_by(is_active=True).all()
        
        if not instances:
            return jsonify({
                "success": False,
                "error": "没有找到活跃的数据库实例"
            }), 400

        success_count = 0
        failed_count = 0
        results = []

        for instance in instances:
            try:
                # 使用统一的账户同步服务
                result = account_sync_service.sync_accounts(instance, sync_type="batch")

                if result["success"]:
                    success_count += 1
                    # 记录同步成功
                    sync_record = SyncData(
                        instance_id=instance.id,
                        sync_type="batch",
                        status="success",
                        message=result.get("message", "同步成功"),
                        synced_count=result.get("synced_count", 0),
                        added_count=result.get("added_count", 0),
                        removed_count=result.get("removed_count", 0),
                        modified_count=result.get("modified_count", 0),
                    )
                    db.session.add(sync_record)
                else:
                    failed_count += 1
                    # 记录同步失败
                    sync_record = SyncData(
                        instance_id=instance.id,
                        sync_type="batch",
                        status="failed",
                        message=result.get("error", "同步失败"),
                        synced_count=0,
                    )
                    db.session.add(sync_record)

                results.append({
                    "instance_name": instance.name,
                    "success": result["success"],
                    "message": result.get("message", result.get("error", "未知错误")),
                    "synced_count": result.get("synced_count", 0),
                })

            except Exception as e:
                failed_count += 1
                # 记录同步失败
                sync_record = SyncData(
                    instance_id=instance.id,
                    sync_type="batch",
                    status="failed",
                    message=f"同步失败: {str(e)}",
                    synced_count=0,
                )
                db.session.add(sync_record)
                
                results.append({
                    "instance_name": instance.name,
                    "success": False,
                    "message": f"同步失败: {str(e)}",
                    "synced_count": 0,
                })

        # 提交所有同步记录
        db.session.commit()

        # 记录操作日志
        from app.utils.logger import log_operation
        log_operation(
            operation_type="BATCH_SYNC_ACCOUNTS_COMPLETE",
            user_id=current_user.id,
            details={
                "total_instances": len(instances),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results,
            },
        )

        return jsonify({
            "success": True,
            "message": f"批量同步完成，成功 {success_count} 个实例，失败 {failed_count} 个实例",
            "total_instances": len(instances),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"批量同步失败: {str(e)}",
        }), 500


@account_sync_bp.route("/sync-details-batch", methods=["GET"])
@login_required
def sync_details_batch():
    """获取批量同步详情"""
    try:
        record_ids = request.args.get("record_ids", "").split(",")
        record_ids = [int(rid) for rid in record_ids if rid.strip()]
        
        if not record_ids:
            return jsonify({
                "success": False,
                "error": "没有提供记录ID"
            }), 400

        # 获取同步记录
        records = SyncData.query.filter(SyncData.id.in_(record_ids)).all()
        
        if not records:
            return jsonify({
                "success": False,
                "error": "没有找到同步记录"
            }), 404

        # 构建详情数据
        details = []
        for record in records:
            instance = Instance.query.get(record.instance_id)
            details.append({
                "id": record.id,
                "instance_name": instance.name if instance else "未知实例",
                "status": record.status,
                "message": record.message,
                "synced_count": record.synced_count,
                "sync_time": record.sync_time.isoformat() if record.sync_time else None,
            })

        return jsonify({
            "success": True,
            "details": details,
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取同步详情失败: {str(e)}"
        }), 500


@account_sync_bp.route("/sync-history")
@login_required
def sync_history():
    """同步历史页面"""
    # 获取查询参数
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sync_type = request.args.get("sync_type", "all")
    status = request.args.get("status", "all")
    instance_id = request.args.get("instance_id", type=int)

    # 构建查询
    query = SyncData.query

    # 同步类型过滤
    if sync_type and sync_type != "all":
        query = query.filter(SyncData.sync_type == sync_type)

    # 状态过滤
    if status and status != "all":
        query = query.filter(SyncData.status == status)

    # 实例过滤
    if instance_id:
        query = query.filter(SyncData.instance_id == instance_id)

    # 排序
    query = query.order_by(SyncData.sync_time.desc())

    # 分页
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 获取实例列表用于过滤
    instances = Instance.query.filter_by(is_active=True).all()

    if request.is_json:
        return jsonify({
            "records": [record.to_dict() for record in pagination.items],
            "pagination": {
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
            "instances": [instance.to_dict() for instance in instances],
        })

    return render_template(
        "accounts/sync_history.html",
        records=pagination.items,
        pagination=pagination,
        sync_type=sync_type,
        status=status,
        instance_id=instance_id,
        instances=instances,
    )


@account_sync_bp.route("/sync-details/<sync_id>")
@login_required
def sync_details(sync_id):
    """同步详情页面"""
    try:
        record = SyncData.query.get_or_404(sync_id)
        instance = Instance.query.get(record.instance_id)
        
        if request.is_json:
            return jsonify({
                "success": True,
                "record": record.to_dict(),
                "instance": instance.to_dict() if instance else None,
            })

        return render_template(
            "accounts/sync_details.html",
            record=record,
            instance=instance,
        )

    except Exception as e:
        if request.is_json:
            return jsonify({
                "success": False,
                "error": f"获取同步详情失败: {str(e)}"
            }), 500
        
        flash(f"获取同步详情失败: {str(e)}", "error")
        return redirect(url_for("account_sync.sync_history"))


@account_sync_bp.route("/sync-report")
@login_required
def sync_report():
    """同步报告页面"""
    # 获取查询参数
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sync_type = request.args.get("sync_type", "all")
    status = request.args.get("status", "all")
    instance_id = request.args.get("instance_id", type=int)

    # 构建查询
    query = SyncData.query

    # 同步类型过滤
    if sync_type and sync_type != "all":
        query = query.filter(SyncData.sync_type == sync_type)

    # 状态过滤
    if status and status != "all":
        query = query.filter(SyncData.status == status)

    # 实例过滤
    if instance_id:
        query = query.filter(SyncData.instance_id == instance_id)

    # 排序
    query = query.order_by(SyncData.sync_time.desc())

    # 分页
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 获取实例列表用于过滤
    instances = Instance.query.filter_by(is_active=True).all()

    if request.is_json:
        return jsonify({
            "records": [record.to_dict() for record in pagination.items],
            "pagination": {
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
            "instances": [instance.to_dict() for instance in instances],
        })

    return render_template(
        "accounts/sync_report.html",
        records=pagination.items,
        pagination=pagination,
        sync_type=sync_type,
        status=status,
        instance_id=instance_id,
        instances=instances,
    )


@account_sync_bp.route("/sync-statistics")
@login_required
def sync_statistics():
    """同步统计页面"""
    try:
        # 获取统计信息
        stats = {
            "total_syncs": SyncData.query.count(),
            "success_syncs": SyncData.query.filter_by(status="success").count(),
            "failed_syncs": SyncData.query.filter_by(status="failed").count(),
            "manual_syncs": SyncData.query.filter_by(sync_type="manual").count(),
            "batch_syncs": SyncData.query.filter_by(sync_type="batch").count(),
            "task_syncs": SyncData.query.filter_by(sync_type="task").count(),
        }

        # 获取最近7天的同步趋势
        end_date = now()
        start_date = end_date - timedelta(days=7)
        
        trend_data = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            count = SyncData.query.filter(
                SyncData.sync_time >= date,
                SyncData.sync_time < next_date
            ).count()
            
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })

        if request.is_json:
            return jsonify({
                "stats": stats,
                "trend_data": trend_data,
            })

        return render_template(
            "accounts/sync_statistics.html",
            stats=stats,
            trend_data=trend_data,
        )

    except Exception as e:
        if request.is_json:
            return jsonify({
                "success": False,
                "error": f"获取同步统计失败: {str(e)}"
            }), 500
        
        flash(f"获取同步统计失败: {str(e)}", "error")
        return redirect(url_for("account_sync.sync_history"))


@account_sync_bp.route("/sync-records")
@login_required
def sync_records():
    """统一的同步记录页面"""
    # 获取查询参数
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    sync_type = request.args.get("sync_type", "all")
    status = request.args.get("status", "all")
    instance_id = request.args.get("instance_id", type=int)

    # 构建查询
    query = SyncData.query

    # 同步类型过滤
    if sync_type and sync_type != "all":
        query = query.filter(SyncData.sync_type == sync_type)

    # 状态过滤
    if status and status != "all":
        query = query.filter(SyncData.status == status)

    # 实例过滤
    if instance_id:
        query = query.filter(SyncData.instance_id == instance_id)

    # 排序
    query = query.order_by(SyncData.sync_time.desc())

    # 分页
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 获取实例列表用于过滤
    instances = Instance.query.filter_by(is_active=True).all()

    # 聚合显示逻辑 - 当同步类型是手动批量或定时任务时，需要聚合显示
    aggregated_records = []
    if sync_type in ["batch", "task"] or sync_type == "all":
        # 按同步时间分组，相同时间的记录聚合显示
        time_groups = defaultdict(list)
        for record in pagination.items:
            if record.sync_time:
                time_key = record.sync_time.strftime("%Y-%m-%d %H:%M:%S")
                time_groups[time_key].append(record)
        
        # 构建聚合记录
        for time_key, records in time_groups.items():
            if len(records) > 1:
                # 多个记录，聚合显示
                success_count = sum(1 for r in records if r.status == "success")
                failed_count = len(records) - success_count
                total_synced = sum(r.synced_count or 0 for r in records)
                
                # 构建聚合消息
                if failed_count == 0:
                    message = f"批量同步完成，成功 {success_count} 个实例，共同步 {total_synced} 个账户"
                else:
                    message = f"批量同步完成，成功 {success_count} 个实例，失败 {failed_count} 个实例，共同步 {total_synced} 个账户"
                
                aggregated_record = type('AggregatedRecord', (), {
                    'id': f"batch_{records[0].id}",
                    'sync_time': records[0].sync_time,
                    'sync_type': records[0].sync_type,
                    'status': 'success' if failed_count == 0 else 'partial',
                    'message': message,
                    'synced_count': total_synced,
                    'instance_name': '批量同步',
                    'is_aggregated': True,
                    'record_ids': [r.id for r in records],
                    'success_count': success_count,
                    'failed_count': failed_count,
                })()
                
                aggregated_records.append(aggregated_record)
            else:
                # 单个记录，直接显示
                record = records[0]
                record.is_aggregated = False
                aggregated_records.append(record)
    else:
        # 其他类型，直接显示
        for record in pagination.items:
            record.is_aggregated = False
            aggregated_records.append(record)

    if request.is_json:
        return jsonify({
            "records": [record.to_dict() if hasattr(record, 'to_dict') else {
                'id': record.id,
                'sync_time': record.sync_time.isoformat() if record.sync_time else None,
                'sync_type': record.sync_type,
                'status': record.status,
                'message': record.message,
                'synced_count': record.synced_count,
                'instance_name': getattr(record, 'instance_name', ''),
                'is_aggregated': getattr(record, 'is_aggregated', False),
                'record_ids': getattr(record, 'record_ids', []),
                'success_count': getattr(record, 'success_count', 0),
                'failed_count': getattr(record, 'failed_count', 0),
            } for record in aggregated_records],
            "pagination": {
                "page": pagination.page,
                "pages": pagination.pages,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
            "instances": [instance.to_dict() for instance in instances],
        })

    return render_template(
        "accounts/sync_records.html",
        records=aggregated_records,
        pagination=pagination,
        sync_type=sync_type,
        status=status,
        instance_id=instance_id,
        instances=instances,
    )


@account_sync_bp.route("/history")
@login_required
def history():
    """历史记录页面 - 重定向到统一页面"""
    return redirect(url_for("account_sync.sync_records"))
