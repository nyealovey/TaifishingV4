# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 数据备份管理工具
"""

import os
import shutil
import gzip
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = 'backups', max_backups: int = 30):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_database_backup(self, db_path: str, backup_name: str = None) -> Optional[str]:
        """
        创建数据库备份
        
        Args:
            db_path: 数据库文件路径
            backup_name: 备份文件名
            
        Returns:
            str: 备份文件路径
        """
        try:
            if not os.path.exists(db_path):
                logger.error(f"数据库文件不存在: {db_path}")
                return None
            
            # 生成备份文件名
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"taifish_db_{timestamp}.sqlite"
            
            backup_path = self.backup_dir / backup_name
            
            # 复制数据库文件
            shutil.copy2(db_path, backup_path)
            
            # 压缩备份文件
            compressed_path = f"{backup_path}.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除未压缩的文件
            os.remove(backup_path)
            
            logger.info(f"数据库备份创建成功: {compressed_path}")
            return str(compressed_path)
            
        except Exception as e:
            logger.error(f"创建数据库备份失败: {e}")
            return None
    
    def create_data_backup(self, data: Dict[str, Any], backup_name: str = None) -> Optional[str]:
        """
        创建数据备份
        
        Args:
            data: 要备份的数据
            backup_name: 备份文件名
            
        Returns:
            str: 备份文件路径
        """
        try:
            # 生成备份文件名
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"taifish_data_{timestamp}.json"
            
            backup_path = self.backup_dir / backup_name
            
            # 添加备份元数据
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'data': data
            }
            
            # 保存备份数据
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # 压缩备份文件
            compressed_path = f"{backup_path}.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除未压缩的文件
            os.remove(backup_path)
            
            logger.info(f"数据备份创建成功: {compressed_path}")
            return str(compressed_path)
            
        except Exception as e:
            logger.error(f"创建数据备份失败: {e}")
            return None
    
    def restore_database_backup(self, backup_path: str, db_path: str) -> bool:
        """
        恢复数据库备份
        
        Args:
            backup_path: 备份文件路径
            db_path: 目标数据库路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            # 解压备份文件
            if backup_path.endswith('.gz'):
                temp_path = backup_path[:-3]  # 移除.gz扩展名
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = temp_path
            
            # 恢复数据库文件
            shutil.copy2(backup_path, db_path)
            
            # 清理临时文件
            if temp_path != backup_path:
                os.remove(temp_path)
            
            logger.info(f"数据库恢复成功: {backup_path} -> {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"恢复数据库备份失败: {e}")
            return False
    
    def restore_data_backup(self, backup_path: str) -> Optional[Dict[str, Any]]:
        """
        恢复数据备份
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            dict: 恢复的数据
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"备份文件不存在: {backup_path}")
                return None
            
            # 解压备份文件
            if backup_path.endswith('.gz'):
                temp_path = backup_path[:-3]
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = temp_path
            
            # 读取备份数据
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 清理临时文件
            if temp_path != backup_path:
                os.remove(temp_path)
            
            logger.info(f"数据恢复成功: {backup_path}")
            return backup_data
            
        except Exception as e:
            logger.error(f"恢复数据备份失败: {e}")
            return None
    
    def list_backups(self, backup_type: str = None) -> List[Dict[str, Any]]:
        """
        列出备份文件
        
        Args:
            backup_type: 备份类型过滤
            
        Returns:
            list: 备份文件列表
        """
        backups = []
        
        try:
            for file_path in self.backup_dir.iterdir():
                if file_path.is_file():
                    file_info = {
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'created': datetime.fromtimestamp(file_path.stat().st_ctime),
                        'type': self._get_backup_type(file_path.name)
                    }
                    
                    if not backup_type or file_info['type'] == backup_type:
                        backups.append(file_info)
            
            # 按创建时间排序
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            logger.error(f"列出备份文件失败: {e}")
        
        return backups
    
    def _get_backup_type(self, filename: str) -> str:
        """获取备份类型"""
        if 'db_' in filename or filename.endswith('.sqlite.gz'):
            return 'database'
        elif 'data_' in filename or filename.endswith('.json.gz'):
            return 'data'
        else:
            return 'unknown'
    
    def cleanup_old_backups(self) -> int:
        """
        清理旧备份文件
        
        Returns:
            int: 清理的文件数量
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= self.max_backups:
                return 0
            
            # 删除超出限制的旧备份
            to_delete = backups[self.max_backups:]
            deleted_count = 0
            
            for backup in to_delete:
                try:
                    os.remove(backup['path'])
                    deleted_count += 1
                    logger.info(f"删除旧备份: {backup['name']}")
                except Exception as e:
                    logger.warning(f"删除备份失败: {backup['name']}, 错误: {e}")
            
            logger.info(f"清理完成，删除了 {deleted_count} 个旧备份")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
            return 0
    
    def get_backup_info(self, backup_path: str) -> Optional[Dict[str, Any]]:
        """
        获取备份信息
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            dict: 备份信息
        """
        try:
            if not os.path.exists(backup_path):
                return None
            
            file_stat = os.stat(backup_path)
            
            info = {
                'name': os.path.basename(backup_path),
                'path': backup_path,
                'size': file_stat.st_size,
                'created': datetime.fromtimestamp(file_stat.st_ctime),
                'modified': datetime.fromtimestamp(file_stat.st_mtime),
                'type': self._get_backup_type(os.path.basename(backup_path))
            }
            
            # 如果是数据备份，尝试读取元数据
            if info['type'] == 'data' and backup_path.endswith('.json.gz'):
                try:
                    with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'timestamp' in data:
                            info['backup_timestamp'] = data['timestamp']
                        if 'version' in data:
                            info['backup_version'] = data['version']
                except:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"获取备份信息失败: {e}")
            return None
    
    def schedule_backup(self, backup_type: str, schedule: str = 'daily') -> bool:
        """
        安排定期备份
        
        Args:
            backup_type: 备份类型
            schedule: 备份计划
            
        Returns:
            bool: 是否成功
        """
        # 这里可以集成定时任务系统
        logger.info(f"安排{schedule}{backup_type}备份")
        return True

# 全局备份管理器
backup_manager = BackupManager()

def create_automatic_backup():
    """创建自动备份"""
    try:
        from app import db
        from app.models.user import User
        from app.models.instance import Instance
        from app.models.credential import Credential
        from app.models.task import Task
        
        # 收集所有数据
        data = {
            'users': [user.to_dict() for user in User.query.all()],
            'instances': [instance.to_dict() for instance in Instance.query.all()],
            'credentials': [credential.to_dict() for credential in Credential.query.all()],
            'tasks': [task.to_dict() for task in Task.query.all()]
        }
        
        # 创建数据备份
        backup_path = backup_manager.create_data_backup(data)
        
        if backup_path:
            logger.info(f"自动备份创建成功: {backup_path}")
            return True
        else:
            logger.error("自动备份创建失败")
            return False
            
    except Exception as e:
        logger.error(f"自动备份失败: {e}")
        return False
