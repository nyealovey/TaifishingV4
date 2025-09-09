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
from app.utils.timezone import now

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
@accounts_bp.route('/list/<db_type>')
@login_required
def list(db_type=None):
    """账户列表页面 - 支持按数据库类型分页"""
    # 获取筛选参数
    search = request.args.get('search', '', type=str)
    is_locked = request.args.get('is_locked', '', type=str)
    plugin = request.args.get('plugin', '', type=str)
    instance_id = request.args.get('instance_id', '', type=str)
    filter_db_type = request.args.get('db_type', '', type=str)  # 新增数据库类型筛选参数
    environment = request.args.get('environment', '', type=str)  # 新增环境筛选参数
    classification = request.args.get('classification', '', type=str)  # 新增分类筛选参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 构建查询 - 包含分类信息
    from app.models.account_classification import AccountClassificationAssignment, AccountClassification
    query = db.session.query(Account).join(Instance, Account.instance_id == Instance.id)
    
    # 数据库类型筛选 - 优先使用URL参数，其次使用筛选参数
    if db_type:
        query = query.filter(Instance.db_type == db_type)
    elif filter_db_type:
        query = query.filter(Instance.db_type == filter_db_type)
    
    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                Account.username.contains(search),
                Account.database_name.contains(search),
                Instance.name.contains(search),
                Instance.host.contains(search)
            )
        )
    
    
    # 锁定状态筛选
    if is_locked:
        if is_locked == 'locked':
            query = query.filter(Account.is_locked == True)
        elif is_locked == 'unlocked':
            query = query.filter(Account.is_locked == False)
    
    # 插件/类型筛选 - 同时搜索plugin和account_type字段
    if plugin:
        query = query.filter(
            db.or_(
                Account.plugin.contains(plugin),
                Account.account_type.contains(plugin)
            )
        )
    
    # 实例筛选
    if instance_id:
        query = query.filter(Account.instance_id == int(instance_id))
    
    # 环境筛选
    if environment:
        query = query.filter(Instance.environment == environment)
    
    # 分类筛选
    if classification:
        if classification == 'unclassified':
            # 未分类：没有活跃的分类分配
            subquery = db.session.query(AccountClassificationAssignment.account_id).filter(
                AccountClassificationAssignment.is_active == True
            ).subquery()
            query = query.filter(~Account.id.in_(subquery))
        else:
            # 具体分类ID
            try:
                classification_id = int(classification)
                query = query.join(AccountClassificationAssignment, Account.id == AccountClassificationAssignment.account_id).filter(
                    AccountClassificationAssignment.classification_id == classification_id,
                    AccountClassificationAssignment.is_active == True
                )
            except ValueError:
                pass  # 忽略无效的分类ID
    
    # 分页查询
    accounts = query.order_by(Account.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取账户分类信息（支持多个分类）
    account_ids = [account.id for account in accounts.items]
    classifications = {}
    if account_ids:
        assignments = db.session.query(AccountClassificationAssignment, AccountClassification).join(
            AccountClassification, AccountClassificationAssignment.classification_id == AccountClassification.id
        ).filter(
            AccountClassificationAssignment.account_id.in_(account_ids),
            AccountClassificationAssignment.is_active == True
        ).all()
        
        for assignment, classification in assignments:
            if assignment.account_id not in classifications:
                classifications[assignment.account_id] = []
            classifications[assignment.account_id].append({
                'id': classification.id,
                'name': classification.name,
                'risk_level': classification.risk_level,
                'color': classification.color
            })
    
    # 获取统计信息
    stats = get_account_list_statistics()
    
    # 获取筛选选项
    filter_options = get_filter_options()
    
    # 获取实例列表用于筛选
    instances = Instance.query.filter_by(is_active=True).all()
    
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
            'stats': stats,
            'filter_options': filter_options
        })
    
    return render_template('accounts/list.html', 
                         accounts=accounts,
                         stats=stats,
                         filter_options=filter_options,
                         instances=instances,
                         classifications=classifications,  # 传递分类信息
                         current_db_type=db_type,
                         search=search,
                         is_locked=is_locked,
                         plugin=plugin,
                         instance_id=instance_id,
                         db_type=filter_db_type,
                         environment=environment,  # 传递环境筛选参数
                         classification=classification)  # 传递分类筛选参数

