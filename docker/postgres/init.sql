-- 泰摸鱼吧 - PostgreSQL数据库初始化脚本
-- 创建数据库和用户

-- 创建数据库（如果不存在）
SELECT 'CREATE DATABASE taifish_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'taifish_dev')\gexec

-- 创建生产数据库（如果不存在）
SELECT 'CREATE DATABASE taifish_prod'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'taifish_prod')\gexec

-- 设置数据库编码
ALTER DATABASE taifish_dev SET timezone TO 'UTC';
ALTER DATABASE taifish_prod SET timezone TO 'UTC';

-- 创建扩展
\c taifish_dev;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c taifish_prod;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 设置连接参数
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- 重启PostgreSQL以应用设置
SELECT pg_reload_conf();
