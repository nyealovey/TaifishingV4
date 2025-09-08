# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 定时任务管理路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.task import Task
from app.services.task_executor import TaskExecutor
from app.models.instance import Instance
from app import db, celery
from app.services.database_service import DatabaseService
import logging
from datetime import datetime, timedelta

# 创建蓝图
tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/')
@login_required
def index():
    """任务管理首页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '', type=str)
    db_type = request.args.get('db_type', '', type=str)
    task_type = request.args.get('task_type', '', type=str)
    
    # 构建查询
    query = Task.query
    
    if status:
        if status == 'active':
            query = query.filter(Task.is_active == True)
        elif status == 'inactive':
            query = query.filter(Task.is_active == False)
    
    if db_type:
        query = query.filter(Task.db_type == db_type)
    
    if task_type:
        query = query.filter(Task.task_type == task_type)
    
    # 分页查询
    tasks = query.order_by(Task.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取实例列表
    instances = Instance.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'tasks': [task.to_dict() for task in tasks.items],
            'pagination': {
                'page': tasks.page,
                'pages': tasks.pages,
                'per_page': tasks.per_page,
                'total': tasks.total,
                'has_next': tasks.has_next,
                'has_prev': tasks.has_prev
            },
            'instances': [instance.to_dict() for instance in instances]
        })
    
    return render_template('tasks/index.html', 
                         tasks=tasks,
                         instances=instances,
                         status=status,
                         db_type=db_type,
                         task_type=task_type)

@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建任务"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 解析配置参数
            config = {}
            if data.get('config'):
                import json
                try:
                    config = json.loads(data.get('config'))
                except json.JSONDecodeError:
                    config = {}
            
            # 创建新任务
            task = Task(
                name=data.get('name'),
                task_type=data.get('task_type'),
                db_type=data.get('db_type'),
                schedule=data.get('schedule'),
                description=data.get('description', ''),
                python_code=data.get('python_code'),
                config=config,
                is_active=data.get('is_active', True),
                is_builtin=data.get('is_builtin', False)
            )
            
            db.session.add(task)
            db.session.commit()
            
            # 如果任务启用，则启动定时任务
            if task.is_active:
                start_scheduled_task(task)
            
            if request.is_json:
                return jsonify({
                    'message': '任务创建成功',
                    'task': task.to_dict()
                }), 201
            
            flash('任务创建成功！', 'success')
            return redirect(url_for('tasks.index'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"创建任务失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '创建任务失败，请重试'}), 500
            
            flash('创建任务失败，请重试', 'error')
    
    # GET请求，显示创建表单
    instances = Instance.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'instances': [instance.to_dict() for instance in instances]
        })
    
    return render_template('tasks/create.html', instances=instances)

@tasks_bp.route('/create-quick', methods=['POST'])
@login_required
def create_quick():
    """快速创建内置任务"""
    data = request.get_json()
    task_type = data.get('task_type')
    
    if not task_type:
        return jsonify({'error': '任务类型不能为空'}), 400
    
    # 支持的数据库类型
    db_types = ['postgresql', 'mysql', 'sqlserver', 'oracle']
    created_count = 0
    skipped_count = 0
    
    for db_type in db_types:
        try:
            # 根据任务类型和数据库类型生成任务名称
            task_name = f'{db_type.upper()}{task_type.replace("_", " ").title()}'
            
            # 检查任务是否已存在
            existing_task = Task.query.filter_by(
                name=task_name,
                task_type=task_type,
                db_type=db_type
            ).first()
            
            if existing_task:
                skipped_count += 1
                continue
            
            # 从内置任务模板中获取配置
            from app.templates.tasks.builtin_tasks import BUILTIN_TASKS
            
            # 查找对应的内置任务配置
            task_config = None
            for config in BUILTIN_TASKS:
                if config['task_type'] == task_type and config['db_type'] == db_type:
                    task_config = config
                    break
            
            if not task_config:
                continue
            
            # 创建新任务
            task = Task(
                name=task_name,
                task_type=task_type,
                db_type=db_type,
                description=task_config['description'],
                python_code=task_config['python_code'],
                config=task_config['config'],
                schedule=task_config['schedule'],
                is_builtin=True,
                is_active=True
            )
            
            db.session.add(task)
            created_count += 1
            
        except Exception as e:
            logging.error(f"创建快速任务失败 {db_type}-{task_type}: {e}")
    
    try:
        db.session.commit()
        return jsonify({
            'message': f'快速创建完成，新增: {created_count}, 跳过: {skipped_count}',
            'created_count': created_count,
            'skipped_count': skipped_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建任务失败: {str(e)}'}), 500

@tasks_bp.route('/batch-toggle', methods=['POST'])
@login_required
def batch_toggle():
    """批量启用/禁用任务"""
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    enable = data.get('enable', True)
    
    if not task_ids:
        return jsonify({'error': '请选择要操作的任务'}), 400
    
    try:
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()
        if not tasks:
            return jsonify({'error': '未找到指定的任务'}), 404
        
        updated_count = 0
        for task in tasks:
            task.is_active = enable
            updated_count += 1
        
        db.session.commit()
        
        action = '启用' if enable else '禁用'
        return jsonify({
            'message': f'成功{action} {updated_count} 个任务',
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'批量操作失败: {str(e)}'}), 500

@tasks_bp.route('/batch-execute', methods=['POST'])
@login_required
def batch_execute():
    """批量执行任务"""
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'error': '请选择要执行的任务'}), 400
    
    try:
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()
        if not tasks:
            return jsonify({'error': '未找到指定的任务'}), 404
        
        executor = TaskExecutor()
        executed_count = 0
        results = []
        
        for task in tasks:
            try:
                result = executor.execute_task(task.id)
                results.append({
                    'task_name': task.name,
                    'result': result
                })
                executed_count += 1
            except Exception as e:
                results.append({
                    'task_name': task.name,
                    'result': {
                        'success': False,
                        'error': str(e)
                    }
                })
        
        return jsonify({
            'message': f'批量执行完成，处理了 {executed_count} 个任务',
            'executed_count': executed_count,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'批量执行失败: {str(e)}'}), 500

@tasks_bp.route('/<int:task_id>')
@login_required
def detail(task_id):
    """任务详情"""
    task = Task.query.get_or_404(task_id)
    
    if request.is_json:
        return jsonify(task.to_dict())
    
    return render_template('tasks/detail.html', task=task)

@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    """编辑任务"""
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # 更新任务信息
            task.name = data.get('name', task.name)
            task.task_type = data.get('task_type', task.task_type)
            task.instance_id = data.get('instance_id', task.instance_id)
            task.schedule = data.get('schedule', task.schedule)
            task.description = data.get('description', task.description)
            task.is_active = data.get('is_active', task.is_active)
            
            db.session.commit()
            
            # 重新启动定时任务
            if task.is_active:
                start_scheduled_task(task)
            else:
                stop_scheduled_task(task)
            
            if request.is_json:
                return jsonify({
                    'message': '任务更新成功',
                    'task': task.to_dict()
                })
            
            flash('任务更新成功！', 'success')
            return redirect(url_for('tasks.detail', task_id=task_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"更新任务失败: {e}")
            
            if request.is_json:
                return jsonify({'error': '更新任务失败，请重试'}), 500
            
            flash('更新任务失败，请重试', 'error')
    
    # GET请求，显示编辑表单
    instances = Instance.query.filter_by(is_active=True).all()
    
    if request.is_json:
        return jsonify({
            'task': task.to_dict(),
            'instances': [instance.to_dict() for instance in instances]
        })
    
    return render_template('tasks/edit.html', 
                         task=task, 
                         instances=instances)

@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    """删除任务"""
    task = Task.query.get_or_404(task_id)
    
    try:
        # 停止定时任务
        stop_scheduled_task(task)
        
        db.session.delete(task)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': '任务删除成功'})
        
        flash('任务删除成功！', 'success')
        return redirect(url_for('tasks.index'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"删除任务失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '删除任务失败，请重试'}), 500
        
        flash('删除任务失败，请重试', 'error')
        return redirect(url_for('tasks.index'))

@tasks_bp.route('/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle(task_id):
    """启用/禁用任务"""
    task = Task.query.get_or_404(task_id)
    
    try:
        task.is_active = not task.is_active
        
        if task.is_active:
            start_scheduled_task(task)
        else:
            stop_scheduled_task(task)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'message': f'任务已{"启用" if task.is_active else "禁用"}',
                'is_active': task.is_active
            })
        
        flash(f'任务已{"启用" if task.is_active else "禁用"}', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"切换任务状态失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '切换任务状态失败，请重试'}), 500
        
        flash('切换任务状态失败，请重试', 'error')
    
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/<int:task_id>/run', methods=['POST'])
@login_required
def run_now(task_id):
    """立即运行任务"""
    task = Task.query.get_or_404(task_id)
    
    try:
        # 立即执行任务
        result = execute_task.delay(task.id)
        
        if request.is_json:
            return jsonify({
                'message': '任务已提交执行',
                'task_id': result.id
            })
        
        flash('任务已提交执行', 'success')
        
    except Exception as e:
        logging.error(f"执行任务失败: {e}")
        
        if request.is_json:
            return jsonify({'error': '执行任务失败，请重试'}), 500
        
        flash('执行任务失败，请重试', 'error')
    
    return redirect(url_for('tasks.index'))

def start_scheduled_task(task):
    """启动定时任务"""
    try:
        if task.task_type == 'sync_accounts':
            # 启动账户同步任务
            from celery.schedules import crontab
            
            # 解析cron表达式
            if task.schedule:
                # 这里需要解析cron表达式并启动任务
                # 简化处理，直接启动
                pass
    except Exception as e:
        logging.error(f"启动定时任务失败: {e}")

def stop_scheduled_task(task):
    """停止定时任务"""
    try:
        # 停止定时任务
        pass
    except Exception as e:
        logging.error(f"停止定时任务失败: {e}")

@celery.task
def execute_task(task_id):
    """执行任务"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}
        
        if task.task_type == 'sync_accounts':
            # 执行账户同步
            instance = Instance.query.get(task.instance_id)
            if not instance:
                return {'success': False, 'error': '实例不存在'}
            
            db_service = DatabaseService()
            result = db_service.sync_accounts(instance)
            
            # 更新任务状态
            task.last_run = datetime.utcnow()
            task.last_status = 'success' if result['success'] else 'failed'
            task.last_message = result.get('message', result.get('error', ''))
            db.session.commit()
            
            return result
        else:
            return {'success': False, 'error': '不支持的任务类型'}
            
    except Exception as e:
        logging.error(f"执行任务失败: {e}")
        return {'success': False, 'error': str(e)}