@accounts_bp.route('/sync/<int:instance_id>', methods=['POST'])
@login_required
def sync_accounts(instance_id):
    """同步指定实例的账户信息"""
    instance = Instance.query.get_or_404(instance_id)
    
    try:
        # 使用统一的账户同步服务
        from app.services.account_sync_service import account_sync_service
        result = account_sync_service.sync_accounts(instance, sync_type='manual')
        
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
    
    # 记录批量同步开始日志
    from app.utils.logger import log_operation
    log_operation('BATCH_SYNC_ACCOUNTS_START', current_user.id, {
        'total_instances': len(instances),
        'instance_names': [instance.name for instance in instances]
    })
    
    success_count = 0
    failed_count = 0
    results = []
    
    for instance in instances:
        try:
            # 使用统一的账户同步服务
            from app.services.account_sync_service import account_sync_service
            result = account_sync_service.sync_accounts(instance, sync_type='batch')
            
            if result['success']:
                # 同步成功后，自动清理多余账户
                cleanup_result = account_sync_service.cleanup_orphaned_accounts(instance)
                if cleanup_result.get('success', False):
                    # 将清理结果合并到同步结果中
                    result['cleanup_removed_count'] = cleanup_result.get('removed_count', 0)
                    result['cleanup_message'] = cleanup_result.get('message', '')
                
                success_count += 1
                # 记录同步成功
                sync_record = SyncData(
                    instance_id=instance.id,
                    sync_type='batch',
                    status='success',
                    message=result.get('message', '同步成功'),
                    synced_count=result.get('synced_count', 0),
                    added_count=result.get('added_count', 0),
                    removed_count=result.get('removed_count', 0),
                    modified_count=result.get('modified_count', 0)
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
                'message': result.get('message', result.get('error', '未知错误')),
                'synced_count': result.get('synced_count', 0)
            })
            
        except Exception as e:
            failed_count += 1
            logging.error(f"同步实例 {instance.name} 失败: {e}")
            results.append({
                'instance_name': instance.name,
                'success': False,
                'message': f'同步失败: {str(e)}',
                'synced_count': 0
            })
    
    db.session.commit()
    
    # 记录批量同步完成日志
    log_operation('BATCH_SYNC_ACCOUNTS_COMPLETE', current_user.id, {
        'total_instances': len(instances),
        'success_count': success_count,
        'failed_count': failed_count,
        'results': results
    })
    
    # 计算总同步账户数
    total_accounts = sum(result.get('synced_count', 0) for result in results)
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': f'批量同步完成，成功: {success_count}, 失败: {failed_count}',
            'report': {
                'total_instances': len(instances),
                'success_count': success_count,
                'failed_count': failed_count,
                'total_accounts': total_accounts,
                'results': results
            }
        })
    
    flash(f'批量同步完成，成功: {success_count}, 失败: {failed_count}', 'info')
    return redirect(url_for('accounts.index'))

