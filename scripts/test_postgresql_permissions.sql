-- =============================================
-- PostgreSQL 权限测试脚本
-- 泰摸鱼吧 - 数据同步管理平台
-- =============================================

-- 此脚本用于测试当前用户是否具有泰摸鱼吧系统所需的权限

SELECT '=============================================' AS "";
SELECT 'PostgreSQL 权限测试开始...' AS "";
SELECT '当前用户: ' || current_user AS "";
SELECT '当前数据库: ' || current_database() AS "";
SELECT '=============================================' AS "";

-- 1. 测试连接权限
SELECT '1. 测试连接权限...' AS "";
SELECT '连接测试成功' AS 结果, version() AS 版本信息;

-- 2. 测试pg_roles表访问
SELECT '2. 测试pg_roles表访问...' AS "";
SELECT 'pg_roles表测试' AS 结果, COUNT(*) AS 可访问的角色数量 FROM pg_roles;

-- 3. 测试pg_database表访问
SELECT '3. 测试pg_database表访问...' AS "";
SELECT 'pg_database表测试' AS 结果, COUNT(*) AS 可访问的数据库数量 FROM pg_database;

-- 4. 测试pg_namespace表访问
SELECT '4. 测试pg_namespace表访问...' AS "";
SELECT 'pg_namespace表测试' AS 结果, COUNT(*) AS 可访问的模式数量 FROM pg_namespace;

-- 5. 测试pg_class表访问
SELECT '5. 测试pg_class表访问...' AS "";
SELECT 'pg_class表测试' AS 结果, COUNT(*) AS 可访问的表数量 FROM pg_class;

-- 6. 测试pg_proc表访问
SELECT '6. 测试pg_proc表访问...' AS "";
SELECT 'pg_proc表测试' AS 结果, COUNT(*) AS 可访问的函数数量 FROM pg_proc;

-- 7. 测试information_schema访问
SELECT '7. 测试information_schema访问...' AS "";
SELECT 'information_schema测试' AS 结果, COUNT(*) AS 可访问的权限信息数量 FROM information_schema.role_table_grants;

-- 8. 测试权限查询
SELECT '8. 测试权限查询...' AS "";
SELECT '权限查询测试' AS 结果, COUNT(*) AS 可访问的数据库权限数量 FROM information_schema.role_usage_grants;

-- 9. 显示当前用户权限摘要
SELECT '=============================================' AS "";
SELECT '当前用户权限摘要:' AS "";

-- 显示角色信息
SELECT 
    '角色信息' AS 权限类型,
    rolname AS 角色名,
    rolsuper AS 超级用户,
    rolinherit AS 继承权限,
    rolcreaterole AS 可创建角色,
    rolcreatedb AS 可创建数据库,
    rolcanlogin AS 可登录,
    rolconnlimit AS 连接限制
FROM pg_roles
WHERE rolname = current_user;

-- 显示数据库权限
SELECT 
    '数据库权限' AS 权限类型,
    datname AS 数据库名,
    datacl AS 访问控制列表
FROM pg_database
WHERE datname = current_database();

-- 显示表权限
SELECT 
    '表权限' AS 权限类型,
    table_schema AS 模式名,
    table_name AS 表名,
    privilege_type AS 权限名称,
    is_grantable AS 可授权
FROM information_schema.role_table_grants
WHERE grantee = current_user
ORDER BY table_schema, table_name, privilege_type;

-- 显示使用权限
SELECT 
    '使用权限' AS 权限类型,
    object_schema AS 模式名,
    object_name AS 对象名,
    object_type AS 对象类型,
    privilege_type AS 权限名称,
    is_grantable AS 可授权
FROM information_schema.role_usage_grants
WHERE grantee = current_user
ORDER BY object_schema, object_name, privilege_type;

-- 显示例程权限
SELECT 
    '例程权限' AS 权限类型,
    routine_schema AS 模式名,
    routine_name AS 例程名,
    routine_type AS 例程类型,
    privilege_type AS 权限名称,
    is_grantable AS 可授权
FROM information_schema.role_routine_grants
WHERE grantee = current_user
ORDER BY routine_schema, routine_name, privilege_type;

SELECT '=============================================' AS "";
SELECT '权限测试完成！' AS "";
SELECT '=============================================' AS "";
