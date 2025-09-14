"""
泰摸鱼吧 - 优化版账户同步路由
解决数据库锁定和并发问题
"""

import time

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.instance import Instance
from app.models.sync_data import SyncData
from app.services.account_sync_service import account_sync_service
from app.services.sync_session_service_optimized import optimized_sync_session_service
from app.utils.auth import view_required
from app.utils.structlog_config import get_api_logger, log_error, log_info, log_warning

# 创建蓝图
account_sync_optimized_bp = Blueprint("account_sync_optimized", __name__, url_prefix="/account-sync-optimized")


@account_sync_optimized_bp.route("/")
@login_required
@view_required
def sync_records() -> str | Response:
    """同步记录页面（优化版）"""
    try:
        # 获取同步记录
        sync_records = SyncData.query.order_by(SyncData.sync_time.desc()).limit(50).all()

        # 获取实例信息
        instances = Instance.query.filter_by(is_active=True).all()

        return render_template(
            "account_sync/sync_records_optimized.html",
            sync_records=sync_records,
            instances=instances,
        )
    except Exception as e:
        log_error(f"获取同步记录失败: {str(e)}", module="account_sync_optimized")
        flash("获取同步记录失败", "error")
        return redirect(url_for("dashboard.index"))


@account_sync_optimized_bp.route("/sync-all", methods=["POST"])
@login_required
def sync_all_accounts_optimized() -> str | Response | tuple[Response, int]:
    """同步所有实例的账户（优化版 - 解决锁定问题）"""
    try:
        log_info("开始优化版批量同步", module="account_sync_optimized", user_id=current_user.id)

        # 获取所有活跃实例
        instances = Instance.query.filter_by(is_active=True).all()

        if not instances:
            log_warning("没有找到活跃的数据库实例", module="account_sync_optimized", user_id=current_user.id)
            return jsonify({"success": False, "error": "没有找到活跃的数据库实例"}), 400

        # 创建同步会话
        session = optimized_sync_session_service.create_session(
            sync_type="manual_batch", sync_category="account", created_by=current_user.id
        )

        log_info(
            "创建优化版批量同步会话",
            module="account_sync_optimized",
            session_id=session.session_id,
            user_id=current_user.id,
            instance_count=len(instances),
        )

        # 分批添加实例记录，避免长时间锁定
        instance_ids = [inst.id for inst in instances]
        records = optimized_sync_session_service.add_instance_records_batch(session.session_id, instance_ids)

        success_count = 0
        failed_count = 0
        results = []

        # 逐个处理实例，避免并发冲突
        for i, instance in enumerate(instances):
            try:
                # 找到对应的记录
                record = next((r for r in records if r.instance_id == instance.id), None)
                if not record:
                    log_warning(
                        "未找到实例记录",
                        module="account_sync_optimized",
                        instance_id=instance.id,
                        session_id=session.session_id,
                    )
                    continue

                # 开始实例同步（带锁控制）
                if not optimized_sync_session_service.start_instance_sync_with_lock(record.id):
                    log_warning(
                        "无法开始实例同步（可能被锁定）",
                        module="account_sync_optimized",
                        instance_id=instance.id,
                        session_id=session.session_id,
                    )
                    failed_count += 1
                    results.append(
                        {
                            "instance_name": instance.name,
                            "success": False,
                            "message": "实例被其他会话锁定",
                            "synced_count": 0,
                        }
                    )
                    continue

                log_info(
                    "开始同步实例",
                    module="account_sync_optimized",
                    session_id=session.session_id,
                    instance_name=instance.name,
                    instance_id=instance.id,
                    progress=f"{i + 1}/{len(instances)}",
                )

                # 执行账户同步
                result = account_sync_service.sync_accounts(instance, sync_type="batch", session_id=session.session_id)

                if result.get("success"):
                    success_count += 1

                    # 完成实例同步（带锁控制）
                    optimized_sync_session_service.complete_instance_sync_with_lock(
                        record.id,
                        accounts_synced=result.get("synced_count", 0),
                        accounts_created=result.get("added_count", 0),
                        accounts_updated=result.get("modified_count", 0),
                        accounts_deleted=result.get("removed_count", 0),
                        sync_details=result.get("details", {}),
                    )

                    # 记录同步成功（使用短事务）
                    sync_record = SyncData(
                        instance_id=instance.id,
                        sync_type="batch_optimized",
                        session_id=session.session_id,
                        sync_category="account",
                        status="success",
                        message=result.get("message", "同步成功"),
                        synced_count=result.get("synced_count", 0),
                        added_count=result.get("added_count", 0),
                        removed_count=result.get("removed_count", 0),
                        modified_count=result.get("modified_count", 0),
                    )
                    db.session.add(sync_record)
                    db.session.commit()

                    results.append(
                        {
                            "instance_name": instance.name,
                            "success": True,
                            "message": result.get("message", "同步成功"),
                            "synced_count": result.get("synced_count", 0),
                        }
                    )

                    log_info(
                        "实例同步成功",
                        module="account_sync_optimized",
                        session_id=session.session_id,
                        instance_name=instance.name,
                        synced_count=result.get("synced_count", 0),
                    )
                else:
                    failed_count += 1

                    # 标记实例同步失败（带锁控制）
                    optimized_sync_session_service.fail_instance_sync_with_lock(
                        record.id,
                        error_message=result.get("error", "同步失败"),
                        sync_details={"error": result.get("error", "同步失败")},
                    )

                    # 记录同步失败（使用短事务）
                    sync_record = SyncData(
                        instance_id=instance.id,
                        sync_type="batch_optimized",
                        session_id=session.session_id,
                        sync_category="account",
                        status="failed",
                        message=result.get("error", "同步失败"),
                        synced_count=0,
                    )
                    db.session.add(sync_record)
                    db.session.commit()

                    results.append(
                        {
                            "instance_name": instance.name,
                            "success": False,
                            "message": result.get("error", "同步失败"),
                            "synced_count": 0,
                        }
                    )

                    log_error(
                        "实例同步失败",
                        module="account_sync_optimized",
                        session_id=session.session_id,
                        instance_name=instance.name,
                        error=result.get("error", "同步失败"),
                    )

            except Exception as e:
                failed_count += 1

                # 确保释放锁
                if record:
                    optimized_sync_session_service.fail_instance_sync_with_lock(
                        record.id,
                        error_message=str(e),
                        sync_details={"exception": str(e)},
                    )

                log_error(
                    f"实例同步异常: {instance.name}",
                    module="account_sync_optimized",
                    session_id=session.session_id,
                    instance_id=instance.id,
                    error=str(e),
                )

                # 记录同步失败（使用短事务）
                sync_record = SyncData(
                    instance_id=instance.id,
                    sync_type="batch_optimized",
                    session_id=session.session_id,
                    sync_category="account",
                    status="failed",
                    message=f"同步异常: {str(e)}",
                    synced_count=0,
                )
                db.session.add(sync_record)
                db.session.commit()

                results.append(
                    {
                        "instance_name": instance.name,
                        "success": False,
                        "message": f"同步异常: {str(e)}",
                        "synced_count": 0,
                    }
                )

            # 添加短暂延迟，避免数据库压力过大
            time.sleep(0.1)

        # 记录同步完成日志
        log_info(
            f"优化版批量同步完成: 成功 {success_count} 个实例，失败 {failed_count} 个实例",
            module="account_sync_optimized",
            session_id=session.session_id,
            user_id=current_user.id,
            total_instances=len(instances),
            success_count=success_count,
            failed_count=failed_count,
        )

        # 记录操作日志
        api_logger = get_api_logger()
        api_logger.info(
            "优化版批量同步账户完成",
            module="account_sync_optimized",
            operation_type="BATCH_SYNC_ACCOUNTS_OPTIMIZED_COMPLETE",
            session_id=session.session_id,
            user_id=current_user.id,
            total_instances=len(instances),
            success_count=success_count,
            failed_count=failed_count,
            results=results,
        )

        return jsonify(
            {
                "success": True,
                "message": f"优化版批量同步完成，成功 {success_count} 个实例，失败 {failed_count} 个实例",
                "total_instances": len(instances),
                "success_count": success_count,
                "failed_count": failed_count,
                "results": results,
                "session_id": session.session_id,
            }
        )

    except Exception as e:
        # 记录详细的错误日志
        api_logger = get_api_logger()
        api_logger.error(
            "优化版同步所有账户失败",
            module="account_sync_optimized",
            operation="sync_all_accounts_optimized",
            user_id=current_user.id if current_user else None,
            exception=str(e),
        )

        return (
            jsonify(
                {
                    "success": False,
                    "error": f"优化版批量同步失败: {str(e)}",
                }
            ),
            500,
        )


