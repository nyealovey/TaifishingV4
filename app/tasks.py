"""
泰摸鱼吧定时任务定义
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models.log import Log
from app.models.account import Account
from app.models.user import User
from app.services.account_sync_service import account_sync_service
import logging

logger = logging.getLogger(__name__)


def cleanup_old_logs():
    """清理旧日志任务"""
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            # 删除30天前的日志
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            deleted_count = Log.query.filter(Log.created_at < cutoff_date).delete()
            db.session.commit()
            
            logger.info(f"清理旧日志完成，删除了 {deleted_count} 条记录")
            return f"清理了 {deleted_count} 条旧日志"
        except Exception as e:
            logger.error(f"清理旧日志失败: {e}")
            db.session.rollback()
            return f"清理旧日志失败: {e}"


def backup_database():
    """数据库备份任务"""
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            # 创建备份目录
            backup_dir = "userdata/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"taifish_backup_{timestamp}.db")
            
            # 复制数据库文件
            db_path = "userdata/taifish_dev.db"
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_file)
                
                # 清理旧备份（保留最近10个）
                _cleanup_old_backups(backup_dir)
                
                logger.info(f"数据库备份完成: {backup_file}")
                return f"数据库备份完成: {backup_file}"
            else:
                logger.warning("数据库文件不存在，跳过备份")
                return "数据库文件不存在，跳过备份"
                
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return f"数据库备份失败: {e}"


def _cleanup_old_backups(backup_dir, keep_count=10):
    """清理旧备份文件"""
    try:
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.startswith("taifish_backup_") and file.endswith(".db"):
                file_path = os.path.join(backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # 按修改时间排序，删除最旧的文件
        backup_files.sort(key=lambda x: x[1], reverse=True)
        for file_path, _ in backup_files[keep_count:]:
            os.remove(file_path)
            logger.info(f"删除旧备份文件: {file_path}")
            
    except Exception as e:
        logger.error(f"清理旧备份失败: {e}")


def sync_accounts():
    """账户同步任务"""
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            # 获取所有活跃的数据库实例
            instances = db.session.query(Account.instance_id).distinct().all()
            sync_count = 0
            
            for (instance_id,) in instances:
                try:
                    # 执行账户同步
                    result = account_sync_service.sync_accounts(instance_id)
                    if result.get('success'):
                        sync_count += result.get('synced_count', 0)
                        logger.info(f"实例 {instance_id} 同步完成，同步了 {result.get('synced_count', 0)} 个账户")
                    else:
                        logger.warning(f"实例 {instance_id} 同步失败: {result.get('message', '未知错误')}")
                        
                except Exception as e:
                    logger.error(f"实例 {instance_id} 同步异常: {e}")
            
            logger.info(f"账户同步任务完成，总共同步了 {sync_count} 个账户")
            return f"同步了 {sync_count} 个账户"
            
        except Exception as e:
            logger.error(f"账户同步任务失败: {e}")
            return f"账户同步失败: {e}"


def generate_reports():
    """生成报告任务"""
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            # 生成系统统计报告
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'total_users': User.query.count(),
                'total_accounts': Account.query.count(),
                'active_accounts': Account.query.filter_by(is_active=True).count(),
                'total_logs': Log.query.count(),
                'recent_logs': Log.query.filter(
                    Log.created_at >= datetime.utcnow() - timedelta(days=7)
                ).count()
            }
            
            # 保存报告到文件
            reports_dir = "userdata/reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(reports_dir, f"weekly_report_{timestamp}.json")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"周报生成完成: {report_file}")
            return f"周报生成完成: {report_file}"
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return f"生成报告失败: {e}"


def health_check():
    """健康检查任务"""
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            # 检查数据库连接
            db.session.execute('SELECT 1')
            
            # 检查关键表
            user_count = User.query.count()
            account_count = Account.query.count()
            log_count = Log.query.count()
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'database': 'connected',
                'users': user_count,
                'accounts': account_count,
                'logs': log_count
            }
            
            logger.info(f"健康检查完成: {health_data}")
            return health_data
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'unhealthy',
                'error': str(e)
            }


def cleanup_temp_files():
    """清理临时文件任务"""
    from app import create_app
    app = create_app()
    with app.app_context():
        try:
            temp_dirs = [
                "userdata/temp",
                "userdata/exports",
                "userdata/logs"
            ]
            
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
