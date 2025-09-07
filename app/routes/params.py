# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 系统参数管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.param import Param
from app import db
import logging
from datetime import datetime

# 创建蓝图
params_bp = Blueprint('params', __name__)

@params_bp.route('/')
@login_required
def index():
    """参数管理首页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category', '', type=str)
    search = request.args.get('search', '', type=str)
    
    # 构建查询
    query = Param.query
    
    if category:
        query = query.filter(Param.category == category)
    
    if search:
        query = query.filter(
            db.or_(
                Param.name.contains(search),
                Param.description.contains(search),
                Param.value.contains(search)
            )
        )
    
    # 分页查询
    params = query.order_by(Param.category, Param.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取所有分类
    categories = db.session.query(Param.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    if request.is_json:
        return jsonify({
            'params': [param.to_dict() for param in params.items],
            'pagination': {
                'page': params.page,
                'pages': params.pages,
                'per_page': params.per_page,
                'total': params.total,
                'has_next': params.has_next,
                'has_prev': params.has_prev
            },
            'categories': categories
        })
    
    return render_template('params/index.html', 
                         params=params,
                         categories=categories,
                         category=category,
                         search=search)

@params_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建参数"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 创建新参数
            param = Param(
                name=data.get('name'),
                value=data.get('value'),
                param_type=data.get('param_type'),
                category=data.get('category'),
                description=data.get('description', ''),
                is_system=data.get('is_system', False)
            )
            
            db.session.add(param)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': '参数创建成功',
                    'param': param.to_dict()
                }), 201
            
            flash('参数创建成功！', 'success')
            return redirect(url_for('params.index'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"创建参数失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '创建参数失败，请重试'}), 500
            
            flash('创建参数失败，请重试', 'error')
    
    # GET请求，显示创建表单
    if request.is_json:
        return jsonify({})
    
    return render_template('params/create.html')

@params_bp.route('/<int:param_id>')
@login_required
def detail(param_id):
    """参数详情"""
    param = Param.query.get_or_404(param_id)
    
    if request.is_json:
        return jsonify(param.to_dict())
    
    return render_template('params/detail.html', param=param)

@params_bp.route('/<int:param_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(param_id):
    """编辑参数"""
    param = Param.query.get_or_404(param_id)
    
    # 系统参数不允许编辑
    if param.is_system:
        if request.is_json:
            return jsonify({'error': '系统参数不允许编辑'}), 400
        flash('系统参数不允许编辑', 'error')
        return redirect(url_for('params.index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 更新参数信息
            param.name = data.get('name', param.name)
            param.value = data.get('value', param.value)
            param.param_type = data.get('param_type', param.param_type)
            param.category = data.get('category', param.category)
            param.description = data.get('description', param.description)
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': '参数更新成功',
                    'param': param.to_dict()
                })
            
            flash('参数更新成功！', 'success')
            return redirect(url_for('params.detail', param_id=param_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"更新参数失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '更新参数失败，请重试'}), 500
            
            flash('更新参数失败，请重试', 'error')
    
    # GET请求，显示编辑表单
    if request.is_json:
        return jsonify({
            'param': param.to_dict()
        })
    
    return render_template('params/edit.html', param=param)

@params_bp.route('/<int:param_id>/delete', methods=['POST'])
@login_required
def delete(param_id):
    """删除参数"""
    param = Param.query.get_or_404(param_id)
    
    # 系统参数不允许删除
    if param.is_system:
        if request.is_json:
            return jsonify({'error': '系统参数不允许删除'}), 400
        flash('系统参数不允许删除', 'error')
        return redirect(url_for('params.index'))
    
    try:
        db.session.delete(param)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': '参数删除成功'})
        
        flash('参数删除成功！', 'success')
        return redirect(url_for('params.index'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"删除参数失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '删除参数失败，请重试'}), 500
        
        flash('删除参数失败，请重试', 'error')
        return redirect(url_for('params.index'))

@params_bp.route('/reset', methods=['POST'])
@login_required
def reset_to_default():
    """重置为默认值"""
    try:
        # 重置所有非系统参数为默认值
        params = Param.query.filter_by(is_system=False).all()
        
        for param in params:
            param.value = param.default_value
            param.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': f'已重置 {len(params)} 个参数为默认值'})
        
        flash(f'已重置 {len(params)} 个参数为默认值', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"重置参数失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '重置参数失败，请重试'}), 500
        
        flash('重置参数失败，请重试', 'error')
    
    return redirect(url_for('params.index'))

@params_bp.route('/export')
@login_required
def export():
    """导出参数配置"""
    format_type = request.args.get('format', 'json', type=str)
    
    params = Param.query.order_by(Param.category, Param.name).all()
    
    if format_type == 'csv':
        # 生成CSV格式
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['分类', '参数名', '参数值', '类型', '描述', '是否系统参数', '创建时间', '更新时间'])
        
        # 写入数据
        for param in params:
            writer.writerow([
                param.category,
                param.name,
                param.value,
                param.param_type,
                param.description,
                '是' if param.is_system else '否',
                param.created_at.strftime('%Y-%m-%d %H:%M:%S') if param.created_at else '',
                param.updated_at.strftime('%Y-%m-%d %H:%M:%S') if param.updated_at else ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=system_params.csv'}
        )
    
    else:
        # 默认JSON格式
        data = {
            'export_time': datetime.utcnow().isoformat(),
            'total_params': len(params),
            'params': [param.to_dict() for param in params]
        }
        
        return jsonify(data)

# API路由
@params_bp.route('/api/params')
@jwt_required()
def api_list():
    """获取参数列表API"""
    params = Param.query.all()
    return jsonify([param.to_dict() for param in params])

@params_bp.route('/api/params/<int:param_id>')
@jwt_required()
def api_detail(param_id):
    """获取参数详情API"""
    param = Param.query.get_or_404(param_id)
    return jsonify(param.to_dict())

@params_bp.route('/api/params/category/<category>')
@jwt_required()
def api_by_category(category):
    """根据分类获取参数API"""
    params = Param.query.filter_by(category=category).all()
    return jsonify([param.to_dict() for param in params])