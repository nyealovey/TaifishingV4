# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 配置管理工具
"""

import os
import json
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ConfigType(Enum):
    """配置类型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    DICT = "dict"

@dataclass
class ConfigItem:
    """配置项"""
    key: str
    value: Any
    type: ConfigType
    description: str = ""
    required: bool = False
    default: Any = None
    validation: Optional[callable] = None

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.config_items: Dict[str, ConfigItem] = {}
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"配置加载成功: {self.config_file}")
            else:
                logger.info("配置文件不存在，使用默认配置")
                self.config = {}
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self.config = {}
    
    def save_config(self):
        """保存配置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置保存成功: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def register_config(self, item: ConfigItem):
        """注册配置项"""
        self.config_items[item.key] = item
        
        # 如果配置中不存在该键，使用默认值
        if item.key not in self.config:
            self.config[item.key] = item.default
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        # 优先从环境变量获取
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return self._convert_value(env_value, self.config_items.get(key))
        
        # 从配置文件获取
        value = self.config.get(key, default)
        
        # 如果配置项已注册，进行类型转换
        if key in self.config_items:
            return self._convert_value(value, self.config_items[key])
        
        return value
    
    def set(self, key: str, value: Any, save: bool = True):
        """设置配置值"""
        # 验证配置项
        if key in self.config_items:
            item = self.config_items[key]
            if item.validation and not item.validation(value):
                raise ValueError(f"配置项 {key} 的值 {value} 验证失败")
        
        self.config[key] = value
        
        if save:
            self.save_config()
    
    def _convert_value(self, value: Any, item: Optional[ConfigItem]) -> Any:
        """转换配置值类型"""
        if not item:
            return value
        
        try:
            if item.type == ConfigType.STRING:
                return str(value)
            elif item.type == ConfigType.INTEGER:
                return int(value)
            elif item.type == ConfigType.FLOAT:
                return float(value)
            elif item.type == ConfigType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif item.type == ConfigType.JSON:
                if isinstance(value, str):
                    return json.loads(value)
                return value
            elif item.type == ConfigType.LIST:
                if isinstance(value, str):
                    return json.loads(value)
                return list(value)
            elif item.type == ConfigType.DICT:
                if isinstance(value, str):
                    return json.loads(value)
                return dict(value)
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.warning(f"配置值类型转换失败: {key}={value}, 错误: {e}")
            return item.default if item.default is not None else value
    
    def validate_config(self) -> Dict[str, List[str]]:
        """验证配置"""
        errors = {}
        
        for key, item in self.config_items.items():
            if item.required and key not in self.config:
                errors[key] = [f"必需配置项 {key} 未设置"]
                continue
            
            if key in self.config:
                value = self.config[key]
                if item.validation and not item.validation(value):
                    errors[key] = [f"配置项 {key} 的值 {value} 验证失败"]
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'total_items': len(self.config_items),
            'configured_items': len(self.config),
            'required_items': sum(1 for item in self.config_items.values() if item.required),
            'missing_required': [
                key for key, item in self.config_items.items()
                if item.required and key not in self.config
            ],
            'validation_errors': self.validate_config()
        }

# 应用配置管理器
class AppConfigManager(ConfigManager):
    """应用配置管理器"""
    
    def __init__(self):
        super().__init__("userdata/app_config.json")
        self._register_default_configs()
    
    def _register_default_configs(self):
        """注册默认配置"""
        # 数据库配置
        self.register_config(ConfigItem(
            key="database_url",
            value="sqlite:///userdata/taifish_dev.db",
            type=ConfigType.STRING,
            description="数据库连接URL",
            required=True,
            validation=lambda x: x and isinstance(x, str)
        ))
        
        # Redis配置
        self.register_config(ConfigItem(
            key="redis_url",
            value="redis://localhost:6379/0",
            type=ConfigType.STRING,
            description="Redis连接URL",
            validation=lambda x: x and isinstance(x, str)
        ))
        
        # 日志配置
        self.register_config(ConfigItem(
            key="log_level",
            value="INFO",
            type=ConfigType.STRING,
            description="日志级别",
            validation=lambda x: x in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        ))
        
        self.register_config(ConfigItem(
            key="log_max_size",
            value=10485760,  # 10MB
            type=ConfigType.INTEGER,
            description="日志文件最大大小（字节）",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        self.register_config(ConfigItem(
            key="log_backup_count",
            value=5,
            type=ConfigType.INTEGER,
            description="日志备份文件数量",
            validation=lambda x: isinstance(x, int) and x >= 0
        ))
        
        # 安全配置
        self.register_config(ConfigItem(
            key="secret_key",
            value="",
            type=ConfigType.STRING,
            description="应用密钥",
            required=True,
            validation=lambda x: x and len(x) >= 32
        ))
        
        self.register_config(ConfigItem(
            key="jwt_secret_key",
            value="",
            type=ConfigType.STRING,
            description="JWT密钥",
            required=True,
            validation=lambda x: x and len(x) >= 32
        ))
        
        # 缓存配置
        self.register_config(ConfigItem(
            key="cache_type",
            value="simple",
            type=ConfigType.STRING,
            description="缓存类型",
            validation=lambda x: x in ['simple', 'redis', 'memcached']
        ))
        
        self.register_config(ConfigItem(
            key="cache_default_timeout",
            value=300,
            type=ConfigType.INTEGER,
            description="默认缓存超时时间（秒）",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        # 任务配置
        self.register_config(ConfigItem(
            key="task_timeout",
            value=300,
            type=ConfigType.INTEGER,
            description="任务执行超时时间（秒）",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        self.register_config(ConfigItem(
            key="max_concurrent_tasks",
            value=10,
            type=ConfigType.INTEGER,
            description="最大并发任务数",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        # 连接池配置
        self.register_config(ConfigItem(
            key="db_pool_size",
            value=10,
            type=ConfigType.INTEGER,
            description="数据库连接池大小",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        self.register_config(ConfigItem(
            key="db_pool_timeout",
            value=20,
            type=ConfigType.INTEGER,
            description="数据库连接池超时时间（秒）",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        # 监控配置
        self.register_config(ConfigItem(
            key="enable_monitoring",
            value=True,
            type=ConfigType.BOOLEAN,
            description="启用监控",
            validation=lambda x: isinstance(x, bool)
        ))
        
        self.register_config(ConfigItem(
            key="monitoring_interval",
            value=60,
            type=ConfigType.INTEGER,
            description="监控间隔（秒）",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        # 备份配置
        self.register_config(ConfigItem(
            key="backup_enabled",
            value=True,
            type=ConfigType.BOOLEAN,
            description="启用自动备份",
            validation=lambda x: isinstance(x, bool)
        ))
        
        self.register_config(ConfigItem(
            key="backup_interval",
            value=86400,  # 24小时
            type=ConfigType.INTEGER,
            description="备份间隔（秒）",
            validation=lambda x: isinstance(x, int) and x > 0
        ))
        
        self.register_config(ConfigItem(
            key="max_backups",
            value=30,
            type=ConfigType.INTEGER,
            description="最大备份文件数",
            validation=lambda x: isinstance(x, int) and x > 0
        ))

# 全局配置管理器
app_config = AppConfigManager()

def get_config(key: str, default: Any = None) -> Any:
    """获取配置的便捷函数"""
    return app_config.get(key, default)

def set_config(key: str, value: Any, save: bool = True):
    """设置配置的便捷函数"""
    app_config.set(key, value, save)

def validate_all_configs() -> Dict[str, List[str]]:
    """验证所有配置的便捷函数"""
    return app_config.validate_config()

def get_config_summary() -> Dict[str, Any]:
    """获取配置摘要的便捷函数"""
    return app_config.get_config_summary()
