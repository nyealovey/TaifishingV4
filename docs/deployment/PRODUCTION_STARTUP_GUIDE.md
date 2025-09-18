# 鲸落 - 生产环境启动指南

## 🚨 重要说明

**当前Docker镜像内部启动方式存在问题！**

### ❌ 当前问题

1. **使用Flask开发服务器**: `CMD ["python", "app.py"]` 直接启动Flask开发服务器
2. **缺少WSGI服务器**: 没有安装Gunicorn、uWSGI等生产级WSGI服务器
3. **单线程运行**: Flask开发服务器不适合生产环境
4. **缺少进程管理**: 没有使用supervisor等进程管理工具

### ✅ 解决方案

我已经为您创建了真正的生产环境配置：

## 🏗️ 生产环境架构

### 1. WSGI服务器
- **Gunicorn**: 生产级WSGI HTTP服务器
- **Gevent**: 异步工作模式，支持高并发
- **多进程**: 根据CPU核心数自动配置工作进程

### 2. 进程管理
- **Supervisor**: 管理多个进程（应用+调度器）
- **自动重启**: 进程崩溃时自动重启
- **日志管理**: 统一的日志收集和管理

### 3. 性能优化
- **连接池**: 数据库连接池优化
- **缓存策略**: Redis缓存配置
- **资源限制**: 内存和CPU使用限制

## 📁 新增文件

### 1. 生产环境依赖
```
requirements-prod.txt          # 生产环境Python依赖
├── gunicorn==21.2.0          # WSGI服务器
├── gevent==23.9.1            # 异步工作模式
├── supervisor==4.2.5         # 进程管理
└── prometheus-client==0.19.0 # 监控支持
```

### 2. 生产环境配置
```
Dockerfile.prod               # 生产环境Dockerfile
├── 安装生产环境依赖
├── 配置Gunicorn
├── 配置Supervisor
└── 多进程启动

wsgi.py                       # WSGI入口文件
├── 生产环境应用入口
└── Gunicorn启动点

app/config.py                 # 统一配置类（支持开发和生产环境）
├── 性能优化配置
├── 安全配置
└── 监控配置
```

### 3. 启动脚本
```
scripts/start-prod.sh         # 生产环境启动脚本
├── 环境检查
├── 依赖服务等待
├── 数据库迁移
└── Gunicorn启动
```

## 🚀 正确的生产环境启动方式

### 1. 构建生产环境镜像

```bash
# 使用新的生产环境Dockerfile
docker build -f Dockerfile.prod -t whalefall:latest .

# 或者使用构建脚本
./scripts/build-image.sh latest
```

### 2. 启动生产环境

```bash
# 使用Docker Compose（推荐）
./scripts/deploy.sh prod start

# 或者手动启动
docker compose -f docker-compose.prod.yml up -d
```

### 3. 验证生产环境

```bash
# 检查进程
docker exec -it whalefall_app ps aux

# 应该看到：
# - gunicorn主进程
# - 多个gunicorn工作进程
# - supervisor进程
# - 调度器进程

# 检查日志
docker logs whalefall_app

# 应该看到Gunicorn启动日志，而不是Flask开发服务器日志
```

## 🔧 生产环境特性

### 1. 高并发支持
```python
# Gunicorn配置
workers = multiprocessing.cpu_count() * 2 + 1  # 工作进程数
worker_class = "gevent"                        # 异步工作模式
worker_connections = 1000                      # 每个工作进程连接数
```

### 2. 进程管理
```ini
# Supervisor配置
[program:whalefall]
command=/app/.venv/bin/gunicorn --config /app/gunicorn.conf.py wsgi:application
autostart=true
autorestart=true

[program:whalefall-scheduler]
command=/app/.venv/bin/python -c "from app.scheduler import start_scheduler; start_scheduler()"
autostart=true
autorestart=true
```

### 3. 性能监控
```python
# 资源限制
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

## 📊 性能对比

| 特性 | 开发环境 | 生产环境 |
|------|----------|----------|
| 服务器 | Flask开发服务器 | Gunicorn + Gevent |
| 进程数 | 1个 | 多进程（CPU核心数×2+1） |
| 并发支持 | 单线程 | 高并发异步 |
| 进程管理 | 无 | Supervisor |
| 自动重启 | 无 | 有 |
| 资源限制 | 无 | 有 |
| 监控支持 | 基础 | 完整 |

## 🛠️ 故障排除

### 1. 检查进程状态
```bash
# 进入容器
docker exec -it whalefall_app bash

# 查看进程
ps aux | grep -E "(gunicorn|supervisor|python)"

# 应该看到多个进程在运行
```

### 2. 检查日志
```bash
# 查看Gunicorn日志
tail -f /app/userdata/logs/gunicorn_access.log
tail -f /app/userdata/logs/gunicorn_error.log

# 查看Supervisor日志
tail -f /app/userdata/logs/supervisord.log
```

### 3. 性能监控
```bash
# 查看资源使用
docker stats whalefall_app

# 查看连接数
docker exec -it whalefall_app netstat -an | grep :5000
```

## 📈 生产环境优化建议

### 1. 数据库优化
```sql
-- 增加连接池大小
-- 配置索引
-- 启用查询缓存
```

### 2. Redis优化
```bash
# 配置内存限制
# 启用持久化
# 配置淘汰策略
```

### 3. Nginx优化
```nginx
# 启用gzip压缩
# 配置静态文件缓存
# 设置超时时间
```

## 🎯 总结

现在您的Docker镜像已经配置了真正的生产环境解决方案：

1. ✅ **WSGI服务器**: 使用Gunicorn替代Flask开发服务器
2. ✅ **多进程支持**: 根据CPU核心数自动配置工作进程
3. ✅ **异步处理**: 使用Gevent支持高并发
4. ✅ **进程管理**: 使用Supervisor管理多个进程
5. ✅ **自动重启**: 进程崩溃时自动重启
6. ✅ **资源限制**: 限制内存和CPU使用
7. ✅ **监控支持**: 完整的日志和监控

**请使用新的Dockerfile.prod重新构建镜像，以获得真正的生产环境性能！**
