"""
泰摸鱼吧定时任务定义
"""

import logging
import os
from datetime import datetime, timedelta

from app import create_app, db
from app.models.account import Account
from app.models.log import Log
from app.models.user import User
from app.services.account_sync_service import account_sync_service

logger = logging.getLogger(__name__)


def cleanup_old_logs():
    """清理旧日志任务 - 清理30天前的日志和临时文件"""
    from app.utils.enhanced_logger import log_operation, sync_logger

    app = create_app()
    with app.app_context():
        try:
            # 删除30天前的日志
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            deleted_logs = Log.query.filter(Log.created_at < cutoff_date).delete()

            # 清理临时文件
            cleaned_files = _cleanup_temp_files()

            # 清理旧的同步记录（保留最近30天）
            from app.models.sync_data import SyncData

            deleted_sync = SyncData.query.filter(SyncData.sync_time < cutoff_date).delete()

            db.session.commit()

            # 记录操作日志
            log_operation(
                operation_type="TASK_CLEANUP_COMPLETE",
                user_id=None,  # 定时任务没有用户ID
                details={
                    "deleted_logs": deleted_logs,
                    "deleted_sync_records": deleted_sync,
                    "cleaned_temp_files": cleaned_files,
                    "cutoff_date": cutoff_date.isoformat(),
                },
            )

            sync_logger.info(
                f"定时任务清理完成，删除了 {deleted_logs} 条日志，{deleted_sync} 条同步记录，{cleaned_files} 个临时文件",
                "scheduler",
                source="定时任务",
            )

            return f"清理完成：{deleted_logs} 条日志，{deleted_sync} 条同步记录，{cleaned_files} 个临时文件"

        except Exception as e:
            sync_logger.error(f"定时任务清理失败: {e}", "scheduler", source="定时任务")
            db.session.rollback()
            return f"清理失败: {e}"


def _cleanup_temp_files():
    """清理临时文件"""
    try:
        temp_dirs = ["userdata/temp", "userdata/exports", "userdata/logs", "userdata/dynamic_tasks"]

        cleaned_files = 0
        cutoff_time = datetime.now() - timedelta(days=7)  # 清理7天前的临时文件

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        # 删除7天前的临时文件
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_mtime < cutoff_time:
                            os.remove(file_path)
                            cleaned_files += 1
                            logger.info(f"删除临时文件: {file_path}")

        return cleaned_files

    except Exception as e:
        logger.error(f"清理临时文件失败: {e}")
        return 0