@accounts_bp.route('/cleanup-orphaned', methods=['POST'])
@login_required
def cleanup_orphaned_accounts():
    """清理多余的账户（服务器上不存在的本地账户）"""
    try:
        from app.services.account_sync_service import account_sync_service
        from app.utils.logger import log_operation
        
        # 记录清理开始日志
        log_operation('CLEANUP_ORPHANED_ACCOUNTS_START', current_user.id, {})
        
        instances = Instance.query.filter_by(is_active=True).all()
        if not instances:
            if request.is_json:
                return jsonify({'error': '没有可用的实例'}), 400
            flash('没有可用的实例', 'error')
            return redirect(url_for('accounts.list'))
        
        total_removed = 0
        results = []
        
        for instance in instances:
            try:
                # 获取数据库连接
                conn = account_sync_service._get_connection(instance)
                if not conn:
                    results.append({
                        'instance_name': instance.name,
                        'success': False,
                        'message': '无法获取数据库连接',
                        'removed_count': 0
                    })
                    continue
                
                # 获取服务器上的账户列表
                if instance.db_type == 'mysql':
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT User as username, Host as host
                        FROM mysql.user
                        WHERE User NOT LIKE 'mysql.%'
                        ORDER BY User, Host
                    """)
                    server_accounts = set((row[0], row[1]) for row in cursor.fetchall())
                    cursor.close()
                elif instance.db_type == 'postgresql':
                    cursor = conn.cursor()
                    cursor.execute("SELECT usename as username FROM pg_user")
                    server_accounts = set((row[0], '') for row in cursor.fetchall())
                    cursor.close()
                elif instance.db_type == 'sqlserver':
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT name as username
                        FROM sys.server_principals
                        WHERE type IN ('S', 'U', 'G')
                        AND name NOT LIKE '##%'
                        ORDER BY name
                    """)
                    server_accounts = set((row[0], '') for row in cursor.fetchall())
                    cursor.close()
                else:
                    # 其他数据库类型暂不支持
                    results.append({
                        'instance_name': instance.name,
                        'success': False,
                        'message': f'不支持的数据库类型: {instance.db_type}',
                        'removed_count': 0
                    })
                    continue
                
                # 获取本地账户
                local_accounts = Account.query.filter_by(instance_id=instance.id).all()
                removed_accounts = []
                
                for local_account in local_accounts:
                    # 根据数据库类型检查账户是否存在
                    if instance.db_type == 'mysql':
                        account_key = (local_account.username, local_account.host)
                    else:  # postgresql 或 sqlserver
                        account_key = (local_account.username, '')
                    
                    if account_key not in server_accounts:
                        removed_accounts.append({
                            'username': local_account.username,
                            'host': local_account.host,
                            'database_name': local_account.database_name,
                            'account_type': local_account.account_type
                        })
                        db.session.delete(local_account)
                
                db.session.commit()
                conn.close()
                
                total_removed += len(removed_accounts)
                results.append({
                    'instance_name': instance.name,
                    'success': True,
                    'message': f'清理完成，删除了 {len(removed_accounts)} 个多余账户',
                    'removed_count': len(removed_accounts),
                    'removed_accounts': removed_accounts
                })
                
            except Exception as e:
                logging.error(f"清理实例 {instance.name} 的多余账户失败: {e}")
                results.append({
                    'instance_name': instance.name,
                    'success': False,
                    'message': f'清理失败: {str(e)}',
                    'removed_count': 0
                })
        
        # 记录清理完成日志
        log_operation('CLEANUP_ORPHANED_ACCOUNTS_COMPLETE', current_user.id, {
            'total_removed': total_removed,
            'results': results
        })
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': f'清理完成，总共删除了 {total_removed} 个多余账户',
                'total_removed': total_removed,
                'results': results
            })
        
        flash(f'清理完成，总共删除了 {total_removed} 个多余账户', 'success')
        return redirect(url_for('accounts.list'))
        
    except Exception as e:
        logging.error(f"清理多余账户失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '清理多余账户失败，请重试'}), 500
        
        flash('清理多余账户失败，请重试', 'error')
        return redirect(url_for('accounts.list'))

@accounts_bp.route('/sync-history')
@login_required
def sync_history():
    """获取同步历史记录API"""
    try:
        from sqlalchemy import desc
        from app.models.sync_data import SyncData
        from collections import defaultdict
        
        # 查询所有同步记录（包括批量同步和任务同步）
        sync_records = SyncData.query.filter(
            SyncData.sync_type.in_(['batch', 'task'])
        ).order_by(desc(SyncData.sync_time)).all()
        
        # 按同步批次分组（相同时间的同步记录为一组）
        grouped = defaultdict(lambda: {
            'total_instances': 0, 
            'success_count': 0, 
            'failed_count': 0, 
            'total_accounts': 0, 
            'added_count': 0,
            'removed_count': 0,
            'modified_count': 0,
            'created_at': None,
            'sync_records': [],
            'sync_types': [],  # 记录包含的同步类型，使用list而不是set
            'sync_type_display': ''  # 显示用的同步类型文本
        })
        
        for record in sync_records:
            # 使用分钟级精度作为分组键，相同分钟的同步记录为一组
            time_key = record.sync_time.strftime('%Y-%m-%d %H:%M')
            grouped[time_key]['total_instances'] += 1
            if record.status == 'success':
                grouped[time_key]['success_count'] += 1
            else:
                grouped[time_key]['failed_count'] += 1
            grouped[time_key]['total_accounts'] += record.synced_count or 0
            grouped[time_key]['added_count'] += record.added_count or 0
            grouped[time_key]['removed_count'] += record.removed_count or 0
            grouped[time_key]['modified_count'] += record.modified_count or 0
            grouped[time_key]['sync_records'].append(record)
            if record.sync_type not in grouped[time_key]['sync_types']:
                grouped[time_key]['sync_types'].append(record.sync_type)  # 记录同步类型
            if not grouped[time_key]['created_at'] or record.sync_time > grouped[time_key]['created_at']:
                grouped[time_key]['created_at'] = record.sync_time
        
        # 转换为列表并排序
        history = []
        for time_key, data in sorted(grouped.items(), key=lambda x: x[1]['created_at'], reverse=True)[:20]:
            # 使用最新记录的时间作为显示时间
            latest_time = max(record.sync_time for record in data['sync_records'])
            # 生成正确的ID格式：YYYYMMDDHHMM
            sync_id = latest_time.strftime('%Y%m%d%H%M')
            
            # 确定同步类型显示文本
            sync_types = data['sync_types']
            if 'task' in sync_types and 'batch' in sync_types:
                sync_type_display = '定时任务 + 手动执行'
            elif 'task' in sync_types:
                sync_type_display = '定时任务'
            elif 'batch' in sync_types:
                sync_type_display = '手动执行'
            else:
                sync_type_display = '未知'
            
            # 使用东八区时间格式化
            from app.utils.timezone import format_china_time
            china_time_str = format_china_time(latest_time, '%Y-%m-%d %H:%M:%S')
            
            history.append({
                'id': sync_id,
                'created_at': china_time_str,
                'total_instances': data['total_instances'],
                'success_count': data['success_count'],
                'failed_count': data['failed_count'],
                'total_accounts': data['total_accounts'],
                'added_count': data['added_count'],
                'removed_count': data['removed_count'],
                'modified_count': data['modified_count'],
                'sync_type': sync_type_display,
                'sync_types': sync_types  # 已经是list，不需要转换
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logging.error(f"获取同步历史失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取同步历史失败: {str(e)}'
        }), 500

@accounts_bp.route('/sync-details/<sync_id>')
@login_required
def sync_details(sync_id):
    """获取同步详情API"""
    try:
        from app.models.sync_data import SyncData
        from datetime import datetime
        from sqlalchemy import func
        
        # 解析同步ID（日期时间格式：YYYYMMDDHHMM）
        sync_datetime = datetime.strptime(sync_id, '%Y%m%d%H%M')
        
        # 查询该时间点前后5分钟内的所有同步记录（考虑到批量同步可能跨越几分钟）
        start_time = sync_datetime - timedelta(minutes=5)
        end_time = sync_datetime + timedelta(minutes=5)
        
        sync_records = SyncData.query.filter(
            SyncData.sync_type.in_(['batch', 'task']),
            SyncData.sync_time >= start_time,
            SyncData.sync_time <= end_time
        ).all()
        
        details = []
        for record in sync_records:
            instance = Instance.query.get(record.instance_id)
            
            # 获取账户变化详情
            account_changes = []
            if hasattr(record, 'account_changes'):
                for change in record.account_changes:
                    account_changes.append({
                        'change_type': change.change_type,
                        'account_data': change.account_data
                    })
            
            details.append({
                'instance_name': instance.name if instance else '未知实例',
                'success': record.status == 'success',
                'message': record.message,
                'synced_count': record.synced_count or 0,
                'added_count': record.added_count or 0,
                'removed_count': record.removed_count or 0,
                'modified_count': record.modified_count or 0,
                'account_changes': account_changes
            })
        
        return jsonify({
            'success': True,
            'details': details
        })
        
    except Exception as e:
        logging.error(f"获取同步详情失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取同步详情失败: {str(e)}'
        }), 500

@accounts_bp.route('/sync-report')
@login_required
def sync_report():
    """同步报告页面"""
    return render_template('accounts/sync_report.html')

@accounts_bp.route('/sync-statistics')
@login_required
def sync_statistics():
    """获取同步统计信息API"""
    try:
        from sqlalchemy import desc, func
        from datetime import datetime, timedelta
        
        # 获取最近7天的数据
        week_ago = now() - timedelta(days=7)
        
        # 总同步次数
        total_syncs = SyncData.query.filter(
            SyncData.sync_time >= week_ago
        ).count()
        
        # 成功和失败次数
        success_syncs = SyncData.query.filter(
            SyncData.sync_time >= week_ago,
            SyncData.status == 'success'
        ).count()
        
        failed_syncs = SyncData.query.filter(
            SyncData.sync_time >= week_ago,
            SyncData.status == 'failed'
        ).count()
        
        # 总同步账户数
        total_accounts = db.session.query(func.sum(SyncData.synced_count)).filter(
            SyncData.sync_time >= week_ago
        ).scalar() or 0
        
        # 成功率
        success_rate = round((success_syncs / total_syncs * 100) if total_syncs > 0 else 0, 1)
        
        # 最近同步时间
        last_sync = SyncData.query.filter(
            SyncData.sync_time >= week_ago
        ).order_by(desc(SyncData.sync_time)).first()
        
        # 使用东八区时间格式化
        from app.utils.timezone import format_china_time
        last_sync_time = format_china_time(last_sync.sync_time, '%Y-%m-%d %H:%M:%S') if last_sync else None
        
        # 按日期统计趋势数据
        trend_data = []
        for i in range(7):
            date = (now() - timedelta(days=i)).date()
            day_syncs = SyncData.query.filter(
                func.date(SyncData.sync_time) == date
            ).all()
            
            day_success = sum(1 for sync in day_syncs if sync.status == 'success')
            day_failed = sum(1 for sync in day_syncs if sync.status == 'failed')
            day_accounts = sum(sync.synced_count or 0 for sync in day_syncs)
            
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'success': day_success,
                'failed': day_failed,
                'accounts': day_accounts
            })
        
        # 数据库类型分布
        db_type_stats = db.session.query(
            Instance.db_type,
            func.count(SyncData.id).label('count')
        ).join(SyncData, Instance.id == SyncData.instance_id).filter(
            SyncData.sync_time >= week_ago
        ).group_by(Instance.db_type).all()
        
        db_type_distribution = {
            stat.db_type: stat.count for stat in db_type_stats
        }
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_syncs': total_syncs,
                'success_syncs': success_syncs,
                'failed_syncs': failed_syncs,
                'total_accounts': total_accounts,
                'success_rate': success_rate,
                'last_sync_time': last_sync_time
            },
            'trend_data': trend_data,
            'db_type_distribution': db_type_distribution
        })
        
    except Exception as e:
        logging.error(f"获取同步统计失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取统计信息失败: {str(e)}'
        }), 500

