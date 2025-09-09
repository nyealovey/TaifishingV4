# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 账户分类管理服务
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from app import db
from app.models.account_classification import (
    AccountClassification, 
    ClassificationRule, 
    AccountClassificationAssignment,
    ClassificationTemplate
)
from app.models.account import Account
from app.models.instance import Instance
from app.models.user import User
from app.utils.logger import log_operation

class AccountClassificationService:
    """账户分类管理服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_classification(self, name: str, description: str = None, 
                            risk_level: str = 'medium', color: str = None, 
                            priority: int = 0) -> Dict[str, Any]:
        """创建账户分类"""
        try:
            # 检查分类名称是否已存在
            existing = AccountClassification.query.filter_by(name=name).first()
            if existing:
                return {
                    'success': False,
                    'error': f'分类名称 "{name}" 已存在'
                }
            
            classification = AccountClassification(
                name=name,
                description=description,
                risk_level=risk_level,
                color=color,
                priority=priority
            )
            
            db.session.add(classification)
            db.session.commit()
            
            log_operation('CREATE_CLASSIFICATION', details={
                'classification_id': classification.id,
                'classification_name': name,
                'risk_level': risk_level
            })
            
            return {
                'success': True,
                'message': f'账户分类 "{name}" 创建成功',
                'classification': classification.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"创建账户分类失败: {e}")
            return {
                'success': False,
                'error': f'创建账户分类失败: {str(e)}'
            }
    
    def update_classification(self, classification_id: int, **kwargs) -> Dict[str, Any]:
        """更新账户分类"""
        try:
            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {
                    'success': False,
                    'error': '分类不存在'
                }
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(classification, key):
                    setattr(classification, key, value)
            
            classification.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_operation('UPDATE_CLASSIFICATION', details={
                'classification_id': classification_id,
                'updated_fields': list(kwargs.keys())
            })
            
            return {
                'success': True,
                'message': f'账户分类 "{classification.name}" 更新成功',
                'classification': classification.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"更新账户分类失败: {e}")
            return {
                'success': False,
                'error': f'更新账户分类失败: {str(e)}'
            }
    
    def delete_classification(self, classification_id: int) -> Dict[str, Any]:
        """删除账户分类"""
        try:
            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {
                    'success': False,
                    'error': '分类不存在'
                }
            
            # 检查是否有关联的账户分配
            assignments_count = classification.account_assignments.filter_by(is_active=True).count()
            if assignments_count > 0:
                return {
                    'success': False,
                    'error': f'无法删除分类，还有 {assignments_count} 个账户正在使用此分类'
                }
            
            classification_name = classification.name
            db.session.delete(classification)
            db.session.commit()
            
            log_operation('DELETE_CLASSIFICATION', details={
                'classification_id': classification_id,
                'classification_name': classification_name
            })
            
            return {
                'success': True,
                'message': f'账户分类 "{classification_name}" 删除成功'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"删除账户分类失败: {e}")
            return {
                'success': False,
                'error': f'删除账户分类失败: {str(e)}'
            }
    
    def create_rule(self, classification_id: int, db_type: str, rule_name: str, 
                   rule_expression: Dict[str, Any]) -> Dict[str, Any]:
        """创建分类规则"""
        try:
            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {
                    'success': False,
                    'error': '分类不存在'
                }
            
            rule = ClassificationRule(
                classification_id=classification_id,
                db_type=db_type,
                rule_name=rule_name,
                rule_expression=json.dumps(rule_expression, ensure_ascii=False)
            )
            
            db.session.add(rule)
            db.session.commit()
            
            log_operation('CREATE_CLASSIFICATION_RULE', details={
                'rule_id': rule.id,
                'classification_id': classification_id,
                'db_type': db_type,
                'rule_name': rule_name
            })
            
            return {
                'success': True,
                'message': f'规则 "{rule_name}" 创建成功',
                'rule': rule.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"创建分类规则失败: {e}")
            return {
                'success': False,
                'error': f'创建分类规则失败: {str(e)}'
            }
    
    def update_rule(self, rule_id: int, **kwargs) -> Dict[str, Any]:
        """更新分类规则"""
        try:
            rule = ClassificationRule.query.get(rule_id)
            if not rule:
                return {
                    'success': False,
                    'error': '规则不存在'
                }
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    if key == 'rule_expression' and isinstance(value, dict):
                        rule.set_rule_expression(value)
                    else:
                        setattr(rule, key, value)
            
            rule.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_operation('UPDATE_CLASSIFICATION_RULE', details={
                'rule_id': rule_id,
                'updated_fields': list(kwargs.keys())
            })
            
            return {
                'success': True,
                'message': f'规则 "{rule.rule_name}" 更新成功',
                'rule': rule.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"更新分类规则失败: {e}")
            return {
                'success': False,
                'error': f'更新分类规则失败: {str(e)}'
            }
    
    def delete_rule(self, rule_id: int) -> Dict[str, Any]:
        """删除分类规则"""
        try:
            rule = ClassificationRule.query.get(rule_id)
            if not rule:
                return {
                    'success': False,
                    'error': '规则不存在'
                }
            
            rule_name = rule.rule_name
            db.session.delete(rule)
            db.session.commit()
            
            log_operation('DELETE_CLASSIFICATION_RULE', details={
                'rule_id': rule_id,
                'rule_name': rule_name
            })
            
            return {
                'success': True,
                'message': f'规则 "{rule_name}" 删除成功'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"删除分类规则失败: {e}")
            return {
                'success': False,
                'error': f'删除分类规则失败: {str(e)}'
            }
    
    def get_classifications(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """获取所有账户分类"""
        try:
            query = AccountClassification.query
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            classifications = query.order_by(AccountClassification.priority.desc(), 
                                           AccountClassification.name).all()
            
            return [classification.to_dict() for classification in classifications]
            
        except Exception as e:
            self.logger.error(f"获取账户分类失败: {e}")
            return []
    
    def get_classification_rules(self, classification_id: int = None, 
                               db_type: str = None) -> List[Dict[str, Any]]:
        """获取分类规则"""
        try:
            query = ClassificationRule.query.filter_by(is_active=True)
            
            if classification_id:
                query = query.filter_by(classification_id=classification_id)
            
            if db_type:
                query = query.filter_by(db_type=db_type)
            
            rules = query.order_by(ClassificationRule.created_at.desc()).all()
            
            return [rule.to_dict() for rule in rules]
            
        except Exception as e:
            self.logger.error(f"获取分类规则失败: {e}")
            return []
    
    def classify_account(self, account_id: int, classification_id: int, 
                        assignment_type: str = 'manual', assigned_by: int = None,
                        notes: str = None) -> Dict[str, Any]:
        """为账户分配分类"""
        try:
            account = Account.query.get(account_id)
            if not account:
                return {
                    'success': False,
                    'error': '账户不存在'
                }
            
            classification = AccountClassification.query.get(classification_id)
            if not classification:
                return {
                    'success': False,
                    'error': '分类不存在'
                }
            
            # 检查是否已有分配
            existing = AccountClassificationAssignment.query.filter_by(
                account_id=account_id,
                classification_id=classification_id
            ).first()
            
            if existing:
                # 更新现有分配
                existing.assignment_type = assignment_type
                existing.assigned_by = assigned_by
                existing.notes = notes
                existing.updated_at = datetime.utcnow()
            else:
                # 创建新分配
                assignment = AccountClassificationAssignment(
                    account_id=account_id,
                    classification_id=classification_id,
                    assigned_by=assigned_by,
                    assignment_type=assignment_type,
                    notes=notes
                )
                db.session.add(assignment)
            
            db.session.commit()
            
            log_operation('ASSIGN_ACCOUNT_CLASSIFICATION', details={
                'account_id': account_id,
                'classification_id': classification_id,
                'assignment_type': assignment_type
            })
            
            return {
                'success': True,
                'message': f'账户 "{account.username}" 已分配到分类 "{classification.name}"'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"分配账户分类失败: {e}")
            return {
                'success': False,
                'error': f'分配账户分类失败: {str(e)}'
            }
    
    def auto_classify_accounts(self, instance_id: int = None) -> Dict[str, Any]:
        """自动分类账户"""
        try:
            # 获取所有活跃的分类规则
            rules = ClassificationRule.query.filter_by(is_active=True).all()
            
            if not rules:
                return {
                    'success': False,
                    'error': '没有可用的分类规则'
                }
            
            # 获取需要分类的账户
            query = Account.query.filter_by(is_active=True)
            if instance_id:
                query = query.filter_by(instance_id=instance_id)
            
            accounts = query.all()
            
            classified_count = 0
            errors = []
            
            for account in accounts:
                try:
                    # 根据账户的数据库类型获取对应的规则
                    account_rules = [rule for rule in rules if rule.db_type == account.instance.db_type]
                    
                    if not account_rules:
                        continue
                    
                    # 应用规则进行自动分类
                    for rule in account_rules:
                        if self._evaluate_rule(account, rule):
                            # 分配分类
                            result = self.classify_account(
                                account.id, 
                                rule.classification_id, 
                                'auto'
                            )
                            if result['success']:
                                classified_count += 1
                            break
                            
                except Exception as e:
                    errors.append(f"账户 {account.username}: {str(e)}")
            
            log_operation('AUTO_CLASSIFY_ACCOUNTS', details={
                'instance_id': instance_id,
                'classified_count': classified_count,
                'total_accounts': len(accounts)
            })
            
            return {
                'success': True,
                'message': f'自动分类完成，成功分类 {classified_count} 个账户',
                'classified_count': classified_count,
                'total_accounts': len(accounts),
                'errors': errors
            }
            
        except Exception as e:
            self.logger.error(f"自动分类账户失败: {e}")
            return {
                'success': False,
                'error': f'自动分类账户失败: {str(e)}'
            }
    
    def _evaluate_rule(self, account: Account, rule: ClassificationRule) -> bool:
        """评估规则是否匹配账户"""
        try:
            rule_expression = rule.get_rule_expression()
            if not rule_expression:
                return False
            
            # 这里需要根据具体的权限检查逻辑来实现
            # 暂时返回False，后续需要实现具体的权限匹配逻辑
            return False
            
        except Exception as e:
            self.logger.error(f"评估规则失败: {e}")
            return False
    
    def get_account_classifications(self, account_id: int = None) -> List[Dict[str, Any]]:
        """获取账户分类分配"""
        try:
            query = AccountClassificationAssignment.query.filter_by(is_active=True)
            
            if account_id:
                query = query.filter_by(account_id=account_id)
            
            assignments = query.all()
            
            return [assignment.to_dict() for assignment in assignments]
            
        except Exception as e:
            self.logger.error(f"获取账户分类分配失败: {e}")
            return []
    
    def remove_account_classification(self, assignment_id: int) -> Dict[str, Any]:
        """移除账户分类分配"""
        try:
            assignment = AccountClassificationAssignment.query.get(assignment_id)
            if not assignment:
                return {
                    'success': False,
                    'error': '分配记录不存在'
                }
            
            assignment.is_active = False
            assignment.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_operation('REMOVE_ACCOUNT_CLASSIFICATION', details={
                'assignment_id': assignment_id,
                'account_id': assignment.account_id,
                'classification_id': assignment.classification_id
            })
            
            return {
                'success': True,
                'message': '账户分类分配已移除'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"移除账户分类分配失败: {e}")
            return {
                'success': False,
                'error': f'移除账户分类分配失败: {str(e)}'
            }

# 全局实例
account_classification_service = AccountClassificationService()