@account_sync_optimized_bp.route("/sync-details-batch", methods=["GET"])
@login_required
def sync_details_batch_optimized() -> str | Response | tuple[Response, int]:
    """获取优化版批量同步详情"""
    try:
        session_id = request.args.get("session_id")
        if not session_id:
            return jsonify({"success": False, "error": "缺少会话ID"}), 400

        # 获取会话性能统计
        performance = optimized_sync_session_service.get_session_performance(session_id)

        if not performance:
            return jsonify({"success": False, "error": "会话不存在"}), 404

        # 获取实例记录详情
        records = optimized_sync_session_service.get_session_records(session_id)
        record_details = []

        for record in records:
            record_details.append(
                {
                    "id": record.id,
                    "instance_id": record.instance_id,
                    "instance_name": record.instance_name,
                    "status": record.status,
                    "started_at": record.started_at.isoformat() if record.started_at else None,
                    "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                    "accounts_synced": record.accounts_synced,
                    "accounts_created": record.accounts_created,
                    "accounts_updated": record.accounts_updated,
                    "accounts_deleted": record.accounts_deleted,
                    "error_message": record.error_message,
                }
            )

        return jsonify(
            {
                "success": True,
                "performance": performance,
                "records": record_details,
            }
        )

    except Exception as e:
        log_error(
            "获取优化版批量同步详情失败",
            module="account_sync_optimized",
            error=str(e),
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"获取同步详情失败: {str(e)}",
                }
            ),
            500,
        )


@account_sync_optimized_bp.route("/cleanup", methods=["POST"])
@login_required
def cleanup_old_sessions() -> Response:
    """清理旧的同步会话"""
    try:
        days = request.json.get("days", 7) if request.is_json else 7

        cleaned_count = optimized_sync_session_service.cleanup_old_sessions(days)

        log_info(
            "清理旧同步会话",
            module="account_sync_optimized",
            user_id=current_user.id,
            cleaned_count=cleaned_count,
            days=days,
        )

        return jsonify(
            {
                "success": True,
                "message": f"清理完成，删除了 {cleaned_count} 个旧会话",
                "cleaned_count": cleaned_count,
            }
        )

    except Exception as e:
        log_error(
            "清理旧同步会话失败",
            module="account_sync_optimized",
            error=str(e),
        )
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"清理失败: {str(e)}",
                }
            ),
            500,
        )
