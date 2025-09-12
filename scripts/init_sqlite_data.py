#!/usr/bin/env python3
"""
SQLite 数据库数据初始化脚本
基于 init_postgresql.sql 文档插入初始数据
"""

import os
import sqlite3
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def init_sqlite_data():
    """初始化 SQLite 数据库数据"""

    # 数据库文件路径
    db_path = "userdata/taifish_dev.db"

    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在，请先运行 init_sqlite_from_postgresql.py")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 开始插入初始数据...")

    try:
        # 1. 插入用户数据
        print("👤 插入用户数据...")
        users_data = [
            (1, 'admin', '$2b$12$DKFZJIArZQ0ASgxpcGyrHeAXYTBS0ThJjewzso1BnQQm7UWdomcAu', 'admin', '2025-09-12 00:25:19.014781', None, True),
            (2, 'jinxj', '$2b$12$MFRYxABcpq2UCv1aC22KLuZ88TO0ICM53jIunXNz5C.L7IaOm.Ca.', 'user', '2025-09-12 04:55:11.168860', None, True)
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO users (id, username, password, role, created_at, last_login, is_active) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', users_data)

        # 2. 插入数据库类型配置数据
        print("🗄️ 插入数据库类型配置数据...")
        db_types_data = [
            (1, 'mysql', 'MySQL', 'pymysql', 3306, 'mysql', 30, 'MySQL数据库', 'fa-database', 'primary', '["replication", "partitioning", "json"]', True, True, 1, '2025-09-12 02:02:33.898448', '2025-09-12 03:02:58.406875'),
            (2, 'postgresql', 'PostgreSQL', 'psycopg', 5432, 'postgres', 30, 'PostgreSQL数据库', 'fa-database', 'info', '["jsonb", "arrays", "full_text_search"]', True, True, 2, '2025-09-12 02:02:33.899255', '2025-09-12 03:06:59.898296'),
            (3, 'sqlserver', 'SQL Server', 'pymssql', 1433, 'master', 30, 'Microsoft SQL Server数据库', 'fa-database', 'danger', '["clustering", "mirroring", "always_on"]', True, True, 3, '2025-09-12 02:02:33.899542', '2025-09-12 03:08:49.557828'),
            (4, 'oracle', 'Oracle', 'oracledb', 1521, 'orcl', 30, 'Oracle数据库', 'fa-database', 'warning', '["rac", "asm", "flashback"]', True, True, 4, '2025-09-12 02:02:33.899757', '2025-09-12 03:02:58.407992')
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO database_type_configs 
        (id, name, display_name, driver, default_port, default_schema, connection_timeout, 
         description, icon, color, features, is_active, is_system, sort_order, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', db_types_data)

        # 3. 插入账户分类数据
        print("🏷️ 插入账户分类数据...")
        classifications_data = [
            (2, '敏感账户', '可授权特定权限以满足业务需求，同时需严格安全控制', 'high', '#fd7e14', 80, True, True, '2025-09-12 00:44:16.876132', '2025-09-12 05:28:53.681826'),
            (4, '风险账户', '可用于删除库和表的操作，需特别监控以防止误删或恶意行为', 'medium', '#bf17fd', 70, True, True, '2025-09-12 00:44:16.876198', '2025-09-12 05:27:36.043494'),
            (5, '只读用户', None, 'critical', '#69dc38', 50, True, True, '2025-09-12 00:44:16.876219', '2025-09-12 05:29:01.826658'),
            (7, '特权账户', '用于具有高级权限的管理员或系统账户，负责管理数据库核心操作', 'critical', '#dc3545', 90, True, True, '2025-09-12 00:44:16.876259', '2025-09-12 05:26:04.919677'),
            (8, '普通账户', '用于日常操作的普通用户账户，权限范围有限', 'low', '#3c49fb', 60, True, True, '2025-09-12 00:44:16.876276', '2025-09-12 05:27:45.250653')
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO account_classifications 
        (id, name, description, risk_level, color, priority, is_system, is_active, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', classifications_data)

        # 4. 插入分类规则数据
        print("📋 插入分类规则数据...")
        rules_data = [
            (2, 2, 'oracle', 'oracle_super_rule', '{"type": "oracle_permissions", "roles": ["DBA"], "system_privileges": [], "tablespace_privileges": [], "tablespace_quotas": [], "operator": "OR"}', True, '2025-09-12 00:44:16.879297', '2025-09-12 06:08:14.494067'),
            (4, 4, 'postgresql', 'postgresql_grant_rule', '{"type": "postgresql_permissions", "role_attributes": ["CREATEROLE"], "database_privileges": [], "tablespace_privileges": [], "operator": "OR"}', True, '2025-09-12 00:44:16.879795', '2025-09-12 06:03:24.239989'),
            (5, 7, 'mysql', 'mysql_super_rule', '{"type": "mysql_permissions", "global_privileges": ["SUPER"], "database_privileges": [], "operator": "OR"}', True, '2025-09-12 00:44:16.880022', '2025-09-12 05:31:38.194297'),
            (7, 7, 'sqlserver', 'sqlserver_super_rule', '{"type": "sqlserver_permissions", "server_roles": ["sysadmin"], "server_permissions": [], "database_roles": [], "database_privileges": [], "operator": "OR"}', True, '2025-09-12 00:44:16.880470', '2025-09-12 05:39:51.998024'),
            (8, 2, 'sqlserver', 'sqlserver_grant_rule', '{"type": "sqlserver_permissions", "server_roles": ["securityadmin"], "server_permissions": [], "database_roles": [], "database_privileges": [], "operator": "OR"}', True, '2025-09-12 00:44:16.880657', '2025-09-12 06:00:46.901211'),
            (9, 2, 'mysql', 'mysql_grant_rule', '{"type": "mysql_permissions", "global_privileges": ["GRANT OPTION"], "database_privileges": [], "operator": "OR"}', True, '2025-09-12 05:34:11.813260', '2025-09-12 05:34:11.813269'),
            (10, 4, 'mysql', 'mysql_delete_rule', '{"type": "mysql_permissions", "global_privileges": ["DROP"], "database_privileges": ["DROP"], "operator": "OR"}', True, '2025-09-12 05:34:53.465284', '2025-09-12 05:34:53.465291'),
            (11, 4, 'sqlserver', 'sqlserver_delete_rule', '{"type": "sqlserver_permissions", "server_roles": [], "server_permissions": ["ALTER ANY DATABASE"], "database_roles": ["db_owner"], "database_privileges": ["DELETE"], "operator": "OR"}', True, '2025-09-12 06:01:31.340355', '2025-09-12 06:01:31.340362'),
            (12, 7, 'postgresql', 'postgresql_super_rule', '{"type": "postgresql_permissions", "role_attributes": ["SUPERUSER"], "database_privileges": [], "tablespace_privileges": [], "permissions": ["SUPERUSER"], "operator": "OR"}', True, '2025-09-12 06:03:41.681866', '2025-09-12 06:03:41.681870')
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO classification_rules 
        (id, classification_id, db_type, rule_name, rule_expression, is_active, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', rules_data)

        # 5. 插入权限配置数据 - MySQL
        print("🔐 插入MySQL权限配置数据...")
        mysql_permissions = [
            # MySQL 全局权限
            ('mysql', 'global_privileges', 'ALTER', '修改表结构', True, 1),
            ('mysql', 'global_privileges', 'ALTER ROUTINE', '修改存储过程和函数', True, 2),
            ('mysql', 'global_privileges', 'CREATE', '创建数据库和表', True, 3),
            ('mysql', 'global_privileges', 'CREATE ROUTINE', '创建存储过程和函数', True, 4),
            ('mysql', 'global_privileges', 'CREATE TEMPORARY TABLES', '创建临时表', True, 5),
            ('mysql', 'global_privileges', 'CREATE USER', '创建用户权限', True, 6),
            ('mysql', 'global_privileges', 'CREATE VIEW', '创建视图', True, 7),
            ('mysql', 'global_privileges', 'DELETE', '删除数据', True, 8),
            ('mysql', 'global_privileges', 'DROP', '删除数据库和表', True, 9),
            ('mysql', 'global_privileges', 'EVENT', '创建、修改、删除事件', True, 10),
            ('mysql', 'global_privileges', 'EXECUTE', '执行存储过程和函数', True, 11),
            ('mysql', 'global_privileges', 'FILE', '文件操作权限', True, 12),
            ('mysql', 'global_privileges', 'GRANT OPTION', '授权权限，可以授予其他用户权限', True, 13),
            ('mysql', 'global_privileges', 'INDEX', '创建和删除索引', True, 14),
            ('mysql', 'global_privileges', 'INSERT', '插入数据', True, 15),
            ('mysql', 'global_privileges', 'LOCK TABLES', '锁定表', True, 16),
            ('mysql', 'global_privileges', 'PROCESS', '查看所有进程', True, 17),
            ('mysql', 'global_privileges', 'REFERENCES', '引用权限', True, 18),
            ('mysql', 'global_privileges', 'RELOAD', '重载权限表', True, 19),
            ('mysql', 'global_privileges', 'REPLICATION CLIENT', '复制客户端权限', True, 20),
            ('mysql', 'global_privileges', 'REPLICATION SLAVE', '复制从库权限', True, 21),
            ('mysql', 'global_privileges', 'SELECT', '查询数据', True, 22),
            ('mysql', 'global_privileges', 'SHOW DATABASES', '显示所有数据库', True, 23),
            ('mysql', 'global_privileges', 'SHOW VIEW', '显示视图', True, 24),
            ('mysql', 'global_privileges', 'SHUTDOWN', '关闭MySQL服务器', True, 25),
            ('mysql', 'global_privileges', 'SUPER', '超级权限，可以执行任何操作', True, 26),
            ('mysql', 'global_privileges', 'TRIGGER', '创建和删除触发器', True, 27),
            ('mysql', 'global_privileges', 'UPDATE', '更新数据', True, 28),
            ('mysql', 'global_privileges', 'USAGE', '无权限，仅用于连接', True, 29),
            # MySQL 数据库权限
            ('mysql', 'database_privileges', 'CREATE', '创建数据库和表', True, 1),
            ('mysql', 'database_privileges', 'DROP', '删除数据库和表', True, 2),
            ('mysql', 'database_privileges', 'ALTER', '修改数据库和表结构', True, 3),
            ('mysql', 'database_privileges', 'INDEX', '创建和删除索引', True, 4),
            ('mysql', 'database_privileges', 'INSERT', '插入数据', True, 5),
            ('mysql', 'database_privileges', 'UPDATE', '更新数据', True, 6),
            ('mysql', 'database_privileges', 'DELETE', '删除数据', True, 7),
            ('mysql', 'database_privileges', 'SELECT', '查询数据', True, 8),
            ('mysql', 'database_privileges', 'CREATE TEMPORARY TABLES', '创建临时表', True, 9),
            ('mysql', 'database_privileges', 'LOCK TABLES', '锁定表', True, 10),
            ('mysql', 'database_privileges', 'EXECUTE', '执行存储过程和函数', True, 11),
            ('mysql', 'database_privileges', 'CREATE VIEW', '创建视图', True, 12),
            ('mysql', 'database_privileges', 'SHOW VIEW', '显示视图', True, 13),
            ('mysql', 'database_privileges', 'CREATE ROUTINE', '创建存储过程和函数', True, 14),
            ('mysql', 'database_privileges', 'ALTER ROUTINE', '修改存储过程和函数', True, 15),
            ('mysql', 'database_privileges', 'EVENT', '创建、修改、删除事件', True, 16),
            ('mysql', 'database_privileges', 'TRIGGER', '创建和删除触发器', True, 17)
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO permission_configs 
        (db_type, category, permission_name, description, is_active, sort_order) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', mysql_permissions)

        # 6. 插入权限配置数据 - PostgreSQL
        print("🔐 插入PostgreSQL权限配置数据...")
        postgresql_permissions = [
            # PostgreSQL 数据库权限
            ('postgresql', 'database_privileges', 'CONNECT', '连接数据库权限', True, 1),
            ('postgresql', 'database_privileges', 'CREATE', '创建对象权限', True, 2),
            ('postgresql', 'database_privileges', 'TEMPORARY', '创建临时表权限', True, 3),
            ('postgresql', 'database_privileges', 'TEMP', '创建临时表权限（别名）', True, 4),
            # PostgreSQL 预定义角色
            ('postgresql', 'predefined_roles', 'SUPERUSER', '超级用户角色，拥有所有权限', True, 1),
            ('postgresql', 'predefined_roles', 'CREATEDB', '创建数据库角色', True, 2),
            ('postgresql', 'predefined_roles', 'CREATEROLE', '创建角色角色', True, 3),
            ('postgresql', 'predefined_roles', 'INHERIT', '继承权限角色', True, 4),
            ('postgresql', 'predefined_roles', 'LOGIN', '登录角色', True, 5),
            ('postgresql', 'predefined_roles', 'REPLICATION', '复制角色', True, 6),
            ('postgresql', 'predefined_roles', 'BYPASSRLS', '绕过行级安全角色', True, 7),
            ('postgresql', 'predefined_roles', 'CONNECTION LIMIT', '连接限制角色', True, 8),
            ('postgresql', 'predefined_roles', 'PASSWORD', '密码角色', True, 9),
            ('postgresql', 'predefined_roles', 'VALID UNTIL', '有效期角色', True, 10),
            # PostgreSQL 表空间权限
            ('postgresql', 'tablespace_privileges', 'CREATE', '创建表空间权限', True, 1),
            ('postgresql', 'tablespace_privileges', 'USAGE', '使用表空间权限', True, 2)
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO permission_configs 
        (db_type, category, permission_name, description, is_active, sort_order) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', postgresql_permissions)

        # 7. 插入权限配置数据 - SQL Server
        print("🔐 插入SQL Server权限配置数据...")
        sqlserver_permissions = [
            # SQL Server 数据库权限
            ('sqlserver', 'database_privileges', 'SELECT', '查询数据', True, 1),
            ('sqlserver', 'database_privileges', 'INSERT', '插入数据', True, 2),
            ('sqlserver', 'database_privileges', 'UPDATE', '更新数据', True, 3),
            ('sqlserver', 'database_privileges', 'DELETE', '删除数据', True, 4),
            ('sqlserver', 'database_privileges', 'CREATE', '创建对象', True, 5),
            ('sqlserver', 'database_privileges', 'ALTER', '修改/删除对象（包含DROP功能）', True, 6),
            ('sqlserver', 'database_privileges', 'EXECUTE', '执行存储过程', True, 7),
            ('sqlserver', 'database_privileges', 'CONTROL', '完全控制权限', True, 8),
            ('sqlserver', 'database_privileges', 'REFERENCES', '引用权限', True, 9),
            ('sqlserver', 'database_privileges', 'VIEW DEFINITION', '查看定义', True, 10),
            ('sqlserver', 'database_privileges', 'TAKE OWNERSHIP', '获取所有权', True, 11),
            ('sqlserver', 'database_privileges', 'IMPERSONATE', '模拟权限', True, 12),
            ('sqlserver', 'database_privileges', 'CREATE SCHEMA', '创建架构', True, 13),
            ('sqlserver', 'database_privileges', 'ALTER ANY SCHEMA', '修改任意架构', True, 14),
            ('sqlserver', 'database_privileges', 'CREATE TABLE', '创建表', True, 15),
            ('sqlserver', 'database_privileges', 'CREATE VIEW', '创建视图', True, 16),
            ('sqlserver', 'database_privileges', 'CREATE PROCEDURE', '创建存储过程', True, 17),
            ('sqlserver', 'database_privileges', 'CREATE FUNCTION', '创建函数', True, 18),
            ('sqlserver', 'database_privileges', 'CREATE TRIGGER', '创建触发器', True, 19),
            # SQL Server 服务器角色
            ('sqlserver', 'server_roles', 'sysadmin', '系统管理员', True, 1),
            ('sqlserver', 'server_roles', 'serveradmin', '服务器管理员', True, 2),
            ('sqlserver', 'server_roles', 'securityadmin', '安全管理员', True, 3),
            ('sqlserver', 'server_roles', 'processadmin', '进程管理员', True, 4),
            ('sqlserver', 'server_roles', 'setupadmin', '设置管理员', True, 5),
            ('sqlserver', 'server_roles', 'bulkadmin', '批量操作管理员', True, 6),
            ('sqlserver', 'server_roles', 'diskadmin', '磁盘管理员', True, 7),
            ('sqlserver', 'server_roles', 'dbcreator', '数据库创建者', True, 8),
            ('sqlserver', 'server_roles', 'public', '公共角色', True, 9),
            # SQL Server 数据库角色
            ('sqlserver', 'database_roles', 'db_owner', '数据库所有者', True, 1),
            ('sqlserver', 'database_roles', 'db_accessadmin', '访问管理员', True, 2),
            ('sqlserver', 'database_roles', 'db_securityadmin', '安全管理员', True, 3),
            ('sqlserver', 'database_roles', 'db_ddladmin', 'DDL管理员', True, 4),
            ('sqlserver', 'database_roles', 'db_backupoperator', '备份操作员', True, 5),
            ('sqlserver', 'database_roles', 'db_datareader', '数据读取者', True, 6),
            ('sqlserver', 'database_roles', 'db_datawriter', '数据写入者', True, 7),
            ('sqlserver', 'database_roles', 'db_denydatareader', '拒绝数据读取', True, 8),
            ('sqlserver', 'database_roles', 'db_denydatawriter', '拒绝数据写入', True, 9),
            # SQL Server 服务器权限
            ('sqlserver', 'server_permissions', 'CONTROL SERVER', '控制服务器', True, 1),
            ('sqlserver', 'server_permissions', 'ALTER ANY LOGIN', '修改任意登录', True, 2),
            ('sqlserver', 'server_permissions', 'ALTER ANY SERVER ROLE', '修改任意服务器角色', True, 3),
            ('sqlserver', 'server_permissions', 'CREATE ANY DATABASE', '创建任意数据库', True, 4),
            ('sqlserver', 'server_permissions', 'ALTER ANY DATABASE', '修改任意数据库', True, 5),
            ('sqlserver', 'server_permissions', 'VIEW SERVER STATE', '查看服务器状态', True, 6),
            ('sqlserver', 'server_permissions', 'ALTER SERVER STATE', '修改服务器状态', True, 7),
            ('sqlserver', 'server_permissions', 'ALTER SETTINGS', '修改设置', True, 8),
            ('sqlserver', 'server_permissions', 'ALTER TRACE', '修改跟踪', True, 9),
            ('sqlserver', 'server_permissions', 'AUTHENTICATE SERVER', '服务器身份验证', True, 10),
            ('sqlserver', 'server_permissions', 'BACKUP DATABASE', '备份数据库', True, 11),
            ('sqlserver', 'server_permissions', 'BACKUP LOG', '备份日志', True, 12),
            ('sqlserver', 'server_permissions', 'CHECKPOINT', '检查点', True, 13),
            ('sqlserver', 'server_permissions', 'CONNECT SQL', '连接SQL', True, 14),
            ('sqlserver', 'server_permissions', 'SHUTDOWN', '关闭服务器', True, 15),
            ('sqlserver', 'server_permissions', 'IMPERSONATE ANY LOGIN', '模拟任意登录', True, 16),
            ('sqlserver', 'server_permissions', 'VIEW ANY DEFINITION', '查看任意定义', True, 17)
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO permission_configs 
        (db_type, category, permission_name, description, is_active, sort_order) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', sqlserver_permissions)

        # 8. 插入权限配置数据 - Oracle
        print("🔐 插入Oracle权限配置数据...")
        oracle_permissions = [
            # Oracle 系统权限 (前20个)
            ('oracle', 'system_privileges', 'CREATE SESSION', '创建会话权限', True, 1),
            ('oracle', 'system_privileges', 'CREATE USER', '创建用户权限', True, 2),
            ('oracle', 'system_privileges', 'ALTER USER', '修改用户权限', True, 3),
            ('oracle', 'system_privileges', 'DROP USER', '删除用户权限', True, 4),
            ('oracle', 'system_privileges', 'CREATE ROLE', '创建角色权限', True, 5),
            ('oracle', 'system_privileges', 'ALTER ROLE', '修改角色权限', True, 6),
            ('oracle', 'system_privileges', 'DROP ROLE', '删除角色权限', True, 7),
            ('oracle', 'system_privileges', 'GRANT ANY PRIVILEGE', '授予任意权限', True, 8),
            ('oracle', 'system_privileges', 'GRANT ANY ROLE', '授予任意角色', True, 9),
            ('oracle', 'system_privileges', 'CREATE TABLE', '创建表权限', True, 10),
            ('oracle', 'system_privileges', 'CREATE ANY TABLE', '创建任意表权限', True, 11),
            ('oracle', 'system_privileges', 'ALTER ANY TABLE', '修改任意表权限', True, 12),
            ('oracle', 'system_privileges', 'DROP ANY TABLE', '删除任意表权限', True, 13),
            ('oracle', 'system_privileges', 'SELECT ANY TABLE', '查询任意表权限', True, 14),
            ('oracle', 'system_privileges', 'INSERT ANY TABLE', '插入任意表权限', True, 15),
            ('oracle', 'system_privileges', 'UPDATE ANY TABLE', '更新任意表权限', True, 16),
            ('oracle', 'system_privileges', 'DELETE ANY TABLE', '删除任意表权限', True, 17),
            ('oracle', 'system_privileges', 'CREATE INDEX', '创建索引权限', True, 18),
            ('oracle', 'system_privileges', 'CREATE ANY INDEX', '创建任意索引权限', True, 19),
            ('oracle', 'system_privileges', 'ALTER ANY INDEX', '修改任意索引权限', True, 20),
            # Oracle 预定义角色
            ('oracle', 'roles', 'CONNECT', '连接角色，基本连接权限', True, 1),
            ('oracle', 'roles', 'RESOURCE', '资源角色，创建对象权限', True, 2),
            ('oracle', 'roles', 'DBA', '数据库管理员角色，所有系统权限', True, 3),
            ('oracle', 'roles', 'EXP_FULL_DATABASE', '导出完整数据库角色', True, 4),
            ('oracle', 'roles', 'IMP_FULL_DATABASE', '导入完整数据库角色', True, 5),
            ('oracle', 'roles', 'RECOVERY_CATALOG_OWNER', '恢复目录所有者角色', True, 6),
            ('oracle', 'roles', 'AUDIT_ADMIN', '审计管理员角色', True, 7),
            ('oracle', 'roles', 'AUDIT_VIEWER', '审计查看者角色', True, 8),
            ('oracle', 'roles', 'AUTHENTICATEDUSER', '认证用户角色', True, 9),
            ('oracle', 'roles', 'AQ_ADMINISTRATOR_ROLE', '高级队列管理员角色', True, 10),
            # Oracle 表空间权限
            ('oracle', 'tablespace_privileges', 'CREATE TABLESPACE', '创建表空间权限', True, 1),
            ('oracle', 'tablespace_privileges', 'ALTER TABLESPACE', '修改表空间权限', True, 2),
            ('oracle', 'tablespace_privileges', 'DROP TABLESPACE', '删除表空间权限', True, 3),
            ('oracle', 'tablespace_privileges', 'MANAGE TABLESPACE', '管理表空间权限', True, 4),
            ('oracle', 'tablespace_privileges', 'UNLIMITED TABLESPACE', '无限制表空间权限', True, 5),
            # Oracle 表空间配额
            ('oracle', 'tablespace_quotas', 'UNLIMITED', '无限制表空间配额', True, 1),
            ('oracle', 'tablespace_quotas', 'DEFAULT', '默认表空间配额', True, 2),
            ('oracle', 'tablespace_quotas', 'QUOTA', '指定大小表空间配额', True, 3),
            ('oracle', 'tablespace_quotas', 'NO QUOTA', '无表空间配额', True, 4),
            ('oracle', 'tablespace_quotas', 'QUOTA 1M', '1MB表空间配额', True, 5)
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO permission_configs 
        (db_type, category, permission_name, description, is_active, sort_order) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', oracle_permissions)

        # 9. 插入任务数据
        print("⏰ 插入任务数据...")
        tasks_data = [
            (1, 'account_sync', 'sync_accounts', 'mysql', '*/5 * * * *', '测试',
             '''# 账户同步任务 - MySQL                                       
# 此任务将使用统一的AccountSyncService进行账户同步
# 无需手动编写代码，系统会自动调用相应的服务

def sync_mysql_accounts(instance, config):
    """同步MySQL数据库账户信息 - 使用统一服务"""
    from app.services.account_sync_service import account_sync_service                                            
    
    # 调用统一的账户同步服务
    result = account_sync_service.sync_accounts(instance, sync_type='task')                                       
    return result''',
             '{}', True, False, None, None, None, None, 0, 0, '2025-09-12 01:20:05.772007', '2025-09-12 01:20:05.772013')
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO tasks 
        (id, name, task_type, db_type, schedule, description, python_code, config, 
         is_active, is_builtin, last_run, last_run_at, last_status, last_message, 
         run_count, success_count, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tasks_data)

        # 10. 插入全局参数数据
        print("⚙️ 插入全局参数数据...")
        global_params_data = [
            ('system_name', '泰摸鱼吧', '系统名称', 'string', True),
            ('system_version', '2.0.0', '系统版本', 'string', True),
            ('max_login_attempts', '5', '最大登录尝试次数', 'integer', True),
            ('session_timeout', '3600', '会话超时时间（秒）', 'integer', True),
            ('default_page_size', '20', '默认分页大小', 'integer', True),
            ('enable_audit_log', 'true', '启用审计日志', 'boolean', True),
            ('backup_retention_days', '30', '备份保留天数', 'integer', True),
            ('sync_interval_minutes', '5', '同步间隔（分钟）', 'integer', True)
        ]

        cursor.executemany('''
        INSERT OR IGNORE INTO global_params 
        (name, value, description, param_type, is_active) 
        VALUES (?, ?, ?, ?, ?)
        ''', global_params_data)

        # 提交事务
        conn.commit()
        print("✅ 初始数据插入完成！")

        # 验证数据
        print("\n📊 数据验证:")
        tables = ['users', 'database_type_configs', 'account_classifications',
                 'classification_rules', 'permission_configs', 'tasks', 'global_params']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} 条记录")

        print("\n🎉 SQLite 数据库数据初始化完成！")

    except Exception as e:
        print(f"❌ 数据插入失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    init_sqlite_data()
