# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户分类管理路由
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.account_classification import AccountClassification, ClassificationRule, AccountClassificationAssignment
from app.services.account_classification_service import AccountClassificationService
import json

account_classification_bp = Blueprint('account_classification', __name__, url_prefix='/account-classification')

@account_classification_bp.route('/')
@login_required
def index():
    """账户分类管理首页"""
    return render_template('account_classification/index.html')

@account_classification_bp.route('/rules-page')
@login_required
def rules():
    """规则管理页面"""
    return render_template('account_classification/rules.html')

@account_classification_bp.route('/classifications')
@login_required
def get_classifications():
    """获取所有账户分类"""
    try:
        classifications = AccountClassification.query.filter_by(is_active=True).order_by(AccountClassification.priority.desc(), AccountClassification.created_at.desc()).all()
        
        result = []
        for classification in classifications:
            # 计算该分类的规则数量
            rules_count = ClassificationRule.query.filter_by(
                classification_id=classification.id, 
                is_active=True
            ).count()
            
            result.append({
                'id': classification.id,
                'name': classification.name,
                'description': classification.description,
                'risk_level': classification.risk_level,
                'color': classification.color,
                'priority': classification.priority,
                'is_system': classification.is_system,
                'rules_count': rules_count,
                'created_at': classification.created_at.isoformat() if classification.created_at else None,
                'updated_at': classification.updated_at.isoformat() if classification.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'classifications': result
        })
    
    except Exception as e:
        current_app.logger.error(f"获取账户分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/classifications', methods=['POST'])
@login_required
def create_classification():
    """创建账户分类"""
    try:
        data = request.get_json()
        
        classification = AccountClassification(
            name=data['name'],
            description=data.get('description', ''),
            risk_level=data.get('risk_level', 'medium'),
            color=data.get('color', '#6c757d'),
            priority=data.get('priority', 0),
            is_system=False
        )
        
        db.session.add(classification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'classification': {
                'id': classification.id,
                'name': classification.name,
                'description': classification.description,
                'risk_level': classification.risk_level,
                'color': classification.color,
                'priority': classification.priority,
                'is_system': classification.is_system
            }
        })
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建账户分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/classifications/<int:classification_id>')
@login_required
def get_classification(classification_id):
    """获取单个账户分类"""
    try:
        classification = AccountClassification.query.get_or_404(classification_id)
        
        return jsonify({
            'success': True,
            'classification': {
                'id': classification.id,
                'name': classification.name,
                'description': classification.description,
                'risk_level': classification.risk_level,
                'color': classification.color,
                'priority': classification.priority,
                'is_system': classification.is_system,
                'created_at': classification.created_at.isoformat() if classification.created_at else None,
                'updated_at': classification.updated_at.isoformat() if classification.updated_at else None
            }
        })
    
    except Exception as e:
        current_app.logger.error(f"获取账户分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/classifications/<int:classification_id>', methods=['PUT'])
@login_required
def update_classification(classification_id):
    """更新账户分类"""
    try:
        classification = AccountClassification.query.get_or_404(classification_id)
        data = request.get_json()
        
        classification.name = data['name']
        classification.description = data.get('description', '')
        classification.risk_level = data.get('risk_level', 'medium')
        classification.color = data.get('color', '#6c757d')
        classification.priority = data.get('priority', 0)
        
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新账户分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/classifications/<int:classification_id>', methods=['DELETE'])
@login_required
def delete_classification(classification_id):
    """删除账户分类"""
    try:
        classification = AccountClassification.query.get_or_404(classification_id)
        
        # 系统分类不能删除
        if classification.is_system:
            return jsonify({
                'success': False,
                'error': '系统分类不能删除'
            })
        
        db.session.delete(classification)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除账户分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/rules/filter')
@login_required
def get_rules():
    """获取分类规则"""
    try:
        classification_id = request.args.get('classification_id', type=int)
        db_type = request.args.get('db_type')
        
        query = ClassificationRule.query.filter_by(is_active=True)
        
        if classification_id:
            query = query.filter_by(classification_id=classification_id)
        
        if db_type:
            query = query.filter_by(db_type=db_type)
        
        rules = query.order_by(ClassificationRule.created_at.desc()).all()
        
        result = []
        for rule in rules:
            result.append({
                'id': rule.id,
                'rule_name': rule.rule_name,
                'classification_id': rule.classification_id,
                'classification_name': rule.classification.name if rule.classification else None,
                'db_type': rule.db_type,
                'rule_expression': rule.rule_expression,
                'is_active': rule.is_active,
                'created_at': rule.created_at.isoformat() if rule.created_at else None,
                'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'rules': result
        })
    
    except Exception as e:
        current_app.logger.error(f"获取分类规则失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/rules')
@login_required
def list_rules():
    """获取所有规则列表（按数据库类型分组）"""
    try:
        # 获取所有规则
        rules = ClassificationRule.query.filter_by(is_active=True).order_by(ClassificationRule.created_at.desc()).all()
        
        # 获取匹配账户数量
        service = AccountClassificationService()
        result = []
        for rule in rules:
            matched_count = service.get_rule_matched_accounts_count(rule.id)
            result.append({
                'id': rule.id,
                'rule_name': rule.rule_name,
                'classification_id': rule.classification_id,
                'classification_name': rule.classification.name if rule.classification else None,
                'db_type': rule.db_type,
                'rule_expression': rule.rule_expression,
                'is_active': rule.is_active,
                'matched_accounts_count': matched_count,
                'created_at': rule.created_at.isoformat() if rule.created_at else None,
                'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
            })
        
        # 按数据库类型分组
        rules_by_db_type = {}
        for rule in result:
            db_type = rule.get('db_type', 'unknown')
            if db_type not in rules_by_db_type:
                rules_by_db_type[db_type] = []
            rules_by_db_type[db_type].append(rule)
        
        return jsonify({
            'success': True,
            'rules_by_db_type': rules_by_db_type
        })
    
    except Exception as e:
        current_app.logger.error(f"获取规则列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/rules', methods=['POST'])
@login_required
def create_rule():
    """创建分类规则"""
    try:
        data = request.get_json()
        
        # 将规则表达式对象转换为JSON字符串
        rule_expression_json = json.dumps(data['rule_expression'], ensure_ascii=False)
        
        rule = ClassificationRule(
            rule_name=data['rule_name'],
            classification_id=data['classification_id'],
            db_type=data['db_type'],
            rule_expression=rule_expression_json,
            is_active=True
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建分类规则失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/rules/<int:rule_id>', methods=['GET'])
@login_required
def get_rule(rule_id):
    """获取单个规则详情"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)
        
        # 解析规则表达式JSON字符串为对象
        try:
            rule_expression_obj = json.loads(rule.rule_expression) if rule.rule_expression else {}
        except (json.JSONDecodeError, TypeError):
            rule_expression_obj = {}
        
        rule_dict = {
            'id': rule.id,
            'rule_name': rule.rule_name,
            'classification_id': rule.classification_id,
            'classification_name': rule.classification.name if rule.classification else None,
            'db_type': rule.db_type,
            'rule_expression': rule_expression_obj,  # 返回解析后的对象
            'is_active': rule.is_active,
            'created_at': rule.created_at.isoformat() if rule.created_at else None,
            'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'rule': rule_dict
        })
    
    except Exception as e:
        current_app.logger.error(f"获取规则详情失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@login_required
def update_rule(rule_id):
    """更新分类规则"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)
        data = request.get_json()
        
        # 将规则表达式对象转换为JSON字符串
        rule_expression_json = json.dumps(data['rule_expression'], ensure_ascii=False)
        
        rule.rule_name = data['rule_name']
        rule.rule_expression = rule_expression_json
        rule.is_active = data.get('is_active', True)
        
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新分类规则失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/rules/<int:rule_id>/matched-accounts', methods=['GET'])
@login_required
def get_matched_accounts(rule_id):
    """获取规则匹配的账户"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)
        
        # 获取匹配的账户
        from app.services.account_classification_service import AccountClassificationService
        classification_service = AccountClassificationService()
        
        # 获取所有账户
        from app.models.account import Account
        from app.models.instance import Instance
        all_accounts = Account.query.join(Instance, Account.instance_id == Instance.id).filter(Instance.db_type == rule.db_type).all()
        
        matched_accounts = []
        for account in all_accounts:
            # 检查账户是否匹配规则
            if classification_service.evaluate_rule(rule, account):
                matched_accounts.append({
                    'id': account.id,
                    'username': account.username,
                    'instance_name': account.instance.name if account.instance else '未知实例',
                    'instance_host': account.instance.host if account.instance else '未知IP'
                })
        
        return jsonify({
            'success': True,
            'accounts': matched_accounts,
            'rule_name': rule.rule_name
        })
    
    except Exception as e:
        current_app.logger.error(f"获取匹配账户失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@login_required
def delete_rule(rule_id):
    """删除分类规则"""
    try:
        rule = ClassificationRule.query.get_or_404(rule_id)
        
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除分类规则失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/assign', methods=['POST'])
@login_required
def assign_classification():
    """分配账户分类"""
    try:
        data = request.get_json()
        
        service = AccountClassificationService()
        result = service.classify_account(
            data['account_id'],
            data['classification_id'],
            current_user.id
        )
        
        return jsonify({
            'success': True,
            'assignment_id': result
        })
    
    except Exception as e:
        current_app.logger.error(f"分配账户分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/auto-classify', methods=['POST'])
@login_required
def auto_classify():
    """自动分类账户"""
    try:
        data = request.get_json()
        instance_id = data.get('instance_id')
        
        service = AccountClassificationService()
        result = service.auto_classify_accounts(instance_id)
        
        # 直接返回服务层的结果
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"自动分类失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/assignments')
@login_required
def get_assignments():
    """获取账户分类分配"""
    try:
        assignments = db.session.query(AccountClassificationAssignment, AccountClassification).join(
            AccountClassification, AccountClassificationAssignment.classification_id == AccountClassification.id
        ).filter(AccountClassificationAssignment.is_active == True).all()
        
        result = []
        for assignment, classification in assignments:
            result.append({
                'id': assignment.id,
                'account_id': assignment.assigned_by,
                'classification_id': assignment.classification_id,
                'classification_name': classification.name,
                'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None
            })
        
        return jsonify({
            'success': True,
            'assignments': result
        })
    
    except Exception as e:
        current_app.logger.error(f"获取账户分类分配失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@account_classification_bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
def remove_assignment(assignment_id):
    """移除账户分类分配"""
    try:
        assignment = AccountClassificationAssignment.query.get_or_404(assignment_id)
        assignment.is_active = False
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"移除账户分类分配失败: {e}")
        return jsonify({
            'success': False,
            'error': f'移除分配失败: {str(e)}'
        })


@account_classification_bp.route('/permissions/<db_type>')
@login_required
def get_permissions(db_type):
    """获取数据库权限列表"""
    try:
        permissions = _get_db_permissions(db_type)
        
        return jsonify({
            'success': True,
            'permissions': permissions
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def _get_db_permissions(db_type: str) -> dict:
    """获取数据库权限列表"""
    from app.models.permission_config import PermissionConfig
    
    # 从数据库获取权限配置
    permissions = PermissionConfig.get_permissions_by_db_type(db_type)
    
    return permissions