@accounts_bp.route('/account-statistics')
@login_required
def account_statistics():
    """获取账户统计信息API"""
    try:
        from sqlalchemy import func
        from app.models import Instance
        
        # 获取查询参数
        db_type = request.args.get('db_type')
        
        # 构建基础查询
        base_query = Account.query
        instance_query = Instance.query.filter_by(is_active=True)
        
        # 如果指定了数据库类型，添加筛选条件
        if db_type:
            base_query = base_query.join(Instance).filter(Instance.db_type == db_type)
            instance_query = instance_query.filter(Instance.db_type == db_type)
        
        # 总账户数
        total_accounts = base_query.count()
        
        # 正常账户数（未锁定且未过期）
        active_accounts = base_query.filter(
            Account.is_locked == False,
            Account.password_expired == False
        ).count()
        
        # 锁定账户数
        locked_accounts = base_query.filter(
            Account.is_locked == True
        ).count()
        
        # 密码过期账户数
        expired_accounts = base_query.filter(
            Account.password_expired == True
        ).count()
        
        # 总实例数
        total_instances = instance_query.count()
        
        # 按数据库类型统计账户数
        db_type_stats = db.session.query(
            Instance.db_type,
            func.count(Account.id).label('count')
        ).join(Account, Instance.id == Account.instance_id).group_by(Instance.db_type).all()
        
        db_type_distribution = {
            stat.db_type: stat.count for stat in db_type_stats
        }
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_accounts': total_accounts,
                'active_accounts': active_accounts,
                'locked_accounts': locked_accounts,
                'expired_accounts': expired_accounts,
                'total_instances': total_instances
            },
            'db_type_distribution': db_type_distribution,
            'filter': {
                'db_type': db_type
            }
        })
        
    except Exception as e:
        logging.error(f"获取账户统计失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取统计信息失败: {str(e)}'
        }), 500

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
            'export_time': now().isoformat(),
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
        today = now().date()
        today_syncs = SyncData.query.filter(
            db.func.date(SyncData.sync_time) == today
        ).count()
        
        # 最近7天同步趋势
        week_ago = now() - timedelta(days=7)
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

