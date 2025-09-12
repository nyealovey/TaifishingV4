# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 数据库类型管理路由
提供数据库类型的Web界面和API接口
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.database_type_service import DatabaseTypeService
from app.utils.enhanced_logger import log_operation
from app.utils.security import validate_required_fields
import json

database_types_bp = Blueprint('database_types', __name__, url_prefix='/database-types')

@database_types_bp.route('/')
@login_required
def index():
    """数据库类型管理首页"""
    types = DatabaseTypeService.get_all_types()
    return render_template('database_types/index.html', types=types)

@database_types_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建数据库类型"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # 验证必填字段
        required_fields = ['name', 'display_name', 'driver', 'default_port', 'default_schema']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['valid']:
            return jsonify({'success': False, 'message': validation_result['message']})
        
        # 处理特性列表
        if 'features' in data and isinstance(data['features'], str):
            try:
                data['features'] = json.loads(data['features'])
            except:
                data['features'] = []
        
        result = DatabaseTypeService.create_type(data)
        
        if request.is_json:
            return jsonify(result)
        else:
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('database_types.index'))
            else:
                flash(result['message'], 'error')
    
    return render_template('database_types/create.html')

@database_types_bp.route('/<int:type_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(type_id):
    """编辑数据库类型"""
    config = DatabaseTypeService.get_type_by_id(type_id)
    if not config:
        flash('数据库类型不存在', 'error')
        return redirect(url_for('database_types.index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # 处理特性列表
        if 'features' in data and isinstance(data['features'], str):
            try:
                data['features'] = json.loads(data['features'])
            except:
                data['features'] = []
        
        result = DatabaseTypeService.update_type(type_id, data)
        
        if request.is_json:
            return jsonify(result)
        else:
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('database_types.index'))
            else:
                flash(result['message'], 'error')
    
    return render_template('database_types/edit.html', config=config)

@database_types_bp.route('/<int:type_id>/delete', methods=['POST'])
@login_required
def delete(type_id):
    """删除数据库类型"""
    result = DatabaseTypeService.delete_type(type_id)
    
    if request.is_json:
        return jsonify(result)
    else:
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
        return redirect(url_for('database_types.index'))

@database_types_bp.route('/<int:type_id>/toggle', methods=['POST'])
@login_required
def toggle_status(type_id):
    """切换启用状态"""
    result = DatabaseTypeService.toggle_status(type_id)
    return jsonify(result)

@database_types_bp.route('/api/list')
@login_required
def api_list():
    """API: 获取数据库类型列表"""
    types = DatabaseTypeService.get_all_types()
    return jsonify({
        'success': True,
        'data': [config.to_dict() for config in types]
    })

@database_types_bp.route('/api/active')
@login_required
def api_active():
    """API: 获取启用的数据库类型"""
    types = DatabaseTypeService.get_active_types()
    return jsonify({
        'success': True,
        'data': [config.to_dict() for config in types]
    })

@database_types_bp.route('/api/form-options')
@login_required
def api_form_options():
    """API: 获取用于表单的数据库类型选项"""
    options = DatabaseTypeService.get_database_types_for_form()
    return jsonify({
        'success': True,
        'data': options
    })

@database_types_bp.route('/init-defaults', methods=['POST'])
@login_required
def init_defaults():
    """初始化默认数据库类型"""
    try:
        DatabaseTypeService.init_default_types()
        return jsonify({
            'success': True,
            'message': '默认数据库类型初始化成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'初始化失败: {str(e)}'
        })
