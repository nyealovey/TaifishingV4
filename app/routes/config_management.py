# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 配置管理路由
提供动态修改配置的Web界面
"""

import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.exceptions import BadRequest

from app.services.config_manager import ConfigManager
from app.utils.decorators import admin_required
from app.utils.api_response import APIResponse

config_management_bp = Blueprint('config_management', __name__, url_prefix='/config-management')

# 初始化配置管理器
config_manager = ConfigManager()


@config_management_bp.route('/')
@login_required
@admin_required
def index():
    """配置管理主页"""
    try:
        # 获取所有配置
        configs = config_manager.get_all_configs()
        categories = config_manager.get_config_categories()
        restart_required = config_manager.get_restart_required_configs()
        
        # 按分类组织配置
        configs_by_category = {}
        for category in categories:
            configs_by_category[category] = config_manager.get_configs_by_category(category)
        
        return render_template('config_management/index.html',
                             configs=configs,
                             configs_by_category=configs_by_category,
                             categories=categories,
                             restart_required=restart_required)
    
    except Exception as e:
        flash(f'加载配置失败: {str(e)}', 'error')
        return render_template('config_management/index.html',
                             configs={},
                             configs_by_category={},
                             categories=[],
                             restart_required=[])


@config_management_bp.route('/api/configs')
@login_required
@admin_required
def api_get_configs():
    """获取所有配置API"""
    try:
        configs = config_manager.get_all_configs()
        categories = config_manager.get_config_categories()
        restart_required = config_manager.get_restart_required_configs()
        
        return APIResponse.success(data={
            'configs': configs,
            'categories': categories,
            'restart_required': restart_required
        })
    
    except Exception as e:
        return APIResponse.server_error(f'获取配置失败: {str(e)}')


@config_management_bp.route('/api/configs/<category>')
@login_required
@admin_required
def api_get_configs_by_category(category):
    """按分类获取配置API"""
    try:
        configs = config_manager.get_configs_by_category(category)
        return APIResponse.success(data={'configs': configs})
    
    except Exception as e:
        return APIResponse.server_error(f'获取配置失败: {str(e)}')


@config_management_bp.route('/api/configs/<key>', methods=['PUT'])
@login_required
@admin_required
def api_update_config(key):
    """更新配置API"""
    try:
        data = request.get_json()
        if not data or 'value' not in data:
            return APIResponse.bad_request('缺少配置值')
        
        value = data['value']
        success, message = config_manager.update_config(key, value)
        
        if success:
            return APIResponse.success(message=message)
        else:
            return APIResponse.bad_request(message)
    
    except Exception as e:
        return APIResponse.server_error(f'更新配置失败: {str(e)}')


@config_management_bp.route('/api/configs/batch', methods=['PUT'])
@login_required
@admin_required
def api_batch_update_configs():
    """批量更新配置API"""
    try:
        data = request.get_json()
        if not data or 'configs' not in data:
            return APIResponse.bad_request('缺少配置数据')
        
        configs = data['configs']
        success_count = 0
        error_count = 0
        errors = []
        
        for key, value in configs.items():
            success, message = config_manager.update_config(key, value)
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(f"{key}: {message}")
        
        if error_count == 0:
            return APIResponse.success(message=f'成功更新 {success_count} 个配置项')
        else:
            return APIResponse.partial_success(
                message=f'成功更新 {success_count} 个配置项，失败 {error_count} 个',
                data={'errors': errors}
            )
    
    except Exception as e:
        return APIResponse.server_error(f'批量更新配置失败: {str(e)}')


@config_management_bp.route('/api/configs/export')
@login_required
@admin_required
def api_export_configs():
    """导出配置API"""
    try:
        config_data = config_manager.export_configs()
        return jsonify(config_data)
    
    except Exception as e:
        return APIResponse.server_error(f'导出配置失败: {str(e)}')


@config_management_bp.route('/api/configs/import', methods=['POST'])
@login_required
@admin_required
def api_import_configs():
    """导入配置API"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.bad_request('缺少配置数据')
        
        success, message = config_manager.import_configs(data)
        
        if success:
            return APIResponse.success(message=message)
        else:
            return APIResponse.bad_request(message)
    
    except Exception as e:
        return APIResponse.server_error(f'导入配置失败: {str(e)}')


