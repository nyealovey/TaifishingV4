# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 权限配置数据模型
"""

from app import db
from datetime import datetime

class PermissionConfig(db.Model):
    """权限配置数据模型"""
    __tablename__ = 'permission_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    db_type = db.Column(db.String(50), nullable=False)  # 数据库类型：mysql, postgresql, sqlserver, oracle
    category = db.Column(db.String(50), nullable=False)  # 权限类别：global_privileges, database_privileges, server_roles, database_roles, server_permissions
    permission_name = db.Column(db.String(255), nullable=False)  # 权限名称
    description = db.Column(db.Text, nullable=True)  # 权限描述
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    sort_order = db.Column(db.Integer, default=0)  # 排序顺序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：同一数据库类型的同一类别下，权限名称不能重复
    __table_args__ = (
        db.UniqueConstraint('db_type', 'category', 'permission_name', name='uq_permission_config'),
        db.Index('idx_permission_config_db_type', 'db_type'),
        db.Index('idx_permission_config_category', 'category'),
    )
    
    def __repr__(self):
        return f'<PermissionConfig {self.db_type}.{self.category}.{self.permission_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'db_type': self.db_type,
            'category': self.category,
            'permission_name': self.permission_name,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_permissions_by_db_type(cls, db_type):
        """根据数据库类型获取权限配置"""
        permissions = cls.query.filter_by(db_type=db_type, is_active=True).order_by(cls.category, cls.sort_order, cls.permission_name).all()
        
        # 按类别分组
        result = {}
        for perm in permissions:
            if perm.category not in result:
                result[perm.category] = []
            result[perm.category].append({
                'name': perm.permission_name,
                'description': perm.description
            })
        
        return result
    
    @classmethod
    def init_default_permissions(cls):
        """初始化默认权限配置"""
        # 检查是否已经初始化过
        if cls.query.first():
            return
        
        # MySQL权限配置
        mysql_permissions = [
            # 全局权限（服务器权限）
            ('mysql', 'global_privileges', 'ALTER', '修改表结构', 1),
            ('mysql', 'global_privileges', 'ALTER ROUTINE', '修改存储过程和函数', 2),
            ('mysql', 'global_privileges', 'CREATE', '创建数据库和表', 3),
            ('mysql', 'global_privileges', 'CREATE ROUTINE', '创建存储过程和函数', 4),
            ('mysql', 'global_privileges', 'CREATE TEMPORARY TABLES', '创建临时表', 5),
            ('mysql', 'global_privileges', 'CREATE USER', '创建用户权限', 6),
            ('mysql', 'global_privileges', 'CREATE VIEW', '创建视图', 7),
            ('mysql', 'global_privileges', 'DELETE', '删除数据', 8),
            ('mysql', 'global_privileges', 'DROP', '删除数据库和表', 9),
            ('mysql', 'global_privileges', 'EVENT', '创建、修改、删除事件', 10),
            ('mysql', 'global_privileges', 'EXECUTE', '执行存储过程和函数', 11),
            ('mysql', 'global_privileges', 'FILE', '文件操作权限', 12),
            ('mysql', 'global_privileges', 'GRANT OPTION', '授权权限，可以授予其他用户权限', 13),
            ('mysql', 'global_privileges', 'INDEX', '创建和删除索引', 14),
            ('mysql', 'global_privileges', 'INSERT', '插入数据', 15),
            ('mysql', 'global_privileges', 'LOCK TABLES', '锁定表', 16),
            ('mysql', 'global_privileges', 'PROCESS', '查看所有进程', 17),
            ('mysql', 'global_privileges', 'REFERENCES', '引用权限', 18),
            ('mysql', 'global_privileges', 'RELOAD', '重载权限表', 19),
            ('mysql', 'global_privileges', 'REPLICATION CLIENT', '复制客户端权限', 20),
            ('mysql', 'global_privileges', 'REPLICATION SLAVE', '复制从库权限', 21),
            ('mysql', 'global_privileges', 'SELECT', '查询数据', 22),
            ('mysql', 'global_privileges', 'SHOW DATABASES', '显示所有数据库', 23),
            ('mysql', 'global_privileges', 'SHOW VIEW', '显示视图', 24),
            ('mysql', 'global_privileges', 'SHUTDOWN', '关闭MySQL服务器', 25),
            ('mysql', 'global_privileges', 'SUPER', '超级权限，可以执行任何操作', 26),
            ('mysql', 'global_privileges', 'TRIGGER', '创建和删除触发器', 27),
            ('mysql', 'global_privileges', 'UPDATE', '更新数据', 28),
            ('mysql', 'global_privileges', 'USAGE', '无权限，仅用于连接', 29),
            
            # 数据库权限
            ('mysql', 'database_privileges', 'CREATE', '创建数据库和表', 1),
            ('mysql', 'database_privileges', 'DROP', '删除数据库和表', 2),
            ('mysql', 'database_privileges', 'ALTER', '修改数据库和表结构', 3),
            ('mysql', 'database_privileges', 'INDEX', '创建和删除索引', 4),
            ('mysql', 'database_privileges', 'INSERT', '插入数据', 5),
            ('mysql', 'database_privileges', 'UPDATE', '更新数据', 6),
            ('mysql', 'database_privileges', 'DELETE', '删除数据', 7),
            ('mysql', 'database_privileges', 'SELECT', '查询数据', 8),
            ('mysql', 'database_privileges', 'CREATE TEMPORARY TABLES', '创建临时表', 9),
            ('mysql', 'database_privileges', 'LOCK TABLES', '锁定表', 10),
            ('mysql', 'database_privileges', 'EXECUTE', '执行存储过程和函数', 11),
            ('mysql', 'database_privileges', 'CREATE VIEW', '创建视图', 12),
            ('mysql', 'database_privileges', 'SHOW VIEW', '显示视图', 13),
            ('mysql', 'database_privileges', 'CREATE ROUTINE', '创建存储过程和函数', 14),
            ('mysql', 'database_privileges', 'ALTER ROUTINE', '修改存储过程和函数', 15),
            ('mysql', 'database_privileges', 'EVENT', '创建、修改、删除事件', 16),
            ('mysql', 'database_privileges', 'TRIGGER', '创建和删除触发器', 17),
        ]
        
        # SQL Server权限配置
        sqlserver_permissions = [
            # 服务器角色
            ('sqlserver', 'server_roles', 'sysadmin', '系统管理员', 1),
            ('sqlserver', 'server_roles', 'serveradmin', '服务器管理员', 2),
            ('sqlserver', 'server_roles', 'securityadmin', '安全管理员', 3),
            ('sqlserver', 'server_roles', 'processadmin', '进程管理员', 4),
            ('sqlserver', 'server_roles', 'setupadmin', '设置管理员', 5),
            ('sqlserver', 'server_roles', 'bulkadmin', '批量操作管理员', 6),
            ('sqlserver', 'server_roles', 'diskadmin', '磁盘管理员', 7),
            ('sqlserver', 'server_roles', 'dbcreator', '数据库创建者', 8),
            ('sqlserver', 'server_roles', 'public', '公共角色', 9),
            
            # 数据库角色
            ('sqlserver', 'database_roles', 'db_owner', '数据库所有者', 1),
            ('sqlserver', 'database_roles', 'db_accessadmin', '访问管理员', 2),
            ('sqlserver', 'database_roles', 'db_securityadmin', '安全管理员', 3),
            ('sqlserver', 'database_roles', 'db_ddladmin', 'DDL管理员', 4),
            ('sqlserver', 'database_roles', 'db_backupoperator', '备份操作员', 5),
            ('sqlserver', 'database_roles', 'db_datareader', '数据读取者', 6),
            ('sqlserver', 'database_roles', 'db_datawriter', '数据写入者', 7),
            ('sqlserver', 'database_roles', 'db_denydatareader', '拒绝数据读取', 8),
            ('sqlserver', 'database_roles', 'db_denydatawriter', '拒绝数据写入', 9),
            
            # 服务器权限
            ('sqlserver', 'server_permissions', 'CONTROL SERVER', '控制服务器', 1),
            ('sqlserver', 'server_permissions', 'ALTER ANY LOGIN', '修改任意登录', 2),
            ('sqlserver', 'server_permissions', 'ALTER ANY SERVER ROLE', '修改任意服务器角色', 3),
            ('sqlserver', 'server_permissions', 'CREATE ANY DATABASE', '创建任意数据库', 4),
            ('sqlserver', 'server_permissions', 'ALTER ANY DATABASE', '修改任意数据库', 5),
            ('sqlserver', 'server_permissions', 'VIEW SERVER STATE', '查看服务器状态', 6),
            ('sqlserver', 'server_permissions', 'ALTER SERVER STATE', '修改服务器状态', 7),
            ('sqlserver', 'server_permissions', 'ALTER SETTINGS', '修改设置', 8),
            ('sqlserver', 'server_permissions', 'ALTER TRACE', '修改跟踪', 9),
            ('sqlserver', 'server_permissions', 'AUTHENTICATE SERVER', '服务器身份验证', 10),
            ('sqlserver', 'server_permissions', 'BACKUP DATABASE', '备份数据库', 11),
            ('sqlserver', 'server_permissions', 'BACKUP LOG', '备份日志', 12),
            ('sqlserver', 'server_permissions', 'CHECKPOINT', '检查点', 13),
            ('sqlserver', 'server_permissions', 'CONNECT SQL', '连接SQL', 14),
            ('sqlserver', 'server_permissions', 'SHUTDOWN', '关闭服务器', 15),
            ('sqlserver', 'server_permissions', 'IMPERSONATE ANY LOGIN', '模拟任意登录', 16),
            ('sqlserver', 'server_permissions', 'VIEW ANY DEFINITION', '查看任意定义', 17),
            ('sqlserver', 'server_permissions', 'VIEW ANY COLUMN ENCRYPTION KEY DEFINITION', '查看任意列加密密钥定义', 18),
            ('sqlserver', 'server_permissions', 'VIEW ANY COLUMN MASTER KEY DEFINITION', '查看任意列主密钥定义', 19),
            
            # 数据库权限
            ('sqlserver', 'database_privileges', 'SELECT', '查询数据', 1),
            ('sqlserver', 'database_privileges', 'INSERT', '插入数据', 2),
            ('sqlserver', 'database_privileges', 'UPDATE', '更新数据', 3),
            ('sqlserver', 'database_privileges', 'DELETE', '删除数据', 4),
            ('sqlserver', 'database_privileges', 'CREATE', '创建对象', 5),
            ('sqlserver', 'database_privileges', 'ALTER', '修改/删除对象（包含DROP功能）', 6),
            ('sqlserver', 'database_privileges', 'EXECUTE', '执行存储过程', 7),
            ('sqlserver', 'database_privileges', 'CONTROL', '完全控制权限', 8),
            ('sqlserver', 'database_privileges', 'REFERENCES', '引用权限', 9),
            ('sqlserver', 'database_privileges', 'VIEW DEFINITION', '查看定义', 10),
            ('sqlserver', 'database_privileges', 'TAKE OWNERSHIP', '获取所有权', 11),
            ('sqlserver', 'database_privileges', 'IMPERSONATE', '模拟权限', 12),
            ('sqlserver', 'database_privileges', 'CREATE SCHEMA', '创建架构', 13),
            ('sqlserver', 'database_privileges', 'ALTER ANY SCHEMA', '修改任意架构', 14),
            ('sqlserver', 'database_privileges', 'CREATE TABLE', '创建表', 15),
            ('sqlserver', 'database_privileges', 'CREATE VIEW', '创建视图', 16),
            ('sqlserver', 'database_privileges', 'CREATE PROCEDURE', '创建存储过程', 17),
            ('sqlserver', 'database_privileges', 'CREATE FUNCTION', '创建函数', 18),
            ('sqlserver', 'database_privileges', 'CREATE TRIGGER', '创建触发器', 19),
        ]
        
        # 批量插入权限配置
        all_permissions = mysql_permissions + sqlserver_permissions
        
        for db_type, category, permission_name, description, sort_order in all_permissions:
            perm = cls(
                db_type=db_type,
                category=category,
                permission_name=permission_name,
                description=description,
                sort_order=sort_order
            )
            db.session.add(perm)
        
        try:
            db.session.commit()
            print(f"成功初始化 {len(all_permissions)} 个权限配置")
        except Exception as e:
            db.session.rollback()
            print(f"初始化权限配置失败: {e}")
            raise
