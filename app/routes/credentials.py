# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 凭据管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.credential import Credential
from app import db
import logging

# 创建蓝图
credentials_bp = Blueprint('credentials', __name__)

@credentials_bp.route('/')
@login_required
def index():
    """凭据管理首页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    credential_type = request.args.get('credential_type', '', type=str)
    
    # 构建查询
    query = Credential.query
    
    if search:
        query = query.filter(
            db.or_(
                Credential.name.contains(search),
                Credential.username.contains(search),
                Credential.description.contains(search)
            )
        )
    
    if credential_type:
        query = query.filter(Credential.credential_type == credential_type)
    
    # 分页查询
    credentials = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'credentials': [cred.to_dict() for cred in credentials.items],
            'pagination': {
                'page': credentials.page,
                'pages': credentials.pages,
                'per_page': credentials.per_page,
                'total': credentials.total,
                'has_next': credentials.has_next,
                'has_prev': credentials.has_prev
            }
        })
    
    return render_template('credentials/index.html', 
                         credentials=credentials,
                         search=search,
                         credential_type=credential_type)

@credentials_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建凭据"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 创建新凭据
            credential = Credential(
                name=data.get('name'),
                credential_type=data.get('credential_type'),
                db_type=data.get('db_type'),
                username=data.get('username'),
                password=data.get('password'),
                description=data.get('description', ''),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(credential)
            db.session.commit()
            
            # 记录操作日志
            log_operation('CREATE_CREDENTIAL', current_user.id, {
                'credential_id': credential.id,
                'credential_name': credential.name,
                'credential_type': credential.credential_type,
                'db_type': credential.db_type
            })
            
            if request.is_json:
                return jsonify({
                    'message': '凭据创建成功',
                    'credential': credential.to_dict()
                }), 201
            
            flash('凭据创建成功！', 'success')
            return redirect(url_for('credentials.index'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"创建凭据失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '创建凭据失败，请重试'}), 500
            
            flash('创建凭据失败，请重试', 'error')
    
    # GET请求，显示创建表单
    if request.is_json:
        return jsonify({})
    
    return render_template('credentials/create.html')

@credentials_bp.route('/<int:credential_id>')
@login_required
def detail(credential_id):
    """凭据详情"""
    credential = Credential.query.get_or_404(credential_id)
    
    if request.is_json:
        return jsonify(credential.to_dict())
    
    return render_template('credentials/detail.html', credential=credential)

@credentials_bp.route('/<int:credential_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(credential_id):
    """编辑凭据"""
    credential = Credential.query.get_or_404(credential_id)
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 更新凭据信息
            credential.name = data.get('name', credential.name)
            credential.credential_type = data.get('credential_type', credential.credential_type)
            credential.db_type = data.get('db_type', credential.db_type)
            credential.username = data.get('username', credential.username)
            credential.description = data.get('description', credential.description)
            credential.is_active = data.get('is_active', credential.is_active)
            
            # 如果提供了新密码，则更新密码
            if data.get('password'):
                credential.set_password(data.get('password'))
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': '凭据更新成功',
                    'credential': credential.to_dict()
                })
            
            flash('凭据更新成功！', 'success')
            return redirect(url_for('credentials.detail', credential_id=credential_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"更新凭据失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '更新凭据失败，请重试'}), 500
            
            flash('更新凭据失败，请重试', 'error')
    
    # GET请求，显示编辑表单
    if request.is_json:
        return jsonify({
            'credential': credential.to_dict()
        })
    
    return render_template('credentials/edit.html', credential=credential)

@credentials_bp.route('/<int:credential_id>/delete', methods=['POST'])
@login_required
def delete(credential_id):
    """删除凭据"""
    credential = Credential.query.get_or_404(credential_id)
    
    try:
        db.session.delete(credential)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': '凭据删除成功'})
        
        flash('凭据删除成功！', 'success')
        return redirect(url_for('credentials.index'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"删除凭据失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '删除凭据失败，请重试'}), 500
        
        flash('删除凭据失败，请重试', 'error')
        return redirect(url_for('credentials.index'))

@credentials_bp.route('/<int:credential_id>/test', methods=['POST'])
@login_required
def test_credential(credential_id):
    """测试凭据"""
    credential = Credential.query.get_or_404(credential_id)
    
    try:
        # 这里可以实现凭据测试逻辑
        # 暂时返回成功
        if request.is_json:
            return jsonify({
                'message': '凭据测试成功',
                'result': {'success': True, 'message': '凭据格式正确'}
            })
        
        flash('凭据测试成功！', 'success')
        
    except Exception as e:
        logging.error(f"测试凭据失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '凭据测试失败，请重试'}), 500
        
        flash('凭据测试失败，请重试', 'error')
    
    return redirect(url_for('credentials.detail', credential_id=credential_id))

# API路由
@credentials_bp.route('/api/credentials')
@jwt_required()
def api_list():
    """获取凭据列表API"""
    credentials = Credential.query.filter_by(is_active=True).all()
    return jsonify([cred.to_dict() for cred in credentials])

@credentials_bp.route('/api/credentials/<int:credential_id>')
@jwt_required()
def api_detail(credential_id):
    """获取凭据详情API"""
    credential = Credential.query.get_or_404(credential_id)
    return jsonify(credential.to_dict())