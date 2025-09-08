-- =============================================
-- MySQL 权限测试脚本
-- 泰摸鱼吧 - 数据同步管理平台
-- =============================================

-- 此脚本用于测试当前用户是否具有泰摸鱼吧系统所需的权限

SELECT '=============================================' AS '';
SELECT 'MySQL 权限测试开始...' AS '';
SELECT CONCAT('当前用户: ', USER()) AS '';
SELECT CONCAT('当前数据库: ', DATABASE()) AS '';
SELECT '=============================================' AS '';

-- 1. 测试连接权限
SELECT '1. 测试连接权限...' AS '';
SELECT '连接测试成功' AS 结果, @@VERSION AS 版本信息;

-- 2. 测试mysql.user表访问
SELECT '2. 测试mysql.user表访问...' AS '';
SELECT 'mysql.user表测试' AS 结果, COUNT(*) AS 可访问的用户数量 FROM mysql.user;

-- 3. 测试mysql.db表访问
SELECT '3. 测试mysql.db表访问...' AS '';
SELECT 'mysql.db表测试' AS 结果, COUNT(*) AS 可访问的数据库权限数量 FROM mysql.db;

-- 4. 测试mysql.tables_priv表访问
SELECT '4. 测试mysql.tables_priv表访问...' AS '';
SELECT 'mysql.tables_priv表测试' AS 结果, COUNT(*) AS 可访问的表权限数量 FROM mysql.tables_priv;

-- 5. 测试mysql.columns_priv表访问
SELECT '5. 测试mysql.columns_priv表访问...' AS '';
SELECT 'mysql.columns_priv表测试' AS 结果, COUNT(*) AS 可访问的列权限数量 FROM mysql.columns_priv;

-- 6. 测试mysql.procs_priv表访问
SELECT '6. 测试mysql.procs_priv表访问...' AS '';
SELECT 'mysql.procs_priv表测试' AS 结果, COUNT(*) AS 可访问的存储过程权限数量 FROM mysql.procs_priv;

-- 7. 测试INFORMATION_SCHEMA访问
SELECT '7. 测试INFORMATION_SCHEMA访问...' AS '';
SELECT 'INFORMATION_SCHEMA测试' AS 结果, COUNT(*) AS 可访问的权限信息数量 FROM INFORMATION_SCHEMA.USER_PRIVILEGES;

-- 8. 测试权限查询
SELECT '8. 测试权限查询...' AS '';
SELECT '权限查询测试' AS 结果, COUNT(*) AS 可访问的数据库权限数量 FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES;

-- 9. 显示当前用户权限摘要
SELECT '=============================================' AS '';
SELECT '当前用户权限摘要:' AS '';

-- 显示用户权限
SELECT 
    '用户权限' AS 权限类型,
    CONCAT(GRANTEE, '@', HOST) AS 用户,
    PRIVILEGE_TYPE AS 权限名称,
    IS_GRANTABLE AS 可授权
FROM INFORMATION_SCHEMA.USER_PRIVILEGES
WHERE GRANTEE = SUBSTRING_INDEX(USER(), '@', 1)
ORDER BY PRIVILEGE_TYPE;

-- 显示数据库权限
SELECT 
    '数据库权限' AS 权限类型,
    GRANTEE AS 用户,
    TABLE_SCHEMA AS 数据库,
    PRIVILEGE_TYPE AS 权限名称,
    IS_GRANTABLE AS 可授权
FROM INFORMATION_SCHEMA.SCHEMA_PRIVILEGES
WHERE GRANTEE = SUBSTRING_INDEX(USER(), '@', 1)
ORDER BY TABLE_SCHEMA, PRIVILEGE_TYPE;

-- 显示表权限
SELECT 
    '表权限' AS 权限类型,
    GRANTEE AS 用户,
    TABLE_SCHEMA AS 数据库,
    TABLE_NAME AS 表名,
    PRIVILEGE_TYPE AS 权限名称,
    IS_GRANTABLE AS 可授权
FROM INFORMATION_SCHEMA.TABLE_PRIVILEGES
WHERE GRANTEE = SUBSTRING_INDEX(USER(), '@', 1)
ORDER BY TABLE_SCHEMA, TABLE_NAME, PRIVILEGE_TYPE;

SELECT '=============================================' AS '';
SELECT '权限测试完成！' AS '';
SELECT '=============================================' AS '';
