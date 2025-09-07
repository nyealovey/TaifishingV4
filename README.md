# 泰摸鱼吧 (TaifishV4)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

> 一个基于Flask的DBA数据库管理Web应用，提供多数据库实例管理、账户管理、任务调度、日志监控等功能。

## ✨ 核心特性

- 🔐 **用户认证与权限管理** - 基于Flask-Login的会话管理
- 🗄️ **多数据库实例管理** - 支持PostgreSQL、MySQL、SQL Server、Oracle
- 👥 **账户信息管理** - 数据库用户账户同步与管理
- 🔑 **凭据管理** - 安全的数据库连接凭据存储
- ⚙️ **系统参数管理** - 全局配置参数管理
- 📊 **任务调度系统** - 高度可定制化的任务管理
- 📈 **实时监控仪表板** - 系统状态和统计信息
- 📝 **操作日志记录** - 完整的审计日志
- 🚀 **RESTful API** - 完整的API接口

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Redis 6.0+
- SQLite 3.0+ (开发环境)
- PostgreSQL 12+ (生产环境)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/nyealovey/TaifishingV4.git
cd TaifishingV4
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

5. **初始化数据库**
```bash
flask db upgrade
```

6. **创建管理员用户**
```bash
python scripts/create_admin_user.py
```

7. **启动应用**
```bash
python app.py
```

8. **访问应用**
打开浏览器访问: http://localhost:5001

### Docker 部署

```bash
# 使用Docker Compose
docker-compose up -d

# 或使用Docker
docker build -t taifish .
docker run -p 5001:5001 taifish
```

## 📖 功能模块

### 1. 用户管理
- 用户注册、登录、登出
- 密码修改和用户资料管理
- 基于角色的权限控制
- JWT令牌认证支持

### 2. 数据库实例管理
- 支持PostgreSQL、MySQL、SQL Server、Oracle
- 实例创建、编辑、删除
- 连接测试和状态监控
- 实例统计和标签管理

### 3. 凭据管理
- 安全的数据库连接凭据存储
- 凭据与实例关联管理
- 凭据状态和统计信息
- 密码加密存储

### 4. 账户信息管理
- 数据库用户账户同步
- 按数据库类型筛选账户
- 账户状态和权限管理
- 账户统计信息

### 5. 任务调度系统
- 高度可定制化的任务管理
- 内置同步任务模板
- 支持自定义Python代码执行
- 按数据库类型自动匹配实例
- 任务执行统计和监控

### 6. 系统参数管理
- 全局配置参数管理
- 参数分类和加密存储
- 参数验证和更新
- 系统配置热更新

### 7. 操作日志管理
- 完整的操作审计日志
- 日志搜索和筛选
- 日志统计和导出
- 安全日志记录

### 8. 实时监控仪表板
- 系统概览和统计信息
- 数据库实例状态监控
- 任务执行状态监控
- 日志趋势图表
- 系统健康检查

## 🛠️ 技术栈

### 后端技术
- **Flask 3.0.3** - Web应用框架
- **SQLAlchemy 2.0.30** - 数据库ORM
- **Flask-Migrate 4.0.7** - 数据库迁移
- **Flask-Login 0.6.3** - 用户认证
- **Flask-JWT-Extended 4.6.0** - JWT认证
- **Celery 5.3.6** - 异步任务队列
- **Redis 8.2.1** - 缓存和消息队列

### 前端技术
- **Bootstrap 5.3.2** - UI组件库
- **Font Awesome 6.4.0** - 图标库
- **jQuery 3.7.1** - JavaScript库
- **Chart.js 4.4.0** - 图表库

### 数据库支持
- **PostgreSQL** - 生产环境主数据库
- **MySQL** - 支持MySQL实例管理
- **SQL Server** - 支持SQL Server实例管理
- **Oracle** - 支持Oracle实例管理
- **SQLite** - 开发环境数据库

## 📁 项目结构

