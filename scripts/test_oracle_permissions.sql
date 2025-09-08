-- =============================================
-- Oracle 权限测试脚本
-- 泰摸鱼吧 - 数据同步管理平台
-- =============================================

-- 此脚本用于测试当前用户是否具有泰摸鱼吧系统所需的权限

SELECT '=============================================' AS "" FROM DUAL;
SELECT 'Oracle 权限测试开始...' AS "" FROM DUAL;
SELECT '当前用户: ' || USER AS "" FROM DUAL;
SELECT '当前数据库: ' || SYS_CONTEXT('USERENV', 'DB_NAME') AS "" FROM DUAL;
SELECT '=============================================' AS "" FROM DUAL;

-- 1. 测试连接权限
SELECT '1. 测试连接权限...' AS "" FROM DUAL;
SELECT '连接测试成功' AS 结果, banner AS 版本信息 FROM v$version WHERE rownum = 1;

-- 2. 测试DBA_USERS表访问
SELECT '2. 测试DBA_USERS表访问...' AS "" FROM DUAL;
SELECT 'DBA_USERS表测试' AS 结果, COUNT(*) AS 可访问的用户数量 FROM dba_users;

-- 3. 测试DBA_ROLES表访问
SELECT '3. 测试DBA_ROLES表访问...' AS "" FROM DUAL;
SELECT 'DBA_ROLES表测试' AS 结果, COUNT(*) AS 可访问的角色数量 FROM dba_roles;

-- 4. 测试DBA_ROLE_PRIVS表访问
SELECT '4. 测试DBA_ROLE_PRIVS表访问...' AS "" FROM DUAL;
SELECT 'DBA_ROLE_PRIVS表测试' AS 结果, COUNT(*) AS 可访问的角色权限数量 FROM dba_role_privs;

-- 5. 测试DBA_SYS_PRIVS表访问
SELECT '5. 测试DBA_SYS_PRIVS表访问...' AS "" FROM DUAL;
SELECT 'DBA_SYS_PRIVS表测试' AS 结果, COUNT(*) AS 可访问的系统权限数量 FROM dba_sys_privs;

-- 6. 测试DBA_TAB_PRIVS表访问
SELECT '6. 测试DBA_TAB_PRIVS表访问...' AS "" FROM DUAL;
SELECT 'DBA_TAB_PRIVS表测试' AS 结果, COUNT(*) AS 可访问的表权限数量 FROM dba_tab_privs;

-- 7. 测试DBA_COL_PRIVS表访问
SELECT '7. 测试DBA_COL_PRIVS表访问...' AS "" FROM DUAL;
SELECT 'DBA_COL_PRIVS表测试' AS 结果, COUNT(*) AS 可访问的列权限数量 FROM dba_col_privs;

-- 8. 测试DBA_PROXY_USERS表访问
SELECT '8. 测试DBA_PROXY_USERS表访问...' AS "" FROM DUAL;
SELECT 'DBA_PROXY_USERS表测试' AS 结果, COUNT(*) AS 可访问的代理用户数量 FROM dba_proxy_users;

-- 9. 测试V$视图访问（可选）
SELECT '9. 测试V$视图访问（可选）...' AS "" FROM DUAL;
SELECT 'V$SESSION表测试' AS 结果, COUNT(*) AS 可访问的会话数量 FROM v$session;
SELECT 'V$INSTANCE表测试' AS 结果, COUNT(*) AS 可访问的实例信息数量 FROM v$instance;
SELECT 'V$DATABASE表测试' AS 结果, COUNT(*) AS 可访问的数据库信息数量 FROM v$database;

-- 10. 显示当前用户权限摘要
SELECT '=============================================' AS "" FROM DUAL;
SELECT '当前用户权限摘要:' AS "" FROM DUAL;

-- 显示用户信息
SELECT 
    '用户信息' AS 权限类型,
    username AS 用户名,
    account_status AS 账户状态,
    created AS 创建时间,
    expiry_date AS 过期时间,
    profile AS 配置文件
FROM dba_users 
WHERE username = USER;

-- 显示角色权限
SELECT 
    '角色权限' AS 权限类型,
    grantee AS 被授权者,
    granted_role AS 角色名,
    admin_option AS 管理选项,
    default_role AS 默认角色
FROM dba_role_privs
WHERE grantee = USER
ORDER BY granted_role;

-- 显示系统权限
SELECT 
    '系统权限' AS 权限类型,
    grantee AS 被授权者,
    privilege AS 权限名称,
    admin_option AS 管理选项
FROM dba_sys_privs
WHERE grantee = USER
ORDER BY privilege;

-- 显示表权限
SELECT 
    '表权限' AS 权限类型,
    grantee AS 被授权者,
    owner AS 所有者,
    table_name AS 表名,
    privilege AS 权限名称,
    grantable AS 可授权
FROM dba_tab_privs
WHERE grantee = USER
ORDER BY owner, table_name, privilege;

-- 显示列权限
SELECT 
    '列权限' AS 权限类型,
    grantee AS 被授权者,
    owner AS 所有者,
    table_name AS 表名,
    column_name AS 列名,
    privilege AS 权限名称,
    grantable AS 可授权
FROM dba_col_privs
WHERE grantee = USER
ORDER BY owner, table_name, column_name, privilege;

-- 显示代理用户权限
SELECT 
    '代理用户权限' AS 权限类型,
    client AS 客户端,
    proxy AS 代理,
    authentication AS 认证方式,
    authorization AS 授权方式
FROM dba_proxy_users
WHERE client = USER OR proxy = USER
ORDER BY client, proxy;

SELECT '=============================================' AS "" FROM DUAL;
SELECT '权限测试完成！' AS "" FROM DUAL;
SELECT '=============================================' AS "" FROM DUAL;
