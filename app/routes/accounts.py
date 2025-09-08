# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.instance import Instance
from app.models.credential import Credential
from app.models.sync_data import SyncData
from app.models.account import Account
from app import db
from app.services.database_service import DatabaseService
import logging
from datetime import datetime, timedelta

# 创建蓝图
accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/')
@login_required
def index():
    """账户统计首页"""
    # 获取统计信息
    stats = get_account_statistics()
    
    # 获取最近同步记录
    recent_syncs = SyncData.query.order_by(SyncData.sync_time.desc()).limit(10).all()
    
    # 获取实例列表
    instances = Instance.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'stats': stats,
            'recent_syncs': [sync.to_dict() for sync in recent_syncs],
            'instances': [instance.to_dict() for instance in instances]
        })
    
    return render_template('accounts/index.html', 
                         stats=stats,
                         recent_syncs=recent_syncs,
                         instances=instances)

@accounts_bp.route('/list')
@login_required
def list():
    """账户列表页面"""
    # 获取筛选参数
    search = request.args.get('search', '', type=str)
    db_type = request.args.get('db_type', '', type=str)
    account_type = request.args.get('account_type', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 构建查询
    query = db.session.query(Account).join(Instance, Account.instance_id == Instance.id)
    
    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                Account.username.contains(search),
                Account.database_name.contains(search)
            )
        )
    
    # 数据库类型筛选
    if db_type:
        query = query.filter(Instance.db_type == db_type)
    
    # 账户类型筛选
    if account_type:
        query = query.filter(Account.account_type == account_type)
    
    # 分页查询
    accounts = query.order_by(Account.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取统计信息
    stats = get_account_list_statistics()
    
    if request.is_json:
        return jsonify({
            'accounts': [account.to_dict() for account in accounts.items],
            'pagination': {
                'page': accounts.page,
                'pages': accounts.pages,
                'per_page': accounts.per_page,
                'total': accounts.total,
                'has_next': accounts.has_next,
                'has_prev': accounts.has_prev
            },
            'stats': stats
        })
    
    return render_template('accounts/list.html', 
                         accounts=accounts,
                         stats=stats,
                         search=search,
                         db_type=db_type,
                         account_type=account_type)

@accounts_bp.route('/sync/<int:instance_id>', methods=['POST'])
@login_required
def sync_accounts(instance_id):
    """同步指定实例的账户信息"""
    instance = Instance.query.get_or_404(instance_id)
    
    try:
        # 使用数据库服务同步账户
        db_service = DatabaseService()
        result = db_service.sync_accounts(instance)
        
        if result['success']:
            # 记录同步结果
            sync_record = SyncData(
                instance_id=instance_id,
                sync_type='manual',
                status='success',
                message=result.get('message', '同步成功'),
                synced_count=result.get('synced_count', 0)
            )
            db.session.add(sync_record)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': '账户同步成功',
                    'result': result
                })
            
            flash('账户同步成功！', 'success')
        else:
            # 记录同步失败
            sync_record = SyncData(
                instance_id=instance_id,
                sync_type='manual',
                status='failed',
                message=result.get('error', '同步失败'),
                synced_count=0
            )
            db.session.add(sync_record)
            db.session.commit()
            
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
    
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/sync-all', methods=['POST'])
@login_required
def sync_all_accounts():
    """同步所有实例的账户信息"""
    instances = Instance.query.filter_by(is_active=True).all()
    
    if not instances:
        if request.is_json:
            return jsonify({'error': '没有可用的实例'}), 400
        flash('没有可用的实例', 'error')
        return redirect(url_for('accounts.index'))
    
    success_count = 0
    failed_count = 0
    results = []
    
    for instance in instances:
        try:
            db_service = DatabaseService()
            result = db_service.sync_accounts(instance)
            
            if result['success']:
                success_count += 1
                # 记录同步成功
                sync_record = SyncData(
                    instance_id=instance.id,
                    sync_type='batch',
                    status='success',
                    message=result.get('message', '同步成功'),
                    synced_count=result.get('synced_count', 0)
                )
                db.session.add(sync_record)
            else:
                failed_count += 1
                # 记录同步失败
                sync_record = SyncData(
                    instance_id=instance.id,
                    sync_type='batch',
                    status='failed',
                    message=result.get('error', '同步失败'),
                    synced_count=0
                )
                db.session.add(sync_record)
            
            results.append({
                'instance_name': instance.name,
                'success': result['success'],
                'message': result.get('message', result.get('error', '未知错误'))
            })
            
        except Exception as e:
            failed_count += 1
            logging.error(f"同步实例 {instance.name} 失败: {e}")
            results.append({
                'instance_name': instance.name,
                'success': False,
                'message': f'同步失败: {str(e)}'
            })
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'message': f'批量同步完成，成功: {success_count}, 失败: {failed_count}',
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        })
    
    flash(f'批量同步完成，成功: {success_count}, 失败: {failed_count}', 'info')
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/history')
@login_required
def history():
    """同步历史记录"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    instance_id = request.args.get('instance_id', type=int)
    status = request.args.get('status', '', type=str)
    
    # 构建查询
    query = SyncData.query
    
    if instance_id:
        query = query.filter(SyncData.instance_id == instance_id)
    
    if status:
        query = query.filter(SyncData.status == status)
    
    # 分页查询
    sync_records = query.order_by(SyncData.sync_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取实例列表用于筛选
    instances = Instance.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'sync_records': [record.to_dict() for record in sync_records.items],
            'pagination': {
                'page': sync_records.page,
                'pages': sync_records.pages,
                'per_page': sync_records.per_page,
                'total': sync_records.total,
                'has_next': sync_records.has_next,
                'has_prev': sync_records.has_prev
            },
            'instances': [instance.to_dict() for instance in instances]
        })
    
    return render_template('accounts/history.html', 
                         sync_records=sync_records,
                         instances=instances,
                         instance_id=instance_id,
                         status=status)

@accounts_bp.route('/export')
@login_required
def export():
    """导出账户数据"""
    format_type = request.args.get('format', 'json', type=str)
    instance_id = request.args.get('instance_id', type=int)
    
    # 构建查询
    query = SyncData.query
    if instance_id:
        query = query.filter(SyncData.instance_id == instance_id)
    
    sync_records = query.order_by(SyncData.sync_time.desc()).all()
    
    if format_type == 'csv':
        # 生成CSV格式
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['实例名称', '同步时间', '同步类型', '状态', '同步数量', '消息'])
        
        # 写入数据
        for record in sync_records:
            instance_name = record.instance.name if record.instance else '未知实例'
            writer.writerow([
                instance_name,
                record.sync_time.strftime('%Y-%m-%d %H:%M:%S'),
                record.sync_type,
                record.status,
                record.synced_count,
                record.message
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=account_sync_history.csv'}
        )
    
    else:
        # 默认JSON格式
        data = {
            'export_time': datetime.utcnow().isoformat(),
            'total_records': len(sync_records),
            'records': [record.to_dict() for record in sync_records]
        }
        
        return jsonify(data)

def get_account_statistics():
    """获取账户统计信息"""
    try:
        # 总实例数
        total_instances = Instance.query.filter_by(is_active=True).count()
        
        # 总同步次数
        total_syncs = SyncData.query.count()
        
        # 成功同步次数
        successful_syncs = SyncData.query.filter_by(status='success').count()
        
        # 失败同步次数
        failed_syncs = SyncData.query.filter_by(status='failed').count()
        
        # 今日同步次数
        today = datetime.utcnow().date()
        today_syncs = SyncData.query.filter(
            db.func.date(SyncData.sync_time) == today
        ).count()
        
        # 最近7天同步趋势
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_syncs = SyncData.query.filter(
            SyncData.sync_time >= week_ago
        ).count()
        
        # 各实例同步统计
        instance_stats = db.session.query(
            Instance.name,
            db.func.count(SyncData.id).label('sync_count'),
            db.func.sum(db.case((SyncData.status == 'success', 1), else_=0)).label('success_count')
        ).outerjoin(SyncData).group_by(Instance.id, Instance.name).all()
        
        return {
            'total_instances': total_instances,
            'total_syncs': total_syncs,
            'successful_syncs': successful_syncs,
            'failed_syncs': failed_syncs,
            'success_rate': round((successful_syncs / total_syncs * 100) if total_syncs > 0 else 0, 2),
            'today_syncs': today_syncs,
            'week_syncs': week_syncs,
            'instance_stats': [
                {
                    'name': stat.name,
                    'sync_count': stat.sync_count or 0,
                    'success_count': stat.success_count or 0,
                    'success_rate': round((stat.success_count / stat.sync_count * 100) if stat.sync_count > 0 else 0, 2)
                }
                for stat in instance_stats
            ]
        }
    except Exception as e:
        logging.error(f"获取统计信息失败: {e}")
        return {
            'total_instances': 0,
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'success_rate': 0,
            'today_syncs': 0,
            'week_syncs': 0,
            'instance_stats': []
        }

def get_account_list_statistics():
    """获取账户列表统计信息"""
    try:
        # 总账户数
        total_accounts = Account.query.count()
        
        # 高权限账户数（暂时占位，后续定义高权限逻辑）
        high_privilege_accounts = 0  # TODO: 实现高权限账户识别逻辑
        
        # 数据库类型数量
        db_types_count = db.session.query(Instance.db_type).distinct().count()
        
        # 实例数量
        instances_count = Instance.query.filter_by(is_active=True).count()
        
        return {
            'total_accounts': total_accounts,
            'high_privilege_accounts': high_privilege_accounts,
            'db_types_count': db_types_count,
            'instances_count': instances_count
        }
    except Exception as e:
        logging.error(f"获取账户列表统计失败: {e}")
        return {
            'total_accounts': 0,
            'high_privilege_accounts': 0,
            'db_types_count': 0,
            'instances_count': 0
        }

# API路由
@accounts_bp.route('/api/statistics')
@jwt_required()
def api_statistics():
    """获取统计信息API"""
    stats = get_account_statistics()
    return jsonify(stats)

@accounts_bp.route('/<int:account_id>/permissions')
@login_required
def get_account_permissions(account_id):
    """获取账户权限详情"""
    account = Account.query.get_or_404(account_id)
    instance = Instance.query.get_or_404(account.instance_id)
    
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

@accounts_bp.route('/api/sync/<int:instance_id>')
@jwt_required()
def api_sync_accounts(instance_id):
    """同步账户API"""
    instance = Instance.query.get_or_404(instance_id)
    
    try:
        db_service = DatabaseService()
        result = db_service.sync_accounts(instance)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500