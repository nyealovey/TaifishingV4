# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 配置管理服务
提供动态修改配置的Web界面功能
"""

import os
import re
import ast
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from dotenv import load_dotenv, set_key, get_key
from flask import current_app

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.constants_file = self.project_root / "app" / "constants.py"
        self.env_file = self.project_root / ".env"
        self.env_example_file = self.project_root / "env.example"
        self.backup_dir = self.project_root / "userdata" / "backups" / "config"
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置项元数据
        self.config_metadata = self._load_config_metadata()
    
    def _load_config_metadata(self) -> Dict[str, Dict[str, Any]]:
        """加载配置项元数据"""
        return {
            # 系统常量配置
            "DEFAULT_PAGE_SIZE": {
                "type": "int",
                "min": 1,
                "max": 1000,
                "description": "默认分页大小",
                "category": "分页配置",
                "editable": True,
                "requires_restart": False
            },
            "MAX_PAGE_SIZE": {
                "type": "int",
                "min": 10,
                "max": 10000,
                "description": "最大分页大小",
                "category": "分页配置",
                "editable": True,
                "requires_restart": False
            },
            "MIN_PASSWORD_LENGTH": {
                "type": "int",
                "min": 6,
                "max": 128,
                "description": "最小密码长度",
                "category": "安全配置",
                "editable": True,
                "requires_restart": False
            },
            "PASSWORD_HASH_ROUNDS": {
                "type": "int",
                "min": 10,
                "max": 20,
                "description": "密码哈希轮数",
                "category": "安全配置",
                "editable": True,
                "requires_restart": True
            },
            "DEFAULT_CACHE_TIMEOUT": {
                "type": "int",
                "min": 60,
                "max": 86400,
                "description": "默认缓存超时时间（秒）",
                "category": "缓存配置",
                "editable": True,
                "requires_restart": False
            },
            "MAX_FILE_SIZE": {
                "type": "int",
                "min": 1024,
                "max": 104857600,
                "description": "最大文件大小（字节）",
                "category": "文件配置",
                "editable": True,
                "requires_restart": True
            },
            "CONNECTION_TIMEOUT": {
                "type": "int",
                "min": 5,
                "max": 300,
                "description": "数据库连接超时时间（秒）",
                "category": "数据库配置",
                "editable": True,
                "requires_restart": False
            },
            "RATE_LIMIT_REQUESTS": {
                "type": "int",
                "min": 10,
                "max": 10000,
                "description": "速率限制请求数",
                "category": "安全配置",
                "editable": True,
                "requires_restart": False
            },
            "RATE_LIMIT_WINDOW": {
                "type": "int",
                "min": 60,
                "max": 3600,
                "description": "速率限制时间窗口（秒）",
                "category": "安全配置",
                "editable": True,
                "requires_restart": False
            },
            "LOG_MAX_SIZE": {
                "type": "int",
                "min": 1048576,
                "max": 104857600,
                "description": "日志文件最大大小（字节）",
                "category": "日志配置",
                "editable": True,
                "requires_restart": True
            },
            "LOG_RETENTION_DAYS": {
                "type": "int",
                "min": 7,
                "max": 365,
                "description": "日志保留天数",
                "category": "日志配置",
                "editable": True,
                "requires_restart": False
            },
            "JWT_ACCESS_TOKEN_EXPIRES": {
                "type": "int",
                "min": 300,
                "max": 86400,
                "description": "JWT访问令牌过期时间（秒）",
                "category": "安全配置",
                "editable": True,
                "requires_restart": False
            },
            "SESSION_LIFETIME": {
                "type": "int",
                "min": 300,
                "max": 86400,
                "description": "会话生命周期（秒）",
                "category": "安全配置",
                "editable": True,
                "requires_restart": False
            },
            "SLOW_QUERY_THRESHOLD": {
                "type": "float",
                "min": 0.1,
                "max": 10.0,
                "description": "慢查询阈值（秒）",
                "category": "性能配置",
                "editable": True,
                "requires_restart": False
            },
            "MEMORY_WARNING_THRESHOLD": {
                "type": "int",
                "min": 50,
                "max": 95,
                "description": "内存警告阈值（百分比）",
                "category": "监控配置",
                "editable": True,
                "requires_restart": False
            },
            
            # 环境变量配置
            "FLASK_ENV": {
                "type": "select",
                "options": ["development", "production", "testing"],
                "description": "Flask环境",
                "category": "应用配置",
                "editable": True,
                "requires_restart": True
            },
            "DEBUG": {
                "type": "boolean",
                "description": "调试模式",
                "category": "应用配置",
                "editable": True,
                "requires_restart": True
            },
            "SECRET_KEY": {
                "type": "string",
                "min_length": 16,
                "max_length": 128,
                "description": "Flask密钥",
                "category": "安全配置",
                "editable": True,
                "requires_restart": True
            },
            "DATABASE_URL": {
                "type": "string",
                "pattern": r"^(sqlite|mysql|postgresql|oracle|mssql)://.*$",
                "description": "数据库连接URL",
                "category": "数据库配置",
                "editable": True,
                "requires_restart": True
            },
            "REDIS_URL": {
                "type": "string",
                "pattern": r"^redis://.*$",
                "description": "Redis连接URL",
                "category": "缓存配置",
                "editable": True,
                "requires_restart": True
            },
            "LOG_LEVEL": {
                "type": "select",
                "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "description": "日志级别",
                "category": "日志配置",
                "editable": True,
                "requires_restart": False
            },
            "APP_NAME": {
                "type": "string",
                "min_length": 1,
                "max_length": 100,
                "description": "应用名称",
                "category": "应用配置",
                "editable": True,
                "requires_restart": False
            },
            "BCRYPT_LOG_ROUNDS": {
                "type": "int",
                "min": 10,
                "max": 20,
                "description": "BCrypt哈希轮数",
                "category": "安全配置",
                "editable": True,
                "requires_restart": True
            },
            "WTF_CSRF_ENABLED": {
                "type": "boolean",
                "description": "启用CSRF保护",
                "category": "安全配置",
                "editable": True,
                "requires_restart": False
            },
            "SESSION_COOKIE_SECURE": {
                "type": "boolean",
                "description": "安全Cookie",
                "category": "安全配置",
                "editable": True,
                "requires_restart": False
            },
            "UPLOAD_FOLDER": {
                "type": "string",
                "min_length": 1,
                "max_length": 255,
                "description": "文件上传目录",
                "category": "文件配置",
                "editable": True,
                "requires_restart": True
            },
            "MAX_CONTENT_LENGTH": {
                "type": "int",
                "min": 1024,
                "max": 104857600,
                "description": "最大内容长度（字节）",
                "category": "文件配置",
                "editable": True,
                "requires_restart": True
            }
        }
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置项"""
        configs = {}
        
        # 从constants.py读取配置
        constants_configs = self._load_constants_configs()
        configs.update(constants_configs)
        
        # 从.env文件读取配置
        env_configs = self._load_env_configs()
        configs.update(env_configs)
        
        return configs
    
    def _load_constants_configs(self) -> Dict[str, Any]:
        """从constants.py加载配置"""
        configs = {}
        
        try:
            with open(self.constants_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析SystemConstants类中的常量
            system_constants_match = re.search(
                r'class SystemConstants:.*?(?=class|\Z)',
                content,
                re.DOTALL
            )
            
            if system_constants_match:
                constants_content = system_constants_match.group(0)
                
                # 提取常量定义
                for key, metadata in self.config_metadata.items():
                    if metadata.get('editable', False):
                        # 查找常量定义
                        pattern = rf'{key}\s*=\s*([^\n]+)'
                        match = re.search(pattern, constants_content)
                        if match:
                            value_str = match.group(1).strip()
                            try:
                                # 尝试解析值
                                value = ast.literal_eval(value_str)
                                configs[key] = {
                                    'value': value,
                                    'source': 'constants.py',
                                    'metadata': metadata
                                }
                            except (ValueError, SyntaxError):
                                logger.warning(f"无法解析常量 {key} 的值: {value_str}")
        
        except Exception as e:
            logger.error(f"加载constants.py配置失败: {e}")
        
        return configs
    
    def _load_env_configs(self) -> Dict[str, Any]:
        """从.env文件加载配置"""
        configs = {}
        
        try:
            if self.env_file.exists():
                load_dotenv(self.env_file)
            
            for key, metadata in self.config_metadata.items():
                if metadata.get('editable', False):
                    value = os.getenv(key)
                    if value is not None:
                        # 根据类型转换值
                        converted_value = self._convert_value(value, metadata['type'])
                        configs[key] = {
                            'value': converted_value,
                            'source': '.env',
                            'metadata': metadata
                        }
        
        except Exception as e:
            logger.error(f"加载.env配置失败: {e}")
        
        return configs
    
    def _convert_value(self, value: str, value_type: str) -> Any:
        """转换值类型"""
        try:
            if value_type == 'int':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return value
        except (ValueError, TypeError):
            return value
    
    def update_config(self, key: str, value: Any) -> Tuple[bool, str]:
        """更新配置项"""
        try:
            # 验证配置项
            if key not in self.config_metadata:
                return False, f"未知的配置项: {key}"
            
            metadata = self.config_metadata[key]
            if not metadata.get('editable', False):
                return False, f"配置项 {key} 不可编辑"
            
            # 验证值
            validation_result = self._validate_value(key, value, metadata)
            if not validation_result[0]:
                return False, validation_result[1]
            
            # 创建备份
            self._create_backup()
            
            # 更新配置
            if metadata.get('source') == '.env' or key in ['FLASK_ENV', 'DEBUG', 'SECRET_KEY', 'DATABASE_URL', 'REDIS_URL', 'LOG_LEVEL', 'APP_NAME', 'BCRYPT_LOG_ROUNDS', 'WTF_CSRF_ENABLED', 'SESSION_COOKIE_SECURE', 'UPLOAD_FOLDER', 'MAX_CONTENT_LENGTH']:
                success, message = self._update_env_config(key, value)
            else:
                success, message = self._update_constants_config(key, value)
            
            if success:
                logger.info(f"配置项 {key} 更新成功: {value}")
            
            return success, message
        
        except Exception as e:
            logger.error(f"更新配置项 {key} 失败: {e}")
            return False, f"更新配置失败: {str(e)}"
    
    def _validate_value(self, key: str, value: Any, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """验证配置值"""
        value_type = metadata.get('type', 'string')
        
        # 类型验证
        if value_type == 'int':
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    return False, f"值必须是整数"
        elif value_type == 'float':
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return False, f"值必须是数字"
        elif value_type == 'boolean':
            if not isinstance(value, bool):
                if isinstance(value, str):
                    if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                        return False, f"值必须是布尔值"
                else:
                    return False, f"值必须是布尔值"
        
        # 范围验证
        if 'min' in metadata and value < metadata['min']:
            return False, f"值不能小于 {metadata['min']}"
        if 'max' in metadata and value > metadata['max']:
            return False, f"值不能大于 {metadata['max']}"
        
        # 长度验证
        if 'min_length' in metadata and len(str(value)) < metadata['min_length']:
            return False, f"长度不能小于 {metadata['min_length']}"
        if 'max_length' in metadata and len(str(value)) > metadata['max_length']:
            return False, f"长度不能大于 {metadata['max_length']}"
        
        # 选项验证
        if 'options' in metadata and value not in metadata['options']:
            return False, f"值必须是以下选项之一: {', '.join(metadata['options'])}"
        
        # 正则表达式验证
        if 'pattern' in metadata:
            if not re.match(metadata['pattern'], str(value)):
                return False, f"值格式不正确"
        
        return True, ""
    
    def _update_env_config(self, key: str, value: Any) -> Tuple[bool, str]:
        """更新.env文件中的配置"""
        try:
            # 确保.env文件存在
            if not self.env_file.exists():
                if self.env_example_file.exists():
                    shutil.copy2(self.env_example_file, self.env_file)
                else:
                    self.env_file.touch()
            
            # 更新.env文件
            set_key(self.env_file, key, str(value))
            
            # 重新加载环境变量
            load_dotenv(self.env_file, override=True)
            
            return True, "配置更新成功"
        
        except Exception as e:
            return False, f"更新.env文件失败: {str(e)}"
    
    def _update_constants_config(self, key: str, value: Any) -> Tuple[bool, str]:
        """更新constants.py文件中的配置"""
        try:
            with open(self.constants_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找并替换常量值
            pattern = rf'({key}\s*=\s*)([^\n]+)'
            replacement = f'\\g<1>{repr(value)}'
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content == content:
                return False, f"未找到配置项 {key}"
            
            # 写入文件
            with open(self.constants_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True, "配置更新成功"
        
        except Exception as e:
            return False, f"更新constants.py文件失败: {str(e)}"
    
    def _create_backup(self):
        """创建配置文件备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 备份constants.py
            if self.constants_file.exists():
                backup_file = self.backup_dir / f"constants_{timestamp}.py"
                shutil.copy2(self.constants_file, backup_file)
            
            # 备份.env文件
            if self.env_file.exists():
                backup_file = self.backup_dir / f"env_{timestamp}.env"
                shutil.copy2(self.env_file, backup_file)
            
            logger.info(f"配置文件备份已创建: {timestamp}")
        
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
    
    def get_config_categories(self) -> List[str]:
        """获取配置分类列表"""
        categories = set()
        for metadata in self.config_metadata.values():
            if 'category' in metadata:
                categories.add(metadata['category'])
        return sorted(list(categories))
    
    def get_configs_by_category(self, category: str) -> Dict[str, Any]:
        """按分类获取配置项"""
        configs = self.get_all_configs()
        return {
            key: config for key, config in configs.items()
            if config['metadata'].get('category') == category
        }
    
    def get_restart_required_configs(self) -> List[str]:
        """获取需要重启的配置项"""
        return [
            key for key, metadata in self.config_metadata.items()
            if metadata.get('requires_restart', False)
        ]
    
    def export_configs(self) -> Dict[str, Any]:
        """导出所有配置"""
        configs = self.get_all_configs()
        return {
            'configs': configs,
            'categories': self.get_config_categories(),
            'restart_required': self.get_restart_required_configs(),
            'export_time': datetime.now().isoformat()
        }
    
    def import_configs(self, config_data: Dict[str, Any]) -> Tuple[bool, str]:
        """导入配置"""
        try:
            if 'configs' not in config_data:
                return False, "无效的配置数据"
            
            success_count = 0
            error_count = 0
            errors = []
            
            for key, value in config_data['configs'].items():
                success, message = self.update_config(key, value)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{key}: {message}")
            
            if error_count == 0:
                return True, f"成功导入 {success_count} 个配置项"
            else:
                return False, f"成功导入 {success_count} 个配置项，失败 {error_count} 个: {'; '.join(errors)}"
        
        except Exception as e:
            return False, f"导入配置失败: {str(e)}"
