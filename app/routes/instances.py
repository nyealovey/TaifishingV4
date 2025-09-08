# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 数据库实例管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.instance import Instance
from app.models.credential import Credential
from app.models.account import Account
from app import db
from app.utils.logger import log_operation
from app.utils.security import (
    sanitize_form_data, validate_required_fields, 
    validate_username, validate_db_type
)
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
        
        # 清理输入数据
        data = sanitize_form_data(data)
        
        # 输入验证
        required_fields = ['name', 'db_type', 'host', 'port']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            if request.is_json:
                return jsonify({'error': validation_error}), 400
            flash(validation_error, 'error')
            return render_template('instances/create.html', credentials=credentials)
        
        # 验证数据库类型
        db_type_error = validate_db_type(data.get('db_type'))
        if db_type_error:
            if request.is_json:
                return jsonify({'error': db_type_error}), 400
            flash(db_type_error, 'error')
            return render_template('instances/create.html', credentials=credentials)
        
        # 验证端口号
        try:
            port = int(data.get('port'))
            if port < 1 or port > 65535:
                raise ValueError("端口号必须在1-65535之间")
        except (ValueError, TypeError):
            error_msg = "端口号必须是1-65535之间的整数"
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('instances/create.html', credentials=credentials)
        
        # 验证凭据ID
        if data.get('credential_id'):
            try:
                credential_id = int(data.get('credential_id'))
                credential = Credential.query.get(credential_id)
                if not credential:
                    raise ValueError("凭据不存在")
            except (ValueError, TypeError):
                error_msg = "无效的凭据ID"
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('instances/create.html', credentials=credentials)
        
        # 验证实例名称唯一性
        existing_instance = Instance.query.filter_by(name=data.get('name')).first()
        if existing_instance:
            error_msg = '实例名称已存在'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('instances/create.html', credentials=credentials)
        
        try:
            # 创建新实例
            instance = Instance(
                name=data.get('name').strip(),
                db_type=data.get('db_type'),
                host=data.get('host').strip(),
                port=int(data.get('port')),
                credential_id=int(data.get('credential_id')) if data.get('credential_id') else None,
                description=data.get('description', '').strip()
            )
            
            # 设置其他属性
            if data.get('database_name'):
                instance.database_name = data.get('database_name').strip()
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
            logging.error(f"创建实例失败: {e}", exc_info=True)
            
            # 根据错误类型提供更具体的错误信息
            if 'UNIQUE constraint failed' in str(e):
                error_msg = '实例名称已存在，请使用其他名称'
            elif 'NOT NULL constraint failed' in str(e):
                error_msg = '必填字段不能为空'
            elif 'FOREIGN KEY constraint failed' in str(e):
                error_msg = '关联的凭据不存在'
            else:
                error_msg = f'创建实例失败: {str(e)}'
            
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            
            flash(error_msg, 'error')
    
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
    try:
        # 添加调试日志
        logging.info(f"收到测试连接请求，Content-Type: {request.content_type}")
        logging.info(f"请求数据: {request.get_data()}")
        
        # 检查Content-Type
        if not request.is_json:
            logging.warning(f"请求不是JSON格式，Content-Type: {request.content_type}")
            return jsonify({
                'success': False,
                'error': f'请求必须是JSON格式，当前Content-Type: {request.content_type}'
            }), 400
        
        data = request.get_json()
        
        # 添加调试日志
        logging.info(f"解析后的JSON数据: {data}")
        
        # 验证必需参数
        if not data:
            logging.warning("测试连接请求参数为空")
            return jsonify({
                'success': False,
                'error': '请求参数为空'
            }), 400
        
        required_fields = ['db_type', 'host', 'port', 'credential_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'缺少必需参数: {", ".join(missing_fields)}'
            }), 400
        
        # 验证端口号
        try:
            port = int(data.get('port', 0))
            if port <= 0 or port > 65535:
                return jsonify({
                    'success': False,
                    'error': '端口号必须在1-65535之间'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': '端口号必须是有效的数字'
            }), 400
        
        # 验证凭据ID
        try:
            credential_id = int(data.get('credential_id')) if data.get('credential_id') else None
            if credential_id and credential_id <= 0:
                return jsonify({
                    'success': False,
                    'error': '凭据ID必须是有效的正整数'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': '凭据ID必须是有效的数字'
            }), 400
        
        # 创建临时实例对象进行测试
        temp_instance = Instance(
            name=data.get('name', 'test'),
            db_type=data.get('db_type'),
            host=data.get('host'),
            port=port,
            credential_id=credential_id,
            description='test'
        )
        temp_instance.database_name = data.get('database_name')
        
        # 获取凭据信息
        if temp_instance.credential_id:
            credential = Credential.query.get(temp_instance.credential_id)
            if not credential:
                return jsonify({
                    'success': False,
                    'error': f'凭据ID {temp_instance.credential_id} 不存在'
                }), 400
            temp_instance.credential = credential
        else:
            return jsonify({
                'success': False,
                'error': '必须选择数据库凭据'
            }), 400
        
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

