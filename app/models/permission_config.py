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
        
        # Oracle权限配置
        oracle_permissions = [
            # 系统权限
            ('oracle', 'system_privileges', 'CREATE SESSION', '创建会话权限', 1),
            ('oracle', 'system_privileges', 'CREATE USER', '创建用户权限', 2),
            ('oracle', 'system_privileges', 'ALTER USER', '修改用户权限', 3),
            ('oracle', 'system_privileges', 'DROP USER', '删除用户权限', 4),
            ('oracle', 'system_privileges', 'CREATE ROLE', '创建角色权限', 5),
            ('oracle', 'system_privileges', 'ALTER ROLE', '修改角色权限', 6),
            ('oracle', 'system_privileges', 'DROP ROLE', '删除角色权限', 7),
            ('oracle', 'system_privileges', 'GRANT ANY PRIVILEGE', '授予任意权限', 8),
            ('oracle', 'system_privileges', 'GRANT ANY ROLE', '授予任意角色', 9),
            ('oracle', 'system_privileges', 'CREATE TABLE', '创建表权限', 10),
            ('oracle', 'system_privileges', 'CREATE ANY TABLE', '创建任意表权限', 11),
            ('oracle', 'system_privileges', 'ALTER ANY TABLE', '修改任意表权限', 12),
            ('oracle', 'system_privileges', 'DROP ANY TABLE', '删除任意表权限', 13),
            ('oracle', 'system_privileges', 'SELECT ANY TABLE', '查询任意表权限', 14),
            ('oracle', 'system_privileges', 'INSERT ANY TABLE', '插入任意表权限', 15),
            ('oracle', 'system_privileges', 'UPDATE ANY TABLE', '更新任意表权限', 16),
            ('oracle', 'system_privileges', 'DELETE ANY TABLE', '删除任意表权限', 17),
            ('oracle', 'system_privileges', 'CREATE INDEX', '创建索引权限', 18),
            ('oracle', 'system_privileges', 'CREATE ANY INDEX', '创建任意索引权限', 19),
            ('oracle', 'system_privileges', 'ALTER ANY INDEX', '修改任意索引权限', 20),
            ('oracle', 'system_privileges', 'DROP ANY INDEX', '删除任意索引权限', 21),
            ('oracle', 'system_privileges', 'CREATE PROCEDURE', '创建存储过程权限', 22),
            ('oracle', 'system_privileges', 'CREATE ANY PROCEDURE', '创建任意存储过程权限', 23),
            ('oracle', 'system_privileges', 'ALTER ANY PROCEDURE', '修改任意存储过程权限', 24),
            ('oracle', 'system_privileges', 'DROP ANY PROCEDURE', '删除任意存储过程权限', 25),
            ('oracle', 'system_privileges', 'EXECUTE ANY PROCEDURE', '执行任意存储过程权限', 26),
            ('oracle', 'system_privileges', 'CREATE SEQUENCE', '创建序列权限', 27),
            ('oracle', 'system_privileges', 'CREATE ANY SEQUENCE', '创建任意序列权限', 28),
            ('oracle', 'system_privileges', 'ALTER ANY SEQUENCE', '修改任意序列权限', 29),
            ('oracle', 'system_privileges', 'DROP ANY SEQUENCE', '删除任意序列权限', 30),
            ('oracle', 'system_privileges', 'SELECT ANY SEQUENCE', '查询任意序列权限', 31),
            ('oracle', 'system_privileges', 'CREATE VIEW', '创建视图权限', 32),
            ('oracle', 'system_privileges', 'CREATE ANY VIEW', '创建任意视图权限', 33),
            ('oracle', 'system_privileges', 'DROP ANY VIEW', '删除任意视图权限', 34),
            ('oracle', 'system_privileges', 'CREATE TRIGGER', '创建触发器权限', 35),
            ('oracle', 'system_privileges', 'CREATE ANY TRIGGER', '创建任意触发器权限', 36),
            ('oracle', 'system_privileges', 'ALTER ANY TRIGGER', '修改任意触发器权限', 37),
            ('oracle', 'system_privileges', 'DROP ANY TRIGGER', '删除任意触发器权限', 38),
            ('oracle', 'system_privileges', 'CREATE TABLESPACE', '创建表空间权限', 39),
            ('oracle', 'system_privileges', 'ALTER TABLESPACE', '修改表空间权限', 40),
            ('oracle', 'system_privileges', 'DROP TABLESPACE', '删除表空间权限', 41),
            ('oracle', 'system_privileges', 'UNLIMITED TABLESPACE', '无限制表空间权限', 42),
            ('oracle', 'system_privileges', 'CREATE DATABASE LINK', '创建数据库链接权限', 43),
            ('oracle', 'system_privileges', 'CREATE PUBLIC DATABASE LINK', '创建公共数据库链接权限', 44),
            ('oracle', 'system_privileges', 'DROP PUBLIC DATABASE LINK', '删除公共数据库链接权限', 45),
            ('oracle', 'system_privileges', 'CREATE SYNONYM', '创建同义词权限', 46),
            ('oracle', 'system_privileges', 'CREATE ANY SYNONYM', '创建任意同义词权限', 47),
            ('oracle', 'system_privileges', 'CREATE PUBLIC SYNONYM', '创建公共同义词权限', 48),
            ('oracle', 'system_privileges', 'DROP ANY SYNONYM', '删除任意同义词权限', 49),
            ('oracle', 'system_privileges', 'DROP PUBLIC SYNONYM', '删除公共同义词权限', 50),
            ('oracle', 'system_privileges', 'AUDIT SYSTEM', '系统审计权限', 51),
            ('oracle', 'system_privileges', 'AUDIT ANY', '任意审计权限', 52),
            ('oracle', 'system_privileges', 'EXEMPT ACCESS POLICY', '豁免访问策略权限', 53),
            ('oracle', 'system_privileges', 'EXEMPT REDACTION POLICY', '豁免数据脱敏策略权限', 54),
            ('oracle', 'system_privileges', 'SYSDBA', '系统数据库管理员权限', 55),
            ('oracle', 'system_privileges', 'SYSOPER', '系统操作员权限', 56),
            
            # 扩展的系统权限 - SYS账户实际拥有的权限
            ('oracle', 'system_privileges', 'CREATE ANY DIRECTORY', '创建任意目录权限', 57),
            ('oracle', 'system_privileges', 'DROP ANY DIRECTORY', '删除任意目录权限', 58),
            ('oracle', 'system_privileges', 'CREATE ANY LIBRARY', '创建任意库权限', 59),
            ('oracle', 'system_privileges', 'DROP ANY LIBRARY', '删除任意库权限', 60),
            ('oracle', 'system_privileges', 'CREATE ANY OPERATOR', '创建任意操作符权限', 61),
            ('oracle', 'system_privileges', 'DROP ANY OPERATOR', '删除任意操作符权限', 62),
            ('oracle', 'system_privileges', 'CREATE ANY TYPE', '创建任意类型权限', 63),
            ('oracle', 'system_privileges', 'ALTER ANY TYPE', '修改任意类型权限', 64),
            ('oracle', 'system_privileges', 'DROP ANY TYPE', '删除任意类型权限', 65),
            ('oracle', 'system_privileges', 'EXECUTE ANY TYPE', '执行任意类型权限', 66),
            ('oracle', 'system_privileges', 'CREATE ANY DIMENSION', '创建任意维度权限', 67),
            ('oracle', 'system_privileges', 'ALTER ANY DIMENSION', '修改任意维度权限', 68),
            ('oracle', 'system_privileges', 'DROP ANY DIMENSION', '删除任意维度权限', 69),
            ('oracle', 'system_privileges', 'CREATE ANY INDEXTYPE', '创建任意索引类型权限', 70),
            ('oracle', 'system_privileges', 'DROP ANY INDEXTYPE', '删除任意索引类型权限', 71),
            ('oracle', 'system_privileges', 'EXECUTE ANY INDEXTYPE', '执行任意索引类型权限', 72),
            ('oracle', 'system_privileges', 'CREATE ANY OUTLINE', '创建任意大纲权限', 73),
            ('oracle', 'system_privileges', 'ALTER ANY OUTLINE', '修改任意大纲权限', 74),
            ('oracle', 'system_privileges', 'DROP ANY OUTLINE', '删除任意大纲权限', 75),
            ('oracle', 'system_privileges', 'CREATE ANY MATERIALIZED VIEW', '创建任意物化视图权限', 76),
            ('oracle', 'system_privileges', 'ALTER ANY MATERIALIZED VIEW', '修改任意物化视图权限', 77),
            ('oracle', 'system_privileges', 'DROP ANY MATERIALIZED VIEW', '删除任意物化视图权限', 78),
            ('oracle', 'system_privileges', 'QUERY REWRITE', '查询重写权限', 79),
            ('oracle', 'system_privileges', 'GLOBAL QUERY REWRITE', '全局查询重写权限', 80),
            ('oracle', 'system_privileges', 'CREATE ANY CONTEXT', '创建任意上下文权限', 81),
            ('oracle', 'system_privileges', 'DROP ANY CONTEXT', '删除任意上下文权限', 82),
            ('oracle', 'system_privileges', 'CREATE ANY CLUSTER', '创建任意簇权限', 83),
            ('oracle', 'system_privileges', 'ALTER ANY CLUSTER', '修改任意簇权限', 84),
            ('oracle', 'system_privileges', 'DROP ANY CLUSTER', '删除任意簇权限', 85),
            ('oracle', 'system_privileges', 'CREATE ANY PROFILE', '创建任意配置文件权限', 86),
            ('oracle', 'system_privileges', 'ALTER ANY PROFILE', '修改任意配置文件权限', 87),
            ('oracle', 'system_privileges', 'DROP ANY PROFILE', '删除任意配置文件权限', 88),
            ('oracle', 'system_privileges', 'CREATE ANY ROLLBACK SEGMENT', '创建任意回滚段权限', 89),
            ('oracle', 'system_privileges', 'ALTER ANY ROLLBACK SEGMENT', '修改任意回滚段权限', 90),
            ('oracle', 'system_privileges', 'DROP ANY ROLLBACK SEGMENT', '删除任意回滚段权限', 91),
            ('oracle', 'system_privileges', 'CREATE ANY SNAPSHOT', '创建任意快照权限', 92),
            ('oracle', 'system_privileges', 'ALTER ANY SNAPSHOT', '修改任意快照权限', 93),
            ('oracle', 'system_privileges', 'DROP ANY SNAPSHOT', '删除任意快照权限', 94),
            ('oracle', 'system_privileges', 'CREATE ANY JOB', '创建任意作业权限', 95),
            ('oracle', 'system_privileges', 'EXECUTE ANY PROGRAM', '执行任意程序权限', 96),
            ('oracle', 'system_privileges', 'MANAGE SCHEDULER', '管理调度器权限', 97),
            ('oracle', 'system_privileges', 'CREATE ANY EVALUATION CONTEXT', '创建任意评估上下文权限', 98),
            ('oracle', 'system_privileges', 'DROP ANY EVALUATION CONTEXT', '删除任意评估上下文权限', 99),
            ('oracle', 'system_privileges', 'CREATE ANY RULE SET', '创建任意规则集权限', 100),
            ('oracle', 'system_privileges', 'ALTER ANY RULE SET', '修改任意规则集权限', 101),
            ('oracle', 'system_privileges', 'DROP ANY RULE SET', '删除任意规则集权限', 102),
            ('oracle', 'system_privileges', 'CREATE ANY RULE', '创建任意规则权限', 103),
            ('oracle', 'system_privileges', 'ALTER ANY RULE', '修改任意规则权限', 104),
            ('oracle', 'system_privileges', 'DROP ANY RULE', '删除任意规则权限', 105),
            ('oracle', 'system_privileges', 'CREATE ANY MINING MODEL', '创建任意挖掘模型权限', 106),
            ('oracle', 'system_privileges', 'ALTER ANY MINING MODEL', '修改任意挖掘模型权限', 107),
            ('oracle', 'system_privileges', 'DROP ANY MINING MODEL', '删除任意挖掘模型权限', 108),
            ('oracle', 'system_privileges', 'SELECT ANY MINING MODEL', '查询任意挖掘模型权限', 109),
            ('oracle', 'system_privileges', 'CREATE ANY SQL PROFILE', '创建任意SQL配置文件权限', 110),
            ('oracle', 'system_privileges', 'DROP ANY SQL PROFILE', '删除任意SQL配置文件权限', 111),
            ('oracle', 'system_privileges', 'ALTER SYSTEM', '修改系统权限', 112),
            ('oracle', 'system_privileges', 'ALTER DATABASE', '修改数据库权限', 113),
            ('oracle', 'system_privileges', 'CREATE DATABASE', '创建数据库权限', 114),
            ('oracle', 'system_privileges', 'DROP DATABASE', '删除数据库权限', 115),
            ('oracle', 'system_privileges', 'CREATE SPFILE', '创建SPFILE权限', 116),
            ('oracle', 'system_privileges', 'ALTER SPFILE', '修改SPFILE权限', 117),
            ('oracle', 'system_privileges', 'CREATE PFILE', '创建PFILE权限', 118),
            ('oracle', 'system_privileges', 'CREATE CONTROLFILE', '创建控制文件权限', 119),
            ('oracle', 'system_privileges', 'ALTER CONTROLFILE', '修改控制文件权限', 120),
            ('oracle', 'system_privileges', 'CREATE RESTORE POINT', '创建还原点权限', 121),
            ('oracle', 'system_privileges', 'DROP RESTORE POINT', '删除还原点权限', 122),
            ('oracle', 'system_privileges', 'FLASHBACK ANY TABLE', '闪回任意表权限', 123),
            ('oracle', 'system_privileges', 'BACKUP ANY TABLE', '备份任意表权限', 124),
            ('oracle', 'system_privileges', 'RESTORE ANY TABLE', '还原任意表权限', 125),
            ('oracle', 'system_privileges', 'RECOVER ANY TABLE', '恢复任意表权限', 126),
            ('oracle', 'system_privileges', 'LOGMINING', '日志挖掘权限', 127),
            ('oracle', 'system_privileges', 'SELECT ANY TRANSACTION', '查询任意事务权限', 128),
            ('oracle', 'system_privileges', 'LOCK ANY TABLE', '锁定任意表权限', 129),
            ('oracle', 'system_privileges', 'COMMENT ANY TABLE', '注释任意表权限', 130),
            ('oracle', 'system_privileges', 'COMMENT ANY COLUMN', '注释任意列权限', 131),
            ('oracle', 'system_privileges', 'GRANT ANY OBJECT PRIVILEGE', '授予任意对象权限', 132),
            ('oracle', 'system_privileges', 'EXEMPT ANY POLICY', '豁免任意策略权限', 133),
            ('oracle', 'system_privileges', 'EXEMPT REDACTION POLICY', '豁免数据脱敏策略权限', 134),
            ('oracle', 'system_privileges', 'EXEMPT ACCESS POLICY', '豁免访问策略权限', 135),
            ('oracle', 'system_privileges', 'EXEMPT IDENTITY POLICY', '豁免身份策略权限', 136),
            ('oracle', 'system_privileges', 'EXEMPT RESOURCE LIMITS', '豁免资源限制权限', 137),
            ('oracle', 'system_privileges', 'EXEMPT CONNECT IDENTIFIER', '豁免连接标识符权限', 138),
            ('oracle', 'system_privileges', 'EXEMPT DDL LOGGING', '豁免DDL日志记录权限', 139),
            ('oracle', 'system_privileges', 'EXEMPT DML LOGGING', '豁免DML日志记录权限', 140),
            ('oracle', 'system_privileges', 'EXEMPT TDE USERSTORE', '豁免TDE用户存储权限', 141),
            ('oracle', 'system_privileges', 'EXEMPT TDE USERSTORE ACCESS', '豁免TDE用户存储访问权限', 142),
            ('oracle', 'system_privileges', 'EXEMPT TDE USERSTORE ADMIN', '豁免TDE用户存储管理权限', 143),
            ('oracle', 'system_privileges', 'EXEMPT TDE USERSTORE ADMIN ACCESS', '豁免TDE用户存储管理访问权限', 144),
            
            # 更多重要的Oracle系统权限 - SYS账户实际拥有的权限
            ('oracle', 'system_privileges', 'CREATE ANY DIRECTORY', '创建任意目录权限', 145),
            ('oracle', 'system_privileges', 'DROP ANY DIRECTORY', '删除任意目录权限', 146),
            ('oracle', 'system_privileges', 'CREATE ANY LIBRARY', '创建任意库权限', 147),
            ('oracle', 'system_privileges', 'DROP ANY LIBRARY', '删除任意库权限', 148),
            ('oracle', 'system_privileges', 'CREATE ANY OPERATOR', '创建任意操作符权限', 149),
            ('oracle', 'system_privileges', 'DROP ANY OPERATOR', '删除任意操作符权限', 150),
            ('oracle', 'system_privileges', 'CREATE ANY TYPE', '创建任意类型权限', 151),
            ('oracle', 'system_privileges', 'ALTER ANY TYPE', '修改任意类型权限', 152),
            ('oracle', 'system_privileges', 'DROP ANY TYPE', '删除任意类型权限', 153),
            ('oracle', 'system_privileges', 'EXECUTE ANY TYPE', '执行任意类型权限', 154),
            ('oracle', 'system_privileges', 'CREATE ANY DIMENSION', '创建任意维度权限', 155),
            ('oracle', 'system_privileges', 'ALTER ANY DIMENSION', '修改任意维度权限', 156),
            ('oracle', 'system_privileges', 'DROP ANY DIMENSION', '删除任意维度权限', 157),
            ('oracle', 'system_privileges', 'CREATE ANY INDEXTYPE', '创建任意索引类型权限', 158),
            ('oracle', 'system_privileges', 'DROP ANY INDEXTYPE', '删除任意索引类型权限', 159),
            ('oracle', 'system_privileges', 'EXECUTE ANY INDEXTYPE', '执行任意索引类型权限', 160),
            ('oracle', 'system_privileges', 'CREATE ANY OUTLINE', '创建任意大纲权限', 161),
            ('oracle', 'system_privileges', 'ALTER ANY OUTLINE', '修改任意大纲权限', 162),
            ('oracle', 'system_privileges', 'DROP ANY OUTLINE', '删除任意大纲权限', 163),
            ('oracle', 'system_privileges', 'CREATE ANY MATERIALIZED VIEW', '创建任意物化视图权限', 164),
            ('oracle', 'system_privileges', 'ALTER ANY MATERIALIZED VIEW', '修改任意物化视图权限', 165),
            ('oracle', 'system_privileges', 'DROP ANY MATERIALIZED VIEW', '删除任意物化视图权限', 166),
            ('oracle', 'system_privileges', 'QUERY REWRITE', '查询重写权限', 167),
            ('oracle', 'system_privileges', 'GLOBAL QUERY REWRITE', '全局查询重写权限', 168),
            ('oracle', 'system_privileges', 'CREATE ANY CONTEXT', '创建任意上下文权限', 169),
            ('oracle', 'system_privileges', 'DROP ANY CONTEXT', '删除任意上下文权限', 170),
            ('oracle', 'system_privileges', 'CREATE ANY CLUSTER', '创建任意簇权限', 171),
            ('oracle', 'system_privileges', 'ALTER ANY CLUSTER', '修改任意簇权限', 172),
            ('oracle', 'system_privileges', 'DROP ANY CLUSTER', '删除任意簇权限', 173),
            ('oracle', 'system_privileges', 'CREATE ANY PROFILE', '创建任意配置文件权限', 174),
            ('oracle', 'system_privileges', 'ALTER ANY PROFILE', '修改任意配置文件权限', 175),
            ('oracle', 'system_privileges', 'DROP ANY PROFILE', '删除任意配置文件权限', 176),
            ('oracle', 'system_privileges', 'CREATE ANY ROLLBACK SEGMENT', '创建任意回滚段权限', 177),
            ('oracle', 'system_privileges', 'ALTER ANY ROLLBACK SEGMENT', '修改任意回滚段权限', 178),
            ('oracle', 'system_privileges', 'DROP ANY ROLLBACK SEGMENT', '删除任意回滚段权限', 179),
            ('oracle', 'system_privileges', 'CREATE ANY SNAPSHOT', '创建任意快照权限', 180),
            ('oracle', 'system_privileges', 'ALTER ANY SNAPSHOT', '修改任意快照权限', 181),
            ('oracle', 'system_privileges', 'DROP ANY SNAPSHOT', '删除任意快照权限', 182),
            ('oracle', 'system_privileges', 'CREATE ANY JOB', '创建任意作业权限', 183),
            ('oracle', 'system_privileges', 'EXECUTE ANY PROGRAM', '执行任意程序权限', 184),
            ('oracle', 'system_privileges', 'MANAGE SCHEDULER', '管理调度器权限', 185),
            ('oracle', 'system_privileges', 'CREATE ANY EVALUATION CONTEXT', '创建任意评估上下文权限', 186),
            ('oracle', 'system_privileges', 'DROP ANY EVALUATION CONTEXT', '删除任意评估上下文权限', 187),
            ('oracle', 'system_privileges', 'CREATE ANY RULE SET', '创建任意规则集权限', 188),
            ('oracle', 'system_privileges', 'ALTER ANY RULE SET', '修改任意规则集权限', 189),
            ('oracle', 'system_privileges', 'DROP ANY RULE SET', '删除任意规则集权限', 190),
            ('oracle', 'system_privileges', 'CREATE ANY RULE', '创建任意规则权限', 191),
            ('oracle', 'system_privileges', 'ALTER ANY RULE', '修改任意规则权限', 192),
            ('oracle', 'system_privileges', 'DROP ANY RULE', '删除任意规则权限', 193),
            ('oracle', 'system_privileges', 'CREATE ANY MINING MODEL', '创建任意挖掘模型权限', 194),
            ('oracle', 'system_privileges', 'ALTER ANY MINING MODEL', '修改任意挖掘模型权限', 195),
            ('oracle', 'system_privileges', 'DROP ANY MINING MODEL', '删除任意挖掘模型权限', 196),
            ('oracle', 'system_privileges', 'SELECT ANY MINING MODEL', '查询任意挖掘模型权限', 197),
            ('oracle', 'system_privileges', 'CREATE ANY SQL PROFILE', '创建任意SQL配置文件权限', 198),
            ('oracle', 'system_privileges', 'ALTER ANY SQL PROFILE', '修改任意SQL配置文件权限', 199),
            ('oracle', 'system_privileges', 'DROP ANY SQL PROFILE', '删除任意SQL配置文件权限', 200),
            ('oracle', 'system_privileges', 'CREATE ANY SQL PLAN BASELINE', '创建任意SQL计划基线权限', 201),
            ('oracle', 'system_privileges', 'ALTER ANY SQL PLAN BASELINE', '修改任意SQL计划基线权限', 202),
            ('oracle', 'system_privileges', 'DROP ANY SQL PLAN BASELINE', '删除任意SQL计划基线权限', 203),
            ('oracle', 'system_privileges', 'CREATE ANY SQL PATCH', '创建任意SQL补丁权限', 204),
            ('oracle', 'system_privileges', 'ALTER ANY SQL PATCH', '修改任意SQL补丁权限', 205),
            ('oracle', 'system_privileges', 'DROP ANY SQL PATCH', '删除任意SQL补丁权限', 206),
            ('oracle', 'system_privileges', 'CREATE ANY EDITION', '创建任意版本权限', 207),
            ('oracle', 'system_privileges', 'DROP ANY EDITION', '删除任意版本权限', 208),
            ('oracle', 'system_privileges', 'USE ANY EDITION', '使用任意版本权限', 209),
            ('oracle', 'system_privileges', 'ALTER SYSTEM', '修改系统权限', 210),
            ('oracle', 'system_privileges', 'ALTER DATABASE', '修改数据库权限', 211),
            ('oracle', 'system_privileges', 'CREATE DATABASE', '创建数据库权限', 212),
            ('oracle', 'system_privileges', 'DROP DATABASE', '删除数据库权限', 213),
            ('oracle', 'system_privileges', 'CREATE SPFILE', '创建SPFILE权限', 214),
            ('oracle', 'system_privileges', 'ALTER SPFILE', '修改SPFILE权限', 215),
            ('oracle', 'system_privileges', 'CREATE PFILE', '创建PFILE权限', 216),
            ('oracle', 'system_privileges', 'CREATE CONTROLFILE', '创建控制文件权限', 217),
            ('oracle', 'system_privileges', 'ALTER CONTROLFILE', '修改控制文件权限', 218),
            ('oracle', 'system_privileges', 'CREATE RESTORE POINT', '创建还原点权限', 219),
            ('oracle', 'system_privileges', 'DROP RESTORE POINT', '删除还原点权限', 220),
            ('oracle', 'system_privileges', 'FLASHBACK ANY TABLE', '闪回任意表权限', 221),
            ('oracle', 'system_privileges', 'BACKUP ANY TABLE', '备份任意表权限', 222),
            ('oracle', 'system_privileges', 'RESTORE ANY TABLE', '还原任意表权限', 223),
            ('oracle', 'system_privileges', 'RECOVER ANY TABLE', '恢复任意表权限', 224),
            ('oracle', 'system_privileges', 'LOGMINING', '日志挖掘权限', 225),
            ('oracle', 'system_privileges', 'SELECT ANY TRANSACTION', '查询任意事务权限', 226),
            ('oracle', 'system_privileges', 'LOCK ANY TABLE', '锁定任意表权限', 227),
            ('oracle', 'system_privileges', 'COMMENT ANY TABLE', '注释任意表权限', 228),
            ('oracle', 'system_privileges', 'COMMENT ANY COLUMN', '注释任意列权限', 229),
            ('oracle', 'system_privileges', 'GRANT ANY OBJECT PRIVILEGE', '授予任意对象权限', 230),
            ('oracle', 'system_privileges', 'EXEMPT ANY POLICY', '豁免任意策略权限', 231),
            ('oracle', 'system_privileges', 'EXEMPT IDENTITY POLICY', '豁免身份策略权限', 232),
            ('oracle', 'system_privileges', 'EXEMPT RESOURCE LIMITS', '豁免资源限制权限', 233),
            ('oracle', 'system_privileges', 'EXEMPT CONNECT IDENTIFIER', '豁免连接标识符权限', 234),
            ('oracle', 'system_privileges', 'EXEMPT DDL LOGGING', '豁免DDL日志记录权限', 235),
            ('oracle', 'system_privileges', 'EXEMPT DML LOGGING', '豁免DML日志记录权限', 236),
            # 对象权限
            ('oracle', 'object_privileges', 'SELECT', '查询权限', 1),
            ('oracle', 'object_privileges', 'INSERT', '插入权限', 2),
            ('oracle', 'object_privileges', 'UPDATE', '更新权限', 3),
            ('oracle', 'object_privileges', 'DELETE', '删除权限', 4),
            ('oracle', 'object_privileges', 'ALTER', '修改权限', 5),
            ('oracle', 'object_privileges', 'INDEX', '索引权限', 6),
            ('oracle', 'object_privileges', 'REFERENCES', '引用权限', 7),
            ('oracle', 'object_privileges', 'EXECUTE', '执行权限', 8),
            ('oracle', 'object_privileges', 'DEBUG', '调试权限', 9),
            ('oracle', 'object_privileges', 'FLASHBACK', '闪回权限', 10),
            ('oracle', 'object_privileges', 'ON COMMIT REFRESH', '提交时刷新权限', 11),
            ('oracle', 'object_privileges', 'QUERY REWRITE', '查询重写权限', 12),
            ('oracle', 'object_privileges', 'UNDER', '继承权限', 13),
            ('oracle', 'object_privileges', 'WRITE', '写入权限', 14),
            ('oracle', 'object_privileges', 'READ', '读取权限', 15),
            # 表空间配额权限
            ('oracle', 'tablespace_quotas', 'UNLIMITED', '无限制表空间配额', 1),
            ('oracle', 'tablespace_quotas', 'DEFAULT', '默认表空间配额', 2),
            ('oracle', 'tablespace_quotas', 'QUOTA', '指定大小表空间配额', 3),
            ('oracle', 'tablespace_quotas', 'NO QUOTA', '无表空间配额', 4),
        ]
        
        # 批量插入权限配置
        all_permissions = mysql_permissions + sqlserver_permissions + oracle_permissions
        
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
