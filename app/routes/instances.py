# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 数据库实例管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.instance import Instance
from app.models.credential import Credential
from app import db
from app.services.database_service import DatabaseService
import logging

# 创建蓝图
instances_bp = Blueprint('instances', __name__)

@instances_bp.route('/')
@login_required
def index():
    """实例管理首页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    db_type = request.args.get('db_type', '', type=str)
    
    # 构建查询
    query = Instance.query
    
    if search:
        query = query.filter(
            db.or_(
                Instance.name.contains(search),
                Instance.host.contains(search),
                Instance.description.contains(search)
            )
        )
    
    if db_type:
        query = query.filter(Instance.db_type == db_type)
    
    # 分页查询
    instances = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取所有可用的凭据
    credentials = Credential.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'instances': [instance.to_dict() for instance in instances.items],
            'pagination': {
                'page': instances.page,
                'pages': instances.pages,
                'per_page': instances.per_page,
                'total': instances.total,
                'has_next': instances.has_next,
                'has_prev': instances.has_prev
            },
            'credentials': [cred.to_dict() for cred in credentials]
        })
    
    return render_template('instances/index.html', 
                         instances=instances, 
                         credentials=credentials,
                         search=search,
                         db_type=db_type)

@instances_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建实例"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 创建新实例
            instance = Instance(
                name=data.get('name'),
                db_type=data.get('db_type'),
                host=data.get('host'),
                port=int(data.get('port', 0)),
                credential_id=int(data.get('credential_id')) if data.get('credential_id') else None,
                description=data.get('description', '')
            )
            
            # 设置其他属性
            instance.database_name = data.get('database_name')
            instance.is_active = data.get('is_active', True) in [True, 'on', '1', 1]
            
            db.session.add(instance)
            db.session.commit()
            
            # 记录操作日志
            log_operation('CREATE_INSTANCE', current_user.id, {
                'instance_id': instance.id,
                'instance_name': instance.name,
                'db_type': instance.db_type,
                'host': instance.host
            })
            
            if request.is_json:
                return jsonify({
                    'message': '实例创建成功',
                    'instance': instance.to_dict()
                }), 201
            
            flash('实例创建成功！', 'success')
            return redirect(url_for('instances.index'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"创建实例失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '创建实例失败，请重试'}), 500
            
            flash('创建实例失败，请重试', 'error')
    
    # GET请求，显示创建表单
    credentials = Credential.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'credentials': [cred.to_dict() for cred in credentials]
        })
    
    return render_template('instances/create.html', credentials=credentials)

@instances_bp.route('/test-connection', methods=['POST'])
@login_required
def test_instance_connection():
    """测试数据库连接"""
    data = request.get_json()
    
    try:
        # 创建临时实例对象进行测试
        temp_instance = Instance(
            name=data.get('name', 'test'),
            db_type=data.get('db_type'),
            host=data.get('host'),
            port=int(data.get('port', 0)),
            credential_id=int(data.get('credential_id')) if data.get('credential_id') else None,
            description='test'
        )
        temp_instance.database_name = data.get('database_name')
        
        # 获取凭据信息
        if temp_instance.credential_id:
            credential = Credential.query.get(temp_instance.credential_id)
            if credential:
                temp_instance.credential = credential
        
        # 使用数据库服务测试连接
        from app.services.database_service import DatabaseService
        db_service = DatabaseService()
        result = db_service.test_connection(temp_instance)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"测试连接失败: {e}")
        return jsonify({
            'success': False,
            'error': f'测试连接失败: {str(e)}'
        }), 500

@instances_bp.route('/<int:instance_id>')
@login_required
def detail(instance_id):
    """实例详情"""
    instance = Instance.query.get_or_404(instance_id)
    
    if request.is_json:
        return jsonify(instance.to_dict())
    
    return render_template('instances/detail.html', instance=instance)

@instances_bp.route('/<int:instance_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(instance_id):
    """编辑实例"""
    instance = Instance.query.get_or_404(instance_id)
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 更新实例信息
            instance.name = data.get('name', instance.name)
            instance.db_type = data.get('db_type', instance.db_type)
            instance.host = data.get('host', instance.host)
            instance.port = data.get('port', instance.port)
            instance.database_name = data.get('database_name', instance.database_name)
            instance.credential_id = data.get('credential_id', instance.credential_id)
            instance.description = data.get('description', instance.description)
            instance.is_active = data.get('is_active', instance.is_active)
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': '实例更新成功',
                    'instance': instance.to_dict()
                })
            
            flash('实例更新成功！', 'success')
            return redirect(url_for('instances.detail', instance_id=instance_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"更新实例失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '更新实例失败，请重试'}), 500
            
            flash('更新实例失败，请重试', 'error')
    
    # GET请求，显示编辑表单
    credentials = Credential.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'instance': instance.to_dict(),
            'credentials': [cred.to_dict() for cred in credentials]
        })
    
    return render_template('instances/edit.html', 
                         instance=instance, 
                         credentials=credentials)

@instances_bp.route('/<int:instance_id>/delete', methods=['POST'])
@login_required
def delete(instance_id):
    """删除实例"""
    instance = Instance.query.get_or_404(instance_id)
    
    try:
        db.session.delete(instance)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': '实例删除成功'})
        
        flash('实例删除成功！', 'success')
        return redirect(url_for('instances.index'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"删除实例失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '删除实例失败，请重试'}), 500
        
        flash('删除实例失败，请重试', 'error')
        return redirect(url_for('instances.index'))

@instances_bp.route('/<int:instance_id>/test', methods=['POST'])
@login_required
def test_connection(instance_id):
    """测试数据库连接"""
    instance = Instance.query.get_or_404(instance_id)
    
    try:
        # 使用数据库服务测试连接
        db_service = DatabaseService()
        result = db_service.test_connection(instance)
        
        if result['success']:
            # 更新最后连接时间
            instance.last_connected = db.func.now()
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': '连接测试成功',
                    'result': result
                })
            
            flash('连接测试成功！', 'success')
        else:
            if request.is_json:
                return jsonify({
                    'error': '连接测试失败',
                    'result': result
                }), 400
            
            flash(f'连接测试失败: {result.get("error", "未知错误")}', 'error')
            
    except Exception as e:
        logging.error(f"测试连接失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '连接测试失败，请重试'}), 500
        
        flash('连接测试失败，请重试', 'error')
    
    return redirect(url_for('instances.detail', instance_id=instance_id))

@instances_bp.route('/<int:instance_id>/sync', methods=['POST'])
@login_required
def sync_accounts(instance_id):
    """同步账户信息"""
    instance = Instance.query.get_or_404(instance_id)
    
    try:
        # 使用数据库服务同步账户
        db_service = DatabaseService()
        result = db_service.sync_accounts(instance)
        
        if result['success']:
            if request.is_json:
                return jsonify({
                    'message': '账户同步成功',
                    'result': result
                })
            
            flash('账户同步成功！', 'success')
        else:
            if request.is_json:
                return jsonify({
                    'error': '账户同步失败',
                    'result': result
                }), 400
            
            flash(f'账户同步失败: {result.get("error", "未知错误")}', 'error')
            
    except Exception as e:
        logging.error(f"同步账户失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '账户同步失败，请重试'}), 500
        
        flash('账户同步失败，请重试', 'error')
    
    return redirect(url_for('instances.detail', instance_id=instance_id))

# API路由
@instances_bp.route('/api/instances')
@jwt_required()
def api_list():
    """获取实例列表API"""
    instances = Instance.query.filter_by(is_active=True).all()
    return jsonify([instance.to_dict() for instance in instances])

@instances_bp.route('/api/instances/<int:instance_id>')
@jwt_required()
def api_detail(instance_id):
    """获取实例详情API"""
    instance = Instance.query.get_or_404(instance_id)
    return jsonify(instance.to_dict())

@instances_bp.route('/api/instances/<int:instance_id>/test')
@jwt_required()
def api_test_connection(instance_id):
    """测试连接API"""
    instance = Instance.query.get_or_404(instance_id)
    
    try:
        db_service = DatabaseService()
        result = db_service.test_connection(instance)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500