def get_filter_options():
    """获取筛选选项"""
    try:
        # 获取数据库类型选项
        db_types = db.session.query(Instance.db_type).distinct().all()
        db_type_options = [{'value': dt[0], 'label': dt[0].upper()} for dt in db_types]
        
        # 获取环境选项
        environments = db.session.query(Instance.environment).distinct().all()
        environment_options = []
        for env in environments:
            if env[0]:  # 确保不为空
                env_label = {
                    'production': '生产环境',
                    'development': '开发环境', 
                    'testing': '测试环境'
                }.get(env[0], env[0])
                environment_options.append({'value': env[0], 'label': env_label})
        
        # 获取插件/类型选项 - 分别处理不同数据库类型的字段
        plugin_options = []
        
        # 获取MySQL的plugin字段选项（认证插件）
        mysql_plugins = db.session.query(Account.plugin).join(Instance, Account.instance_id == Instance.id).filter(
            Instance.db_type == 'mysql',
            Account.plugin.isnot(None),
            Account.plugin != ''
        ).distinct().all()
        
        for p in mysql_plugins:
            if p[0] and p[0] not in ['sqlserver']:  # 排除数据库类型
                plugin_options.append({'value': p[0], 'label': f'MySQL认证插件: {p[0]}'})
        
        # 获取MySQL的account_type字段选项（账户类型）
        mysql_types = db.session.query(Account.account_type).join(Instance, Account.instance_id == Instance.id).filter(
            Instance.db_type == 'mysql',
            Account.account_type.isnot(None),
            Account.account_type != ''
        ).distinct().all()
        
        for at in mysql_types:
            if at[0]:
                plugin_options.append({'value': at[0], 'label': f'MySQL账户类型: {at[0]}'})
        
        # 获取SQL Server的account_type字段选项（账户类型）
        sqlserver_types = db.session.query(Account.account_type).join(Instance, Account.instance_id == Instance.id).filter(
            Instance.db_type == 'sqlserver',
            Account.account_type.isnot(None),
            Account.account_type != ''
        ).distinct().all()
        
        for at in sqlserver_types:
            if at[0]:
                plugin_options.append({'value': at[0], 'label': f'SQL Server账户类型: {at[0]}'})
        
        # 获取PostgreSQL的plugin字段选项
        postgres_plugins = db.session.query(Account.plugin).join(Instance, Account.instance_id == Instance.id).filter(
            Instance.db_type == 'postgresql',
            Account.plugin.isnot(None),
            Account.plugin != ''
        ).distinct().all()
        
        for p in postgres_plugins:
            if p[0] and p[0] not in ['sqlserver']:  # 排除数据库类型
                plugin_options.append({'value': p[0], 'label': f'PostgreSQL认证插件: {p[0]}'})
        
        # 获取PostgreSQL的account_type字段选项
        postgres_types = db.session.query(Account.account_type).join(Instance, Account.instance_id == Instance.id).filter(
            Instance.db_type == 'postgresql',
            Account.account_type.isnot(None),
            Account.account_type != ''
        ).distinct().all()
        
        for at in postgres_types:
            if at[0]:
                plugin_options.append({'value': at[0], 'label': f'PostgreSQL账户类型: {at[0]}'})
        
        # 获取实例选项
        instances = Instance.query.filter_by(is_active=True).all()
        instance_options = [{'value': str(i.id), 'label': i.name} for i in instances]
        
        # 获取分类选项
        from app.models.account_classification import AccountClassification
        classifications = AccountClassification.query.filter_by(is_active=True).order_by(AccountClassification.priority.desc(), AccountClassification.name).all()
        
        # 构建分类筛选选项，包括特殊筛选条件
        classification_options = [
            {'value': 'unclassified', 'name': '未分类', 'type': 'special'},
            {'value': '', 'name': '───────────────', 'type': 'separator', 'disabled': True}
        ]
        
        # 添加数据库中的分类
        for c in classifications:
            classification_options.append({
                'value': str(c.id), 
                'name': f'{c.name}（分类）', 
                'type': 'classification',
                'risk_level': c.risk_level
            })
        
        return {
            'db_types': db_type_options,
            'environments': environment_options,
            'plugins': plugin_options,
            'instances': instance_options,
            'classifications': classification_options
        }
    except Exception as e:
        logging.error(f"获取筛选选项失败: {e}")
        return {
            'db_types': [],
            'environments': [],
            'plugins': [],
            'instances': [],
            'classifications': []
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
                'plugin': account.plugin,
                'instance': {
                    'db_type': instance.db_type,
                    'name': instance.name
                }
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
        from app.services.account_sync_service import account_sync_service
        result = account_sync_service.sync_accounts(instance, sync_type='manual')
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500