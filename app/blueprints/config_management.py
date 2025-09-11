"""
配置管理蓝图
"""
from flask import Blueprint

config_management_bp = Blueprint(
    'config_management',
    __name__,
    url_prefix='/config',
    template_folder='../templates/config_management'
)

# 导入路由
from app.routes.config_management import *
