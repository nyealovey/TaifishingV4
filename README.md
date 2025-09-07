# 泰摸鱼吧 (TaifishV4)

## 项目简介

泰摸鱼吧是一个专为DBA设计的数据库管理Web应用，提供数据库实例管理、凭据管理、账户信息统计、定时任务调度等功能。支持SQL Server、MySQL、Oracle等多种数据库类型，采用Flask + PostgreSQL + Redis + Celery技术栈。

## 核心特性

- **多数据库支持**: 支持SQL Server、MySQL、Oracle数据库实例管理
- **统一凭据管理**: 安全的全局凭据存储与加密
- **账户信息统计**: 多维度数据统计与分析
- **智能搜索筛选**: 分数据库类型的账户查询功能
- **模块化定时任务**: 灵活的数据同步任务调度
- **全局参数管理**: 系统配置参数统一管理
- **完整操作日志**: 系统变更审计与追踪
- **Redis缓存优化**: 高性能数据访问
- **Docker容器化**: 统一的开发与部署环境

## 技术栈

### 后端技术
- **Web框架**: Flask 2.0.3 + Jinja2 3.0.3
- **数据库**: PostgreSQL 13.5
- **缓存**: Redis 4.0.2
- **任务队列**: Celery 5.2.7
- **数据库驱动**: 
  - SQL Server: pymssql 2.2.5, pyodbc 4.0.32
  - MySQL: pymysql 1.0.2, mysql-connector-python 8.0.29
  - Oracle: cx_Oracle 8.3.0

### 前端技术
- **模板引擎**: Jinja2 3.0.3
- **样式框架**: Bootstrap 5
- **图表库**: Chart.js
- **代码编辑器**: CodeMirror

### 部署技术
- **容器化**: Docker 20.10.12 + Docker Compose 1.29.2
- **Web服务器**: Gunicorn
- **操作系统**: Ubuntu 20.04 LTS

## 项目结构

```
TaifishV4/
├── app/                    # Flask应用主目录
│   ├── __init__.py        # 应用初始化
│   ├── models/            # 数据模型
│   │   ├── user.py        # 用户模型
│   │   ├── instance.py    # 数据库实例模型
│   │   ├── credential.py  # 凭据模型
│   │   └── sync_data.py   # 同步数据模型
│   ├── routes/            # 路由控制器
│   │   ├── main.py        # 主要路由
│   │   ├── auth.py        # 认证路由
│   │   ├── api.py         # API路由
│   │   └── admin.py       # 管理路由
│   ├── services/          # 业务逻辑服务
│   │   ├── database_service.py    # 数据库服务
│   │   └── database_drivers.py    # 数据库驱动检查
│   ├── templates/         # HTML模板
│   │   └── index.html     # 首页模板
│   └── utils/             # 工具函数
├── scripts/               # 工具脚本
│   ├── start_redis.sh     # Redis管理脚本
│   ├── migrate_db.py      # 数据库迁移脚本
│   ├── init_data.py       # 数据初始化脚本
│   └── init_database.py   # 数据库初始化脚本
├── tests/                 # 测试文件
│   └── test_api.py        # API测试
├── docker/                # Docker环境配置
│   ├── Dockerfile         # 应用镜像
│   └── compose/           # Docker Compose配置
│       └── docker-compose.yml
├── doc/                   # 项目文档
│   ├── README.md          # 文档导航
│   ├── development/       # 开发文档
│   │   ├── ENVIRONMENT_SETUP.md    # 环境设置指南
│   │   ├── DATABASE_MIGRATION.md   # 数据库迁移指南
│   │   └── TROUBLESHOOTING.md      # 故障排除指南
│   └── api/              # API文档
├── userdata/              # 用户数据目录
│   ├── taifish_dev.db    # SQLite数据库
│   ├── redis/            # Redis数据
│   ├── logs/             # 日志文件
│   ├── backups/          # 备份文件
│   ├── exports/          # 导出文件
│   └── uploads/          # 上传文件
├── migrations/            # 数据库迁移文件
├── requirements-local.txt # 本地开发依赖
├── requirements.txt       # 生产环境依赖
├── setup_dev_environment.sh # 一键安装脚本
├── start_dev_with_redis.sh  # 开发环境启动脚本
├── redis_manager.sh       # Redis管理工具
├── dev_workflow.sh        # 开发工作流工具
├── test_database.py       # 数据库连接测试
├── app.py                 # 应用入口点
└── README.md             # 项目说明
```

## 快速开始

### 环境要求

- **Python**: 3.11 或 3.12 (推荐)
- **Redis**: 6.0+ (用于缓存和Celery)
- **Git**: 2.0+
- **操作系统**: macOS, Linux, Windows
- **Docker**: 20.10+ (可选，用于生产环境)

### 一键启动 (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd TaifishV4

# 一键启动开发环境
./start_dev_with_redis.sh
```

访问 http://localhost:5001 查看应用。

### 手动安装

#### 1. 克隆项目
```bash
git clone <repository-url>
cd TaifishV4
```

#### 2. 创建虚拟环境
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements-local.txt
```

#### 4. 启动Redis
```bash
# macOS (使用Homebrew)
brew install redis
brew services start redis

# 或使用项目脚本
./redis_manager.sh start
```

#### 5. 启动应用
```bash
python app.py
```

### Docker环境 (生产环境)

```bash
# 启动完整Docker环境
cd docker
./scripts/start_full_test.sh

# 访问应用
# 应用地址: http://localhost:8000
# 管理员账户: admin / admin123
```

### 开发环境设置

#### 方式一：一键启动 (推荐)
```bash
./start_dev_with_redis.sh
```

#### 方式二：Docker环境
```bash
cd docker
./scripts/start_full_test.sh
```

#### 方式三：手动启动
```bash
# 1. 启动Redis
./redis_manager.sh start

# 2. 启动Flask应用
python app.py
```

### 开发工作流

#### 数据库迁移
```bash
# 开始新功能开发
./dev_workflow.sh start '功能名称'

# 修改模型后创建迁移
./dev_workflow.sh migrate '描述变更内容'

# 应用迁移
./dev_workflow.sh apply

# 查看状态
./dev_workflow.sh status
```

#### Redis管理
```bash
# 启动Redis
./redis_manager.sh start

# 停止Redis
./redis_manager.sh stop

# 查看状态
./redis_manager.sh status

# 查看日志
./redis_manager.sh logs
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_models.py

# 测试数据库连接
python test_database.py
```

## 数据要求

### 重要说明
本项目严格要求使用真实数据，禁止使用任何形式的模拟数据、假数据或硬编码测试数据。

### 数据生成
- 所有数据必须通过真实数据库连接获取
- 提供完整的数据生成脚本
- 支持开发和生产环境数据初始化
- 所有数据必须经过连接验证

### 数据生成脚本使用
```bash
# 初始化全局参数
python scripts/init_data.py --init-global-params

# 初始化数据库实例（需要真实连接信息）
python scripts/init_data.py --init-instances

# 初始化凭据信息
python scripts/init_data.py --init-credentials

# 同步账户数据（从真实数据库获取）
python scripts/init_data.py --init-accounts

# 验证所有数据
python scripts/init_data.py --validate-all
```

## 功能模块

### 1. 用户认证与权限管理
- JWT令牌认证
- 基于角色的访问控制(RBAC)
- 密码加密存储
- 会话管理

### 2. 数据库实例管理
- 支持SQL Server/MySQL/Oracle
- 实例CRUD操作
- 连接测试功能
- 手动同步触发

### 3. 凭据管理
- 全局凭据存储
- 密码加密保护
- 凭据与实例关联
- 凭据类型管理

### 4. 账户信息统计
- 多维度数据统计
- 按数据库类型统计
- 按账户类型统计
- 活跃度分析

### 5. 账户搜索筛选
- 分数据库类型搜索
- 多条件筛选
- 权限搜索
- 时间范围搜索

### 6. 定时任务管理
- 模块化任务调度
- 账户信息同步
- 任务监控
- 手动触发

### 7. 全局参数管理
- 系统配置统一管理
- 数据库类型配置
- 凭据类型配置
- 同步类型配置

### 8. 日志管理
- 操作日志记录
- 错误日志追踪
- 日志搜索导出
- 审计功能

## API文档

### 认证API
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `POST /api/auth/forgot-password` - 密码重置

### 实例管理API
- `GET /api/instances` - 获取实例列表
- `POST /api/instances` - 创建实例
- `PUT /api/instances/<id>` - 更新实例
- `DELETE /api/instances/<id>` - 删除实例
- `POST /api/instances/<id>/test` - 测试连接

### 凭据管理API
- `GET /api/credentials` - 获取凭据列表
- `POST /api/credentials` - 创建凭据
- `PUT /api/credentials/<id>` - 更新凭据
- `DELETE /api/credentials/<id>` - 删除凭据

### 账户统计API
- `GET /api/accounts/stats` - 获取统计数据
- `POST /api/accounts/stats/export` - 导出统计

### 账户搜索API
- `GET /api/accounts/search/<db_type>` - 搜索账户
- `POST /api/accounts/search/<db_type>/export` - 导出搜索结果

### 任务管理API
- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks` - 创建任务
- `PUT /api/tasks/<id>` - 更新任务
- `DELETE /api/tasks/<id>` - 删除任务
- `POST /api/tasks/<id>/run` - 手动运行任务

## 配置说明

### 环境变量
```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/taifish
REDIS_URL=redis://localhost:6379/0

# 应用配置
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# 外部数据库配置
SQL_SERVER_HOST=192.168.1.100
SQL_SERVER_PORT=1433
MYSQL_HOST=192.168.1.101
MYSQL_PORT=3306
ORACLE_HOST=192.168.1.102
ORACLE_PORT=1521
```

### Docker配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  flask:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@postgres:5432/taifish
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:13.5
    environment:
      - POSTGRES_DB=taifish
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:4.0.2
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
```

## 测试

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python -m pytest tests/test_models.py

# 运行测试并生成覆盖率报告
python -m pytest --cov=app --cov-report=html
```

### 测试要求
- 所有测试必须使用真实数据
- 禁止使用模拟数据或假数据
- 测试数据必须通过脚本生成
- 确保测试环境数据隔离

## 部署

### 生产环境部署
```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d

# 初始化生产数据
docker-compose exec flask python scripts/init_data.py --init-all
```

### 监控与维护
- 定期备份数据库
- 监控Redis缓存状态
- 检查Celery任务执行情况
- 查看应用日志

## 安全说明

### 数据安全
- 所有密码使用bcrypt加密
- 敏感信息使用AES加密
- 数据库连接使用SSL
- Redis设置密码保护

### 访问控制
- 基于JWT的认证机制
- 角色权限控制
- API访问限制
- 操作日志记录

## 贡献指南

### 开发规范
- 遵循PEP 8代码规范
- 使用类型注解
- 编写完整的文档字符串
- 确保测试覆盖率

### 提交规范
- 使用清晰的提交信息
- 每个提交只包含一个功能
- 提交前运行所有测试
- 确保代码质量检查通过

## 许可证

本项目采用MIT许可证，详情请查看LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: your-email@example.com

---

**重要提醒**: 本项目严格要求使用真实数据，禁止使用任何形式的模拟数据。所有数据必须通过真实数据库连接获取或通过脚本自动生成。
