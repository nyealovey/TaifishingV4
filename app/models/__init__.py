"""
泰摸鱼吧 - 数据模型
"""

from app import db

# 导入所有模型
from .user import User
from .instance import Instance
from .credential import Credential
from .account import Account
from .task import Task
from .log import Log
from .global_param import GlobalParam
from .sync_data import SyncData

# 导出所有模型
__all__ = [
    'User',
    'Instance', 
    'Credential',
    'Account',
    'Task',
    'Log',
    'GlobalParam',
    'SyncData'
]