@config_management_bp.route('/api/configs/validate', methods=['POST'])
@login_required
@admin_required
def api_validate_config():
    """验证配置API"""
    try:
        data = request.get_json()
        if not data or 'key' not in data or 'value' not in data:
            return APIResponse.bad_request('缺少配置键或值')
        
        key = data['key']
        value = data['value']
        
        # 获取配置元数据
        metadata = config_manager.config_metadata.get(key, {})
        if not metadata:
            return APIResponse.bad_request(f'未知的配置项: {key}')
        
        # 验证值
        validation_result = config_manager._validate_value(key, value, metadata)
        
        if validation_result[0]:
            return APIResponse.success(message='配置值有效')
        else:
            return APIResponse.bad_request(validation_result[1])
    
    except Exception as e:
        return APIResponse.server_error(f'验证配置失败: {str(e)}')


@config_management_bp.route('/api/configs/reset/<key>', methods=['POST'])
@login_required
@admin_required
def api_reset_config(key):
    """重置配置到默认值API"""
    try:
        # 获取默认值
        metadata = config_manager.config_metadata.get(key, {})
        if not metadata:
            return APIResponse.bad_request(f'未知的配置项: {key}')
        
        # 这里可以从DefaultConfig类获取默认值
        # 暂时返回错误，提示需要手动设置
        return APIResponse.bad_request('重置功能暂未实现，请手动设置默认值')
    
    except Exception as e:
        return APIResponse.server_error(f'重置配置失败: {str(e)}')


@config_management_bp.route('/api/configs/backup', methods=['POST'])
@login_required
@admin_required
def api_create_backup():
    """创建配置备份API"""
    try:
        config_manager._create_backup()
        return APIResponse.success(message='配置备份已创建')
    
    except Exception as e:
        return APIResponse.server_error(f'创建备份失败: {str(e)}')


@config_management_bp.route('/api/configs/restart-required')
@login_required
@admin_required
def api_get_restart_required():
    """获取需要重启的配置项API"""
    try:
        restart_required = config_manager.get_restart_required_configs()
        return APIResponse.success(data={'restart_required': restart_required})
    
    except Exception as e:
        return APIResponse.server_error(f'获取重启配置失败: {str(e)}')


@config_management_bp.route('/api/configs/categories')
@login_required
@admin_required
def api_get_categories():
    """获取配置分类API"""
    try:
        categories = config_manager.get_config_categories()
        return APIResponse.success(data={'categories': categories})
    
    except Exception as e:
        return APIResponse.server_error(f'获取分类失败: {str(e)}')


@config_management_bp.route('/help')
@login_required
@admin_required
def help_page():
    """配置管理帮助页面"""
    return render_template('config_management/help.html')


@config_management_bp.route('/history')
@login_required
@admin_required
def history_page():
    """配置修改历史页面"""
    try:
        # 获取备份文件列表
        backup_files = []
        if config_manager.backup_dir.exists():
            for file_path in config_manager.backup_dir.iterdir():
                if file_path.is_file():
                    backup_files.append({
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    })
        
        # 按修改时间排序
        backup_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return render_template('config_management/history.html', backup_files=backup_files)
    
    except Exception as e:
        flash(f'加载历史记录失败: {str(e)}', 'error')
        return render_template('config_management/history.html', backup_files=[])


@config_management_bp.errorhandler(BadRequest)
def handle_bad_request(e):
    """处理错误请求"""
    return APIResponse.bad_request(str(e))


@config_management_bp.errorhandler(404)
def handle_not_found(e):
    """处理404错误"""
    return APIResponse.not_found('页面不存在')


@config_management_bp.errorhandler(500)
def handle_internal_error(e):
    """处理500错误"""
    return APIResponse.server_error('服务器内部错误')