@instances_bp.route('/statistics')
@login_required
def statistics():
    """实例统计页面"""
    stats = get_instance_statistics()
    
    if request.is_json:
        return jsonify(stats)
    
    return render_template('instances/statistics.html', stats=stats)

@instances_bp.route('/api/statistics')
@login_required
def api_statistics():
    """获取实例统计API"""
    stats = get_instance_statistics()
    return jsonify(stats)

@instances_bp.route('/<int:instance_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(instance_id):
    """编辑实例"""
    instance = Instance.query.get_or_404(instance_id)
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # 清理输入数据
        data = sanitize_form_data(data)
        
        # 输入验证
        required_fields = ['name', 'db_type', 'host', 'port']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            if request.is_json:
                return jsonify({'error': validation_error}), 400
            flash(validation_error, 'error')
            return render_template('instances/edit.html', instance=instance)
        
        # 验证数据库类型
        db_type_error = validate_db_type(data.get('db_type'))
        if db_type_error:
            if request.is_json:
                return jsonify({'error': db_type_error}), 400
            flash(db_type_error, 'error')
            return render_template('instances/edit.html', instance=instance)
        
        # 验证端口号
        try:
            port = int(data.get('port'))
            if port < 1 or port > 65535:
                raise ValueError("端口号必须在1-65535之间")
        except (ValueError, TypeError):
            error_msg = "端口号必须是1-65535之间的整数"
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('instances/edit.html', instance=instance)
        
        # 验证凭据ID
        if data.get('credential_id'):
            try:
                credential_id = int(data.get('credential_id'))
                credential = Credential.query.get(credential_id)
                if not credential:
                    raise ValueError("凭据不存在")
            except (ValueError, TypeError):
                error_msg = "无效的凭据ID"
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('instances/edit.html', instance=instance)
        
        # 验证实例名称唯一性（排除当前实例）
        existing_instance = Instance.query.filter(
            Instance.name == data.get('name'),
            Instance.id != instance_id
        ).first()
        if existing_instance:
            error_msg = '实例名称已存在'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('instances/edit.html', instance=instance)
        
        try:
            # 更新实例信息
            instance.name = data.get('name', instance.name).strip()
            instance.db_type = data.get('db_type', instance.db_type)
            instance.host = data.get('host', instance.host).strip()
            instance.port = int(data.get('port', instance.port))
            instance.database_name = data.get('database_name', instance.database_name)
            if data.get('database_name'):
                instance.database_name = data.get('database_name').strip()
            instance.credential_id = int(data.get('credential_id')) if data.get('credential_id') else None
            instance.description = data.get('description', instance.description)
            if data.get('description'):
                instance.description = data.get('description').strip()
            # 正确处理布尔值
            is_active_value = data.get('is_active', instance.is_active)
            if isinstance(is_active_value, str):
                instance.is_active = is_active_value in ['on', 'true', '1', 'yes']
            else:
                instance.is_active = bool(is_active_value)
            
            db.session.commit()
            
            # 记录操作日志
            log_operation('UPDATE_INSTANCE', current_user.id, {
                'instance_id': instance.id,
                'instance_name': instance.name,
                'db_type': instance.db_type,
                'host': instance.host,
                'changes': {
                    'name': data.get('name'),
                    'db_type': data.get('db_type'),
                    'host': data.get('host'),
                    'port': data.get('port'),
                    'database_name': data.get('database_name'),
                    'credential_id': data.get('credential_id'),
                    'description': data.get('description'),
                    'is_active': data.get('is_active')
                }
            })
            
            if request.is_json:
                return jsonify({
                    'message': '实例更新成功',
                    'instance': instance.to_dict()
                })
            
            flash('实例更新成功！', 'success')
            return redirect(url_for('instances.detail', instance_id=instance_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"更新实例失败: {e}", exc_info=True)
            
            # 根据错误类型提供更具体的错误信息
            if 'UNIQUE constraint failed' in str(e):
                error_msg = '实例名称已存在，请使用其他名称'
            elif 'NOT NULL constraint failed' in str(e):
                error_msg = '必填字段不能为空'
            elif 'FOREIGN KEY constraint failed' in str(e):
                error_msg = '关联的凭据不存在'
            else:
                error_msg = f'更新实例失败: {str(e)}'
            
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            
            flash(error_msg, 'error')
    
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
        # 记录操作日志
        log_operation('DELETE_INSTANCE', current_user.id, {
            'instance_id': instance.id,
            'instance_name': instance.name,
            'db_type': instance.db_type,
            'host': instance.host
        })
        
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

@instances_bp.route('/api/test-connection', methods=['POST'])
@login_required
def api_test_instance_connection():
    """测试数据库连接API（无需CSRF）"""
    try:
        data = request.get_json()
        
        # 添加调试日志
        logging.info(f"收到API测试连接请求，Content-Type: {request.content_type}")
        logging.info(f"请求数据: {request.get_data()}")
        
        # 检查Content-Type
        if not request.is_json:
            logging.warning(f"请求不是JSON格式，Content-Type: {request.content_type}")
            return jsonify({
                'success': False,
                'error': f'请求必须是JSON格式，当前Content-Type: {request.content_type}'
            }), 400
        
        # 添加调试日志
        logging.info(f"解析后的JSON数据: {data}")
        
        # 验证必需参数
        if not data:
            logging.warning("测试连接请求参数为空")
            return jsonify({
                'success': False,
                'error': '请求参数为空'
            }), 400
        
        required_fields = ['db_type', 'host', 'port', 'credential_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'缺少必需参数: {", ".join(missing_fields)}'
            }), 400
        
        # 验证端口号
        try:
            port = int(data.get('port', 0))
            if port <= 0 or port > 65535:
                return jsonify({
                    'success': False,
                    'error': '端口号必须在1-65535之间'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': '端口号必须是有效的数字'
            }), 400
        
        # 验证凭据ID
        try:
            credential_id = int(data.get('credential_id')) if data.get('credential_id') else None
            if credential_id and credential_id <= 0:
                return jsonify({
                    'success': False,
                    'error': '凭据ID必须是有效的正整数'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': '凭据ID必须是有效的数字'
            }), 400
        
        # 创建临时实例对象进行测试
        temp_instance = Instance(
            name=data.get('name', 'test'),
            db_type=data.get('db_type'),
            host=data.get('host'),
            port=port,
            credential_id=credential_id,
            description='test'
        )
        temp_instance.database_name = data.get('database_name')
        
        # 获取凭据信息
        if temp_instance.credential_id:
            credential = Credential.query.get(temp_instance.credential_id)
            if not credential:
                return jsonify({
                    'success': False,
                    'error': f'凭据ID {temp_instance.credential_id} 不存在'
                }), 400
            temp_instance.credential = credential
        else:
            return jsonify({
                'success': False,
                'error': '必须选择数据库凭据'
            }), 400
        
        # 使用数据库服务测试连接
        db_service = DatabaseService()
        result = db_service.test_connection(temp_instance)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"测试连接失败: {e}")
        return jsonify({
            'success': False,
            'error': f'测试连接失败: {str(e)}'
        }), 500