def sync_accounts():
    """账户同步任务 - 同步所有数据库实例的账户"""
    from app import db
    from app.models.instance import Instance
    from app.models.sync_data import SyncData
    from app.utils.enhanced_logger import log_operation, sync_logger

    app = create_app()
    with app.app_context():
        try:
            # 获取所有活跃的数据库实例
            instances = Instance.query.filter_by(is_active=True).all()
            total_instances = len(instances)

            if not instances:
                sync_logger.warning("没有找到活跃的数据库实例", "scheduler", source="定时任务")
                return "没有找到活跃的数据库实例"

            sync_logger.info(f"定时任务开始同步所有账户，共 {total_instances} 个实例", "scheduler", source="定时任务")

            success_count = 0
            failed_count = 0
            total_synced_count = 0
            total_added_count = 0
            total_removed_count = 0
            total_modified_count = 0
            results = []

            for instance in instances:
                try:
                    sync_logger.info(
                        f"开始同步实例: {instance.name} ({instance.db_type})",
                        "scheduler",
                        f"实例ID: {instance.id}",
                        source="定时任务",
                    )

                    # 执行账户同步，使用task类型
                    result = account_sync_service.sync_accounts(instance, sync_type="task")

                    if result.get("success"):
                        success_count += 1
                        instance_sync_count = result.get("synced_count", 0)
                        total_synced_count += instance_sync_count
                        total_added_count += result.get("added_count", 0)
                        total_removed_count += result.get("removed_count", 0)
                        total_modified_count += result.get("modified_count", 0)

                        sync_logger.info(
                            f"实例 {instance.name} 同步完成，同步了 {instance_sync_count} 个账户",
                            "scheduler",
                            f"实例ID: {instance.id}",
                            source="定时任务",
                        )

                        results.append(
                            {
                                "instance_name": instance.name,
                                "success": True,
                                "message": result.get("message", "同步成功"),
                                "synced_count": instance_sync_count,
                            }
                        )
                    else:
                        failed_count += 1
                        error_msg = result.get("message", result.get("error", "未知错误"))
                        sync_logger.warning(
                            f"实例 {instance.name} 同步失败: {error_msg}",
                            "scheduler",
                            f"实例ID: {instance.id}",
                            source="定时任务",
                        )

                        results.append(
                            {
                                "instance_name": instance.name,
                                "success": False,
                                "message": error_msg,
                                "synced_count": 0,
                            }
                        )

                except Exception as e:
                    failed_count += 1
                    sync_logger.error(
                        f"实例 {instance.name} 同步异常: {e}", "scheduler", f"实例ID: {instance.id}", source="定时任务"
                    )

                    results.append(
                        {
                            "instance_name": instance.name,
                            "success": False,
                            "message": f"同步异常: {str(e)}",
                            "synced_count": 0,
                        }
                    )

            # 记录操作日志
            log_operation(
                operation_type="TASK_SYNC_ACCOUNTS_COMPLETE",
                user_id=None,  # 定时任务没有用户ID
                details={
                    "total_instances": total_instances,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "total_synced_count": total_synced_count,
                    "total_added_count": total_added_count,
                    "total_removed_count": total_removed_count,
                    "total_modified_count": total_modified_count,
                    "results": results,
                },
            )

            # 创建聚合的同步记录
            sync_record = SyncData(
                instance_id=None,  # 聚合记录没有单一实例ID
                sync_type="task",
                status="success" if failed_count == 0 else "failed",
                message=f"定时任务同步完成，成功 {success_count} 个实例，失败 {failed_count} 个实例，总共同步 {total_synced_count} 个账户",
                synced_count=total_synced_count,
                added_count=total_added_count,
                removed_count=total_removed_count,
                modified_count=total_modified_count,
                records_count=total_synced_count,
                data={
                    "total_instances": total_instances,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "results": results,
                },
            )
            db.session.add(sync_record)
            db.session.commit()

            sync_logger.info(
                f"定时任务账户同步完成，总共同步了 {total_synced_count} 个账户，涉及 {total_instances} 个实例",
                "scheduler",
                source="定时任务",
            )

            return f"定时任务同步完成，成功 {success_count} 个实例，失败 {failed_count} 个实例，总共同步 {total_synced_count} 个账户"

        except Exception as e:
            sync_logger.error(f"定时任务账户同步失败: {e}", "scheduler", source="定时任务")

            # 记录失败的同步记录
            sync_record = SyncData(
                instance_id=None,
                sync_type="task",
                status="failed",
                message=f"定时任务同步失败: {str(e)}",
                synced_count=0,
                records_count=0,
                data={"error": str(e)},
            )
            db.session.add(sync_record)
            db.session.commit()

            return f"定时任务同步失败: {e}"


def health_check():
    """健康检查任务"""
    app = create_app()
    with app.app_context():
        try:
            # 检查数据库连接
            db.session.execute("SELECT 1")

            # 检查关键表
            user_count = User.query.count()
            account_count = Account.query.count()
            log_count = Log.query.count()

            health_data = {
                "timestamp": datetime.now().isoformat(),
                "status": "healthy",
                "database": "connected",
                "users": user_count,
                "accounts": account_count,
                "logs": log_count,
            }

            logger.info(f"健康检查完成: {health_data}")
            return health_data

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {"timestamp": datetime.now().isoformat(), "status": "unhealthy", "error": str(e)}


def cleanup_temp_files():
    """清理临时文件任务"""
    app = create_app()
    with app.app_context():
        try:
            temp_dirs = ["userdata/temp", "userdata/exports", "userdata/logs"]

            cleaned_files = 0
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            # 删除7天前的临时文件
                            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_age.days > 7:
                                os.remove(file_path)
                                cleaned_files += 1

            logger.info(f"临时文件清理完成，删除了 {cleaned_files} 个文件")
            return f"清理了 {cleaned_files} 个临时文件"

        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
            return f"清理临时文件失败: {e}"
