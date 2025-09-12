# 泰摸鱼吧 - 项目结构

## 项目目录结构

```
TaifishV4/
├── app/                           # Flask应用主目录 ✅
│   ├── __init__.py               # 应用初始化 ✅
│   ├── models/                   # 数据模型 ✅
│   │   ├── __init__.py           # 模型初始化 ✅
│   │   ├── user.py              # 用户模型 ✅
│   │   ├── instance.py          # 实例模型 ✅
│   │   ├── credential.py        # 凭据模型 ✅
│   │   └── sync_data.py         # 同步数据模型 ✅
│   ├── routes/                   # 路由定义 ✅
│   │   ├── __init__.py           # 路由初始化 ✅
│   │   ├── main.py              # 主页面路由 ✅
│   │   ├── auth.py              # 认证路由 ✅
│   │   ├── instances.py         # 实例管理路由 ✅
│   │   ├── credentials.py       # 凭据管理路由 ✅
│   │   ├── account_list.py      # 账户列表路由 ✅
│   │   ├── account_sync.py      # 账户同步路由 ✅
│   │   ├── account_static.py    # 账户统计路由 ✅
│   │   ├── account_classification.py # 账户分类路由 ✅
│   │   ├── tasks.py             # 任务管理路由 ✅
│   │   ├── logs.py              # 日志管理路由 ✅ (已优化)
│   │   │                        # - 智能日志筛选 (按级别、模块、时间)
│   │   │                        # - 动态模块列表获取
│   │   │                        # - 中间状态日志过滤
│   │   │                        # - 完整响应内容解析
│   │   │                        # - 错误日志筛选修复
│   │   ├── dashboard.py         # 仪表板路由 ✅
│   │   └── admin.py             # 管理后台路由 ✅
│   ├── services/                 # 业务逻辑服务 ✅
│   │   ├── database_service.py  # 数据库服务 ✅
│   │   ├── database_drivers.py  # 数据库驱动检查 ✅
│   │   ├── account_sync_service.py # 账户同步服务 ✅
│   │   └── account_classification_service.py # 账户分类服务 ✅
│   ├── middleware/               # 中间件 ✅
│   │   └── error_logging_middleware.py # 错误日志中间件 ✅
│   │                              # - 请求/响应日志记录
│   │                              # - 日志合并功能
│   │                              # - 来源识别 (网页请求/后台调用)
│   │                              # - 批量同步日志合并
│   └── templates/                # Jinja2模板 ✅
│       └── index.html           # 首页模板 ✅
├── scripts/                      # 脚本目录 ✅
│   ├── start_redis.sh           # Redis管理脚本 ✅
│   ├── migrate_db.py            # 数据库迁移脚本 ✅
│   ├── init_data.py             # 数据初始化脚本 ✅
│   └── init_database.py         # 数据库初始化脚本 ✅
│   │   └── (待实现)
│   ├── validators/              # 数据验证器
│   │   └── (待实现)
│   └── config/                  # 配置文件
│       └── (待实现)
├── tests/                        # 测试文件
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   ├── api/                     # API测试
│   ├── cache/                   # 缓存测试
│   ├── task/                    # 任务测试
│   └── security/                # 安全测试
├── docker/                       # Docker配置
│   ├── postgres/                # PostgreSQL配置
│   │   └── init.sql
│   ├── redis/                   # Redis配置
│   │   └── redis.conf
│   └── nginx/                   # Nginx配置
│       └── nginx.conf
├── docs/                         # 项目文档
│   └── (待实现)
├── userdata/                     # 用户数据目录
│   ├── logs/                    # 日志文件
│   ├── uploads/                 # 上传文件
│   ├── backups/                 # 备份文件
│   └── exports/                 # 导出文件
├── .env                         # 环境变量文件
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略文件
├── Dockerfile                   # Docker镜像构建文件
├── docker-compose.yml           # Docker Compose开发配置
├── docker-compose.prod.yml      # Docker Compose生产配置
├── requirements.txt             # Python依赖
├── README.md                    # 项目说明
├── spec.md                      # 技术规格文档
├── todolist.md                  # 任务清单
└── PROJECT_STRUCTURE.md         # 项目结构文档
```

## 核心文件说明

### 应用核心文件
- `app/__init__.py`: Flask应用初始化，配置扩展和蓝图
- `app/config.py`: 应用配置管理，支持开发/生产/测试环境
- `app/models/`: 数据模型定义，包含所有数据库表模型
- `app/routes/`: 路由定义，包含所有页面和API路由
- `app/templates/`: Jinja2模板文件，用于页面渲染
- `app/utils/`: 工具函数，包含日志和环境变量管理

### Docker配置文件
- `Dockerfile`: 应用容器镜像构建文件
- `docker-compose.yml`: 开发环境Docker Compose配置
- `docker-compose.prod.yml`: 生产环境Docker Compose配置
- `docker/`: 各种服务的配置文件

### 脚本文件
- `scripts/start_dev.sh`: 开发环境启动脚本
- `scripts/start_prod.sh`: 生产环境启动脚本
- `scripts/data_requirements.md`: 数据要求和生成脚本规范

### 配置文件
- `.env`: 环境变量配置文件
- `.env.example`: 环境变量配置示例
- `requirements.txt`: Python依赖包列表
- `.gitignore`: Git版本控制忽略文件

### 文档文件
- `README.md`: 项目说明文档
- `spec.md`: 详细技术规格文档
- `todolist.md`: 开发任务清单
- `PROJECT_STRUCTURE.md`: 项目结构说明文档

## 技术栈

### 后端技术
- **Web框架**: Flask 3.0.3 + Jinja2 3.1.2
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis 6.0+
- **任务队列**: Celery 5.3.6
- **数据库驱动**: 
  - PostgreSQL: psycopg2-binary
  - MySQL: PyMySQL
  - SQL Server: pyodbc
  - Oracle: python-oracledb 2.0.0

### 前端技术
- **模板引擎**: Jinja2 3.1.2
- **样式框架**: Bootstrap 5.3.2
- **图标库**: Font Awesome 6.4.0
- **图表库**: Chart.js 4.4.0
- **JavaScript库**: jQuery 3.7.1

### 部署技术
- **容器化**: Docker 20.10.12 + Docker Compose 1.29.2
- **Web服务器**: Nginx (可选)
- **进程管理**: Gunicorn

## 开发环境启动

### 使用启动脚本
```bash
# 开发环境
./scripts/start_dev.sh

# 生产环境
./scripts/start_prod.sh
```

### 手动启动
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 数据要求

本项目严格要求使用真实数据，禁止使用任何形式的模拟数据、假数据或硬编码测试数据。所有数据必须通过真实数据库连接获取或通过脚本自动生成。

## 下一步开发

1. 实现数据模型和数据库迁移
2. 实现用户认证和权限系统
3. 实现数据库实例管理功能
4. 实现凭据管理功能
5. 实现账户统计和搜索功能
6. 实现定时任务系统
7. 实现全局参数管理
8. 实现日志管理系统
9. 完善前端界面
10. 实现测试套件