def get_instance_statistics():
    """获取实例统计数据"""
    try:
        # 基础统计
        total_instances = Instance.query.count()
        active_instances = Instance.query.filter_by(is_active=True).count()
        inactive_instances = Instance.query.filter_by(is_active=False).count()
        
        # 数据库类型统计
        db_type_stats = db.session.query(
            Instance.db_type,
            db.func.count(Instance.id).label('count')
        ).group_by(Instance.db_type).all()
        
        # 端口统计
        port_stats = db.session.query(
            Instance.port,
            db.func.count(Instance.id).label('count')
        ).group_by(Instance.port).order_by(db.func.count(Instance.id).desc()).limit(10).all()
        
        # 数据库版本统计（这里简化处理，实际应该从数据库连接中获取版本信息）
        version_stats = db.session.query(
            Instance.db_type,
            db.func.count(Instance.id).label('count')
        ).group_by(Instance.db_type).all()
        
        # 转换为版本统计格式
        version_stats = [
            {
                'db_type': stat.db_type,
                'version': get_default_version(stat.db_type),
                'count': stat.count
            }
            for stat in version_stats
        ]
        
        # 最近连接的实例（按最后连接时间排序）
        recent_connections = Instance.query.order_by(
            Instance.last_connected.desc().nullslast()
        ).limit(10).all()
        
        # 数据库类型数量
        db_types_count = len(db_type_stats)
        
        return {
            'total_instances': total_instances,
            'active_instances': active_instances,
            'inactive_instances': inactive_instances,
            'db_types_count': db_types_count,
            'db_type_stats': [
                {
                    'db_type': stat.db_type,
                    'count': stat.count
                }
                for stat in db_type_stats
            ],
            'port_stats': [
                {
                    'port': stat.port,
                    'count': stat.count
                }
                for stat in port_stats
            ],
            'version_stats': version_stats,
            'recent_connections': recent_connections
        }
        
    except Exception as e:
        logging.error(f"获取实例统计失败: {e}", exc_info=True)
        return {
            'total_instances': 0,
            'active_instances': 0,
            'inactive_instances': 0,
            'db_types_count': 0,
            'db_type_stats': [],
            'port_stats': [],
            'version_stats': [],
            'recent_connections': []
        }

def get_default_version(db_type):
    """获取数据库类型的默认版本"""
    default_versions = {
        'postgresql': '15.x',
        'mysql': '8.0.x',
        'sqlserver': '2019',
        'oracle': '19c',
        'sqlite': '3.x'
    }
    return default_versions.get(db_type, '未知版本')

@instances_bp.route('/<int:instance_id>/accounts/<int:account_id>/permissions')
@login_required
def get_account_permissions(instance_id, account_id):
    """获取账户权限详情"""
    instance = Instance.query.get_or_404(instance_id)
    account = Account.query.filter_by(id=account_id, instance_id=instance_id).first_or_404()
    
    try:
        from app.services.database_service import DatabaseService
        db_service = DatabaseService()
        
        # 获取账户权限
        permissions = db_service.get_account_permissions(instance, account)
        
        return jsonify({
            'success': True,
            'account': {
                'id': account.id,
                'username': account.username,
                'host': account.host,
                'plugin': account.plugin
            },
            'permissions': permissions
        })
        
    except Exception as e:
        logging.error(f"获取账户权限失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取权限失败: {str(e)}'
        }), 500