# API路由
@tasks_bp.route('/api/tasks')
@jwt_required()
def api_list():
    """获取任务列表API"""
    tasks = Task.query.filter_by(is_active=True).all()
    return jsonify([task.to_dict() for task in tasks])

@tasks_bp.route('/api/tasks/<int:task_id>')
@jwt_required()
def api_detail(task_id):
    """获取任务详情API"""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@tasks_bp.route('/api/tasks/<int:task_id>/run')
@jwt_required()
def api_run_now(task_id):
    """立即运行任务API"""
    task = Task.query.get_or_404(task_id)
    
    try:
        result = execute_task.delay(task.id)
        return jsonify({
            'success': True,
            'message': '任务已提交执行',
            'task_id': result.id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@tasks_bp.route('/create-builtin', methods=['POST'])
@login_required
def create_builtin_tasks():
    """创建内置任务"""
    try:
        executor = TaskExecutor()
        result = executor.create_builtin_tasks()
        
        if result['success']:
            if request.is_json:
                return jsonify(result)
            flash(result['message'], 'success')
        else:
            if request.is_json:
                return jsonify(result), 400
            flash(result['error'], 'error')
            
    except Exception as e:
        logging.error(f"创建内置任务失败: {e}")
        error_msg = f'创建内置任务失败: {str(e)}'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
    
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/<int:task_id>/execute', methods=['POST'])
@login_required
def execute_task_direct(task_id):
    """直接执行指定任务"""
    try:
        executor = TaskExecutor()
        result = executor.execute_task(task_id)
        
        if request.is_json:
            return jsonify(result)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['error'], 'error')
            
    except Exception as e:
        logging.error(f"执行任务失败: {e}")
        error_msg = f'执行任务失败: {str(e)}'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
    
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/execute-all', methods=['POST'])
@login_required
def execute_all_tasks():
    """执行所有活跃任务"""
    try:
        executor = TaskExecutor()
        result = executor.execute_all_active_tasks()
        
        if request.is_json:
            return jsonify(result)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['error'], 'error')
            
    except Exception as e:
        logging.error(f"批量执行任务失败: {e}")
        error_msg = f'批量执行任务失败: {str(e)}'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
    
    return redirect(url_for('tasks.index'))