```
TaifishV4/
├── app/                    # 应用主目录
│   ├── models/            # 数据模型
│   ├── routes/            # 路由控制器
│   ├── services/          # 业务服务层
│   ├── utils/             # 工具类
│   └── templates/         # 模板文件
├── doc/                   # 项目文档
├── docker/                # Docker配置
├── scripts/               # 脚本文件
├── tests/                 # 测试文件
├── userdata/              # 用户数据目录
├── migrations/            # 数据库迁移
├── requirements.txt       # Python依赖
├── app.py                 # 应用入口
└── README.md             # 项目说明
```

## 🔧 配置说明

### 环境变量配置

```bash
# 应用配置
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# 数据库配置
DATABASE_URL=sqlite:///instance.db  # 开发环境
# DATABASE_URL=postgresql://user:pass@localhost/taifish  # 生产环境

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 时区配置
TIMEZONE=Asia/Shanghai
```

### 数据库配置

支持多种数据库配置：

```python
# SQLite (开发环境)
DATABASE_URL = "sqlite:///instance.db"

# PostgreSQL (生产环境)
DATABASE_URL = "postgresql://user:password@localhost:5432/taifish"

# MySQL
DATABASE_URL = "mysql://user:password@localhost:3306/taifish"
```

## 🚀 部署指南

### 开发环境部署

1. **本地开发**
```bash
# 启动Redis
redis-server

# 启动应用
python app.py
```

2. **Docker开发环境**
```bash
docker-compose -f docker/compose/docker-compose.yml up -d
```

### 生产环境部署

1. **使用Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

2. **手动部署**
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost/taifish

# 初始化数据库
flask db upgrade

# 启动应用
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

## 📚 API文档

### 认证接口
- `POST /auth/login` - 用户登录
- `POST /auth/logout` - 用户登出
- `POST /auth/register` - 用户注册

### 实例管理接口
- `GET /instances/` - 获取实例列表
- `POST /instances/create` - 创建实例
- `GET /instances/<id>` - 获取实例详情
- `PUT /instances/<id>/edit` - 更新实例
- `DELETE /instances/<id>/delete` - 删除实例

### 任务管理接口
- `GET /tasks/` - 获取任务列表
- `POST /tasks/create` - 创建任务
- `POST /tasks/create-builtin` - 创建内置任务
- `POST /tasks/execute-all` - 批量执行任务

更多API文档请参考 [API文档](doc/api/README.md)

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_models.py

# 运行测试并生成覆盖率报告
pytest --cov=app tests/
```

### 测试类型
- **单元测试** - 测试单个函数和类
- **集成测试** - 测试API接口
- **端到端测试** - 测试完整用户流程

## 📊 监控和日志

### 日志系统
- 应用日志: `userdata/logs/app.log`
- 认证日志: `userdata/logs/auth.log`
- 数据库日志: `userdata/logs/database.log`
- 安全日志: `userdata/logs/security.log`

### 监控指标
- 系统健康状态
- 数据库连接状态
- 任务执行状态
- 用户活跃度

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 开发团队

- **项目负责人**: 泰摸鱼吧开发团队
- **主要贡献者**: [@nyealovey](https://github.com/nyealovey)

## 📞 支持与反馈

- **问题反馈**: [GitHub Issues](https://github.com/nyealovey/TaifishingV4/issues)
- **功能建议**: [GitHub Discussions](https://github.com/nyealovey/TaifishingV4/discussions)
- **文档**: [项目文档](doc/)

## 🗺️ 路线图

### v1.1.0 (计划中)
- [ ] 数据库备份与恢复
- [ ] 数据导入导出功能
- [ ] 移动端适配
- [ ] 主题切换

### v1.2.0 (计划中)
- [ ] 多租户支持
- [ ] 插件系统
- [ ] 自动化运维
- [ ] 监控告警

### v2.0.0 (计划中)
- [ ] 微服务架构
- [ ] 云原生部署
- [ ] 大数据分析
- [ ] AI智能运维

---

**泰摸鱼吧** - 让数据库管理更简单！ 🐟

[![Star](https://img.shields.io/github/stars/nyealovey/TaifishingV4?style=social)](https://github.com/nyealovey/TaifishingV4)
[![Fork](https://img.shields.io/github/forks/nyealovey/TaifishingV4?style=social)](https://github.com/nyealovey/TaifishingV4/fork)