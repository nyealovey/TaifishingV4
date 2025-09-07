# 泰摸鱼吧 - 快速参考卡片

## 🚀 快速启动

### 一键安装
```bash
git clone <repository-url>
cd TaifishV4
./setup_dev_environment.sh
```

### 启动开发环境
```bash
./start_dev_with_redis.sh
# 访问: http://localhost:5001
```

### 手动启动
```bash
# 启动Redis
./redis_manager.sh start

# 启动应用
python app.py
```

## 🛠️ 常用命令

### 开发工作流
```bash
# 开始新功能
./dev_workflow.sh start '功能名称'

# 创建数据库迁移
./dev_workflow.sh migrate '描述变更'

# 应用迁移
./dev_workflow.sh apply

# 查看状态
./dev_workflow.sh status
```

### Redis管理
```bash
# 启动Redis
./redis_manager.sh start

# 停止Redis
./redis_manager.sh stop

# 重启Redis
./redis_manager.sh restart

# 查看状态
./redis_manager.sh status

# 查看日志
./redis_manager.sh logs
```

### 数据库操作
```bash
# 测试数据库连接
python test_database.py

# 创建迁移
flask db migrate -m "描述"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

### 测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_models.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 📁 重要文件

### 配置文件
- `.env` - 环境变量配置
- `requirements-local.txt` - 本地开发依赖
- `requirements.txt` - 生产环境依赖

### 脚本文件
- `setup_dev_environment.sh` - 一键安装脚本
- `start_dev_with_redis.sh` - 开发环境启动
- `dev_workflow.sh` - 开发工作流
- `redis_manager.sh` - Redis管理
- `test_database.py` - 数据库测试

### 数据目录
- `userdata/taifish_dev.db` - SQLite数据库
- `userdata/logs/` - 日志文件
- `userdata/backups/` - 备份文件
- `migrations/` - 数据库迁移文件

## 🌐 访问地址

### 开发环境
- **应用首页**: http://localhost:5001
- **API状态**: http://localhost:5001/api/status
- **健康检查**: http://localhost:5001/api/health

### Docker环境
- **应用地址**: http://localhost:8000
- **管理员账户**: admin / admin123

## 🔧 环境变量

### 基础配置
```bash
FLASK_APP=app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key
```

### 数据库配置
```bash
# 使用默认SQLite（推荐）
# DATABASE_URL=sqlite:///./userdata/taifish_dev.db

# 或使用PostgreSQL
# DATABASE_URL=postgresql://user:pass@localhost:5432/taifish
```

### Redis配置
```bash
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
```

## 🐛 常见问题

### 数据库连接失败
```bash
# 检查权限
chmod 666 userdata/taifish_dev.db

# 重新创建数据库
rm userdata/taifish_dev.db
python test_database.py
```

### Redis连接失败
```bash
# 检查Redis状态
./redis_manager.sh status

# 重启Redis
./redis_manager.sh restart
```

### 端口占用
```bash
# 检查端口占用
lsof -i :5001

# 使用其他端口
export FLASK_PORT=5002
python app.py
```

### 依赖安装失败
```bash
# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements-local.txt
```

## 📚 文档链接

- [完整文档](doc/README.md)
- [环境设置指南](doc/development/ENVIRONMENT_SETUP.md)
- [故障排除指南](doc/development/TROUBLESHOOTING.md)
- [数据库迁移指南](doc/development/DATABASE_MIGRATION.md)

## 🆘 获取帮助

1. 查看 [故障排除指南](doc/development/TROUBLESHOOTING.md)
2. 运行 `python test_database.py` 检查环境
3. 查看日志文件 `userdata/logs/`
4. 联系项目维护者

---

**提示**: 将此卡片保存为书签，方便快速查阅常用命令和配置。
