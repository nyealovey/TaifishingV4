# 泰摸鱼吧 - 企业级数据同步管理平台

## 项目简介

泰摸鱼吧是一个基于Flask的企业级数据同步管理平台，专为DBA和数据分析师设计，提供统一的数据源管理、同步任务调度和监控功能。

## 主要功能

- **用户认证系统**: 基于Flask-Login的完整用户管理
- **数据库实例管理**: 支持多种数据库类型的连接管理
- **凭据安全管理**: 安全的数据库凭据存储和管理
- **定时任务管理**: 基于Celery的异步任务调度
- **系统参数配置**: 灵活的系统参数管理
- **操作日志记录**: 完整的操作审计日志
- **账户统计分析**: 数据同步统计和分析
- **系统仪表板**: 实时系统监控和状态展示
- **API状态监控**: 完整的API健康检查

## 技术栈

- **后端**: Flask 3.0.3, SQLAlchemy 2.0.30, Celery 5.3.6
- **数据库**: PostgreSQL 16.3, SQLite (开发环境)
- **缓存**: Redis 7.2.5
- **前端**: Bootstrap 5, Chart.js, Font Awesome
- **容器化**: Docker, Docker Compose
- **部署**: Gunicorn, Nginx

## 快速开始

### 本地开发环境

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
pip install -r requirements-local.txt
```

4. **初始化数据库**
```bash
python scripts/init_database.py
```

5. **启动开发服务器**
```bash
python app.py
```

6. **访问应用**
- 访问地址: http://localhost:5001
- 默认登录: admin/admin123

### Docker环境

1. **启动完整测试环境**
```bash
cd docker
./scripts/start_full_test.sh
```

2. **访问应用**
- 访问地址: http://localhost:5001
- 默认登录: admin/admin123

## 项目结构

```
TaifishV4/
├── app/                    # Flask应用核心
│   ├── models/            # 数据模型
│   ├── routes/            # 路由控制器
│   ├── services/          # 业务服务
│   ├── templates/         # HTML模板
│   └── utils/             # 工具函数
├── docker/                # Docker配置
├── doc/                   # 项目文档
├── scripts/               # 脚本文件
├── tests/                 # 测试文件
└── requirements*.txt      # 依赖文件
```

## 支持的数据库

- PostgreSQL
- MySQL
- SQL Server
- Oracle

## 开发指南

详细的开发指南请参考 [doc/development/](doc/development/) 目录下的文档。

## 部署指南

详细的部署指南请参考 [doc/deployment/](doc/deployment/) 目录下的文档。

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目链接: [https://github.com/nyealovey/TaifishingV4](https://github.com/nyealovey/TaifishingV4)
- 问题反馈: [Issues](https://github.com/nyealovey/TaifishingV4/issues)

## 更新日志

### v1.0.0 (2025-09-07)

#### 新增功能
- ✅ 完整的用户认证系统
- ✅ 数据库实例管理 (支持PostgreSQL, MySQL, SQL Server, Oracle)
- ✅ 凭据安全管理
- ✅ 定时任务管理
- ✅ 系统参数配置
- ✅ 操作日志记录
- ✅ 账户统计分析
- ✅ 系统仪表板监控
- ✅ API状态监控页面

#### 技术特性
- ✅ 基于Flask 3.0.3的现代化Web框架
- ✅ SQLAlchemy 2.0.30 ORM支持
- ✅ Redis缓存和Celery异步任务
- ✅ 响应式Bootstrap 5界面
- ✅ Chart.js数据可视化
- ✅ 完整的错误处理和日志记录
- ✅ Docker容器化支持
- ✅ 数据库迁移管理

#### 修复问题
- ✅ 修复仪表盘API认证问题
- ✅ 修复SQLAlchemy case()函数语法错误
- ✅ 修复Redis状态检测问题
- ✅ 修复模板变量默认值处理
- ✅ 修复实例编辑功能
- ✅ 修复所有缺失的模板文件
- ✅ 优化系统状态监控

#### 项目文档
- ✅ 完整的技术规格文档
- ✅ 详细的开发环境搭建指南
- ✅ 数据库迁移文档
- ✅ 故障排除指南
- ✅ API文档和使用说明