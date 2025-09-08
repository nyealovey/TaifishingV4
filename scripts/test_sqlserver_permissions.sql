-- =============================================
-- SQL Server 权限测试脚本
-- 泰摸鱼吧 - 数据同步管理平台
-- =============================================

-- 此脚本用于测试当前用户是否具有泰摸鱼吧系统所需的权限

PRINT '=============================================';
PRINT 'SQL Server 权限测试开始...';
PRINT '当前用户: ' + SUSER_NAME();
PRINT '当前数据库: ' + DB_NAME();
PRINT '=============================================';

-- 1. 测试连接权限
PRINT '1. 测试连接权限...';
BEGIN TRY
    SELECT '连接测试成功' AS 结果, @@VERSION AS 版本信息;
    PRINT '   ✓ 连接权限正常';
END TRY
BEGIN CATCH
    PRINT '   ✗ 连接权限不足: ' + ERROR_MESSAGE();
END CATCH

-- 2. 测试服务器级权限
PRINT '2. 测试服务器级权限...';
BEGIN TRY
    SELECT '服务器级权限测试' AS 结果, COUNT(*) AS 可访问的服务器主体数量 FROM sys.server_principals;
    PRINT '   ✓ 服务器级权限正常';
END TRY
BEGIN CATCH
    PRINT '   ✗ 服务器级权限不足: ' + ERROR_MESSAGE();
END CATCH

-- 3. 测试数据库级权限
PRINT '3. 测试数据库级权限...';
BEGIN TRY
    SELECT '数据库级权限测试' AS 结果, COUNT(*) AS 可访问的数据库数量 FROM sys.databases;
    PRINT '   ✓ 数据库级权限正常';
END TRY
BEGIN CATCH
    PRINT '   ✗ 数据库级权限不足: ' + ERROR_MESSAGE();
END CATCH

-- 4. 测试权限查询
PRINT '4. 测试权限查询...';
BEGIN TRY
    SELECT '权限查询测试' AS 结果, COUNT(*) AS 可访问的服务器权限数量 FROM sys.server_permissions;
    PRINT '   ✓ 权限查询正常';
END TRY
BEGIN CATCH
    PRINT '   ✗ 权限查询不足: ' + ERROR_MESSAGE();
END CATCH

-- 5. 测试数据库权限查询
PRINT '5. 测试数据库权限查询...';
BEGIN TRY
    SELECT '数据库权限查询测试' AS 结果, COUNT(*) AS 可访问的数据库权限数量 FROM sys.database_permissions;
    PRINT '   ✓ 数据库权限查询正常';
END TRY
BEGIN CATCH
    PRINT '   ✗ 数据库权限查询不足: ' + ERROR_MESSAGE();
END CATCH

-- 6. 测试服务器状态查询（可选）
PRINT '6. 测试服务器状态查询（可选）...';
BEGIN TRY
    SELECT '服务器状态查询测试' AS 结果, COUNT(*) AS 可访问的服务器状态信息数量 FROM sys.dm_exec_sessions;
    PRINT '   ✓ 服务器状态查询正常';
END TRY
BEGIN CATCH
    PRINT '   ⚠ 服务器状态查询不足（可选功能）: ' + ERROR_MESSAGE();
END CATCH

-- 7. 显示当前用户权限摘要
PRINT '=============================================';
PRINT '当前用户权限摘要:';

-- 服务器级权限
SELECT 
    '服务器级权限' AS 权限级别,
    p.permission_name AS 权限名称,
    p.state_desc AS 权限状态
FROM sys.server_permissions p
JOIN sys.server_principals sp ON p.grantee_principal_id = sp.principal_id
WHERE sp.name = SUSER_NAME()
ORDER BY p.permission_name;

-- 数据库级权限（当前数据库）
SELECT 
    '数据库级权限' AS 权限级别,
    dp.permission_name AS 权限名称,
    dp.state_desc AS 权限状态
FROM sys.database_permissions dp
JOIN sys.database_principals dbp ON dp.grantee_principal_id = dbp.principal_id
WHERE dbp.name = USER_NAME()
ORDER BY dp.permission_name;

PRINT '=============================================';
PRINT '权限测试完成！';
PRINT '=============================================';
