# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 用户认证路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from app.models.user import User
from app import db, bcrypt
from app.utils.logger import log_operation
from app.utils.rate_limiter import login_rate_limit, password_reset_rate_limit, registration_rate_limit

# 创建蓝图
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@login_rate_limit
def login():
    """用户登录页面"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            flash('用户名和密码不能为空', 'error')
            return render_template('auth/login.html')
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.is_active:
                # 登录成功
                login_user(user, remember=True)
                
                # 记录登录日志
                log_operation('USER_LOGIN', user.id, {
                    'username': user.username,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent')
                })
                
                if request.is_json:
                    # API登录，返回JWT token
                    access_token = create_access_token(identity=user.id)
                    refresh_token = create_refresh_token(identity=user.id)
                    return jsonify({
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'token_type': 'Bearer',
                        'expires_in': 3600,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'role': user.role,
                            'is_active': user.is_active
                        }
                    })
                else:
                    # Web登录，重定向到首页
                    flash('登录成功！', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page) if next_page else redirect(url_for('main.index'))
            else:
                if request.is_json:
                    return jsonify({'error': '账户已被禁用'}), 403
                flash('账户已被禁用', 'error')
        else:
            if request.is_json:
                return jsonify({'error': '用户名或密码错误'}), 401
            flash('用户名或密码错误', 'error')
    
    # GET请求，显示登录页面
    if request.is_json:
        return jsonify({'error': '请使用POST方法登录'}), 405
    
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    # 记录登出日志
    log_operation('USER_LOGOUT', current_user.id, {
        'username': current_user.username,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    })
    
    logout_user()
    
    if request.is_json:
        return jsonify({'message': '登出成功'})
    
    flash('已成功登出', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@registration_rate_limit
def register():
    """用户注册页面"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        email = data.get('email')
        
        # 验证输入
        if not username or not password:
            if request.is_json:
                return jsonify({'error': '用户名和密码不能为空'}), 400
            flash('用户名和密码不能为空', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            if request.is_json:
                return jsonify({'error': '两次输入的密码不一致'}), 400
            flash('两次输入的密码不一致', 'error')
            return render_template('auth/register.html')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'error': '用户名已存在'}), 400
            flash('用户名已存在', 'error')
            return render_template('auth/register.html')
        
        # 创建新用户
        try:
            user = User(
                username=username,
                password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
                email=email,
                role='user',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'message': '注册成功'}), 201
            
            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': '注册失败，请重试'}), 500
            flash('注册失败，请重试', 'error')
    
    # GET请求，显示注册页面
    if request.is_json:
        return jsonify({'error': '请使用POST方法注册'}), 405
    
    return render_template('auth/register.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """用户资料页面"""
    if request.is_json:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role,
            'is_active': current_user.is_active,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        })
    
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@password_reset_rate_limit
def change_password():
    """修改密码页面"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # 验证输入
        if not old_password or not new_password:
            if request.is_json:
                return jsonify({'error': '所有字段都不能为空'}), 400
            flash('所有字段都不能为空', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            if request.is_json:
                return jsonify({'error': '两次输入的新密码不一致'}), 400
            flash('两次输入的新密码不一致', 'error')
            return render_template('auth/change_password.html')
        
        # 验证旧密码
        if not current_user.check_password(old_password):
            if request.is_json:
                return jsonify({'error': '旧密码错误'}), 400
            flash('旧密码错误', 'error')
            return render_template('auth/change_password.html')
        
        # 更新密码
        try:
            current_user.set_password(new_password)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'message': '密码修改成功'})
            
            flash('密码修改成功！', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': '密码修改失败，请重试'}), 500
            flash('密码修改失败，请重试', 'error')
    
    # GET请求，显示修改密码页面
    if request.is_json:
        return jsonify({'error': '请使用POST方法修改密码'}), 405
    
    return render_template('auth/change_password.html')

# API路由
@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新JWT token"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 3600
    })

@auth_bp.route('/api/me')
@jwt_required()
def me():
    """获取当前用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    })