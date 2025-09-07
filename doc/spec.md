# 泰摸鱼吧 - 技术规格文档

## 项目概述

**泰摸鱼吧** 是一个基于Flask的DBA数据库管理Web应用，提供多数据库实例管理、账户管理、任务调度、日志监控等功能。支持PostgreSQL、MySQL、SQL Server、Oracle等主流数据库。

### 核心特性

- 🔐 **用户认证与权限管理** - 基于Flask-Login的会话管理
- 🗄️ **多数据库实例管理** - 支持PostgreSQL、MySQL、SQL Server、Oracle
- 👥 **账户信息管理** - 数据库用户账户同步与管理
- 🔑 **凭据管理** - 安全的数据库连接凭据存储
- ⚙️ **系统参数管理** - 全局配置参数管理
- 📊 **任务调度系统** - 高度可定制化的任务管理
- 📈 **实时监控仪表板** - 系统状态和统计信息
- 📝 **操作日志记录** - 完整的审计日志
- 🚀 **RESTful API** - 完整的API接口

## 技术架构

### 技术栈

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **后端框架** | Flask | 3.0.3 | Web应用框架 |
| **模板引擎** | Jinja2 | 3.1.4 | 模板渲染 |
| **WSGI服务器** | Werkzeug | 3.0.3 | WSGI工具包 |
| **数据库ORM** | SQLAlchemy | 2.0.30 | 数据库ORM |
| **数据库迁移** | Flask-Migrate | 4.0.7 | 数据库版本管理 |
| **用户认证** | Flask-Login | 0.6.3 | 用户会话管理 |
| **密码加密** | Flask-Bcrypt | 1.0.1 | 密码哈希 |
| **JWT认证** | Flask-JWT-Extended | 4.6.0 | JWT令牌管理 |
| **缓存系统** | Flask-Caching | 2.1.0 | 缓存管理 |
| **任务队列** | Celery | 5.3.6 | 异步任务处理 |
| **消息代理** | Redis | 8.2.1 | 缓存和消息队列 |
| **前端框架** | Bootstrap | 5.3.2 | UI组件库 |
| **图标库** | Font Awesome | 6.4.0 | 图标库 |
| **时区处理** | pytz | 2023.3 | 时区转换 |

### 数据库支持

| 数据库 | 驱动 | 版本 | 状态 |
|--------|------|------|------|
| **PostgreSQL** | psycopg2-binary | 2.9.9 | ✅ 完全支持 |
| **MySQL** | PyMySQL | 1.1.1 | ✅ 完全支持 |
| **SQL Server** | pyodbc | 5.1.0 | ✅ 完全支持 |
| **SQL Server** | pymssql | 2.2.11 | ✅ 完全支持 |
| **Oracle** | cx_Oracle | 8.3.0 | ⚠️ 需要Oracle客户端 |

### 系统架构图

```mermaid
graph TB
    subgraph "前端层"
        A[Web浏览器] --> B[Bootstrap UI]
        B --> C[JavaScript/AJAX]
    end
    
    subgraph "应用层"
        C --> D[Flask应用]
        D --> E[路由控制器]
        E --> F[业务逻辑层]
        F --> G[服务层]
    end
    
    subgraph "数据层"
        G --> H[SQLAlchemy ORM]
        H --> I[SQLite/PostgreSQL]
        G --> J[Redis缓存]
        G --> K[文件存储]
    end
    
    subgraph "任务层"
        L[Celery Worker] --> M[任务执行器]
        M --> N[数据库连接池]
        N --> O[外部数据库]
    end
    
    subgraph "外部系统"
        P[PostgreSQL实例]
        Q[MySQL实例]
        R[SQL Server实例]
        S[Oracle实例]
    end
    
    D --> L
    N --> P
    N --> Q
    N --> R
    N --> S
```

## 数据模型设计

### 核心实体关系图

```mermaid
erDiagram
    User ||--o{ Log : creates
    User ||--o{ Instance : manages
    User ||--o{ Credential : manages
    User ||--o{ Task : creates
    
    Instance ||--o{ Account : contains
    Instance ||--o{ SyncData : generates
    Instance }o--|| Credential : uses
    
    Credential ||--o{ Instance : authenticates
    
    Task ||--o{ SyncData : executes
    Task }o--|| Instance : targets
    
    Account }o--|| Instance : belongs_to
    
    User {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role
        boolean is_active
        datetime created_at
        datetime updated_at
        datetime last_login
    }
    
    Instance {
        int id PK
        string name UK
        string db_type
        string host
        int port
        string database_name
        int credential_id FK
        text description
        json tags
        string status
        boolean is_active
        datetime last_connected
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    Credential {
        int id PK
        string name UK
        string username
        string password
        string db_type
        text description
        json config
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    Account {
        int id PK
        int instance_id FK
        string username
        string database_name
        string account_type
        boolean is_active
        datetime last_login
        datetime created_at
        datetime updated_at
    }
    
    Task {
        int id PK
        string name UK
        string task_type
        string db_type
        string schedule
        text description
        text python_code
        json config
        boolean is_active
        boolean is_builtin
        datetime last_run
        string last_status
        text last_message
        int run_count
        int success_count
        datetime created_at
        datetime updated_at
    }
    
    Log {
        int id PK
        int user_id FK
        string operation
        string resource_type
        int resource_id
        text details
        string ip_address
        string user_agent
        datetime created_at
    }
    
    SyncData {
        int id PK
        int instance_id FK
        int task_id FK
        string sync_type
        string status
        text message
        int synced_count
        datetime created_at
    }
    
    GlobalParam {
        int id PK
        string key UK
        text value
        string description
        string category
        boolean is_encrypted
        datetime created_at
        datetime updated_at
    }
```

### 数据模型详细说明

#### 1. 用户模型 (User)
- **功能**: 系统用户管理
- **字段**: 用户名、邮箱、密码哈希、角色、状态等
- **关系**: 一对多关联日志、实例、凭据、任务

#### 2. 实例模型 (Instance)
- **功能**: 数据库实例管理
- **字段**: 实例名、数据库类型、连接信息、状态等
- **关系**: 多对一关联凭据，一对多关联账户、同步数据

#### 3. 凭据模型 (Credential)
- **功能**: 数据库连接凭据管理
- **字段**: 凭据名、用户名、密码、数据库类型等
- **关系**: 一对多关联实例

#### 4. 账户模型 (Account)
- **功能**: 数据库用户账户管理
- **字段**: 用户名、数据库名、账户类型、状态等
- **关系**: 多对一关联实例

#### 5. 任务模型 (Task)
- **功能**: 任务调度管理
- **字段**: 任务名、类型、数据库类型、Python代码、配置等
- **关系**: 一对多关联同步数据

#### 6. 日志模型 (Log)
- **功能**: 操作审计日志
- **字段**: 操作用户、操作类型、资源信息、详情等
- **关系**: 多对一关联用户

#### 7. 同步数据模型 (SyncData)
- **功能**: 数据同步记录
- **字段**: 同步类型、状态、消息、同步数量等
- **关系**: 多对一关联实例和任务

#### 8. 全局参数模型 (GlobalParam)
- **功能**: 系统配置参数管理
- **字段**: 参数键、值、描述、分类、加密状态等

## API接口设计

### 认证接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| POST | `/auth/login` | 用户登录 | 无 |
| POST | `/auth/logout` | 用户登出 | 需要 |
| POST | `/auth/register` | 用户注册 | 无 |
| POST | `/auth/change-password` | 修改密码 | 需要 |

### 实例管理接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/instances/` | 获取实例列表 | 需要 |
| POST | `/instances/create` | 创建实例 | 需要 |
| GET | `/instances/<id>` | 获取实例详情 | 需要 |
| PUT | `/instances/<id>/edit` | 更新实例 | 需要 |
| DELETE | `/instances/<id>/delete` | 删除实例 | 需要 |
| POST | `/instances/<id>/test-connection` | 测试连接 | 需要 |
| GET | `/instances/statistics` | 实例统计 | 需要 |

### 凭据管理接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/credentials/` | 获取凭据列表 | 需要 |
| POST | `/credentials/create` | 创建凭据 | 需要 |
| GET | `/credentials/<id>` | 获取凭据详情 | 需要 |
| PUT | `/credentials/<id>/edit` | 更新凭据 | 需要 |
| DELETE | `/credentials/<id>/delete` | 删除凭据 | 需要 |
| POST | `/credentials/<id>/toggle` | 启用/禁用凭据 | 需要 |

### 账户管理接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/accounts/` | 账户统计首页 | 需要 |
| GET | `/accounts/list` | 账户列表 | 需要 |
| GET | `/accounts/api/statistics` | 账户统计API | 需要 |

### 任务管理接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/tasks/` | 获取任务列表 | 需要 |
| POST | `/tasks/create` | 创建任务 | 需要 |
| GET | `/tasks/<id>` | 获取任务详情 | 需要 |
| PUT | `/tasks/<id>/edit` | 更新任务 | 需要 |
| DELETE | `/tasks/<id>/delete` | 删除任务 | 需要 |
| POST | `/tasks/<id>/toggle` | 启用/禁用任务 | 需要 |
| POST | `/tasks/<id>/execute` | 执行任务 | 需要 |
| POST | `/tasks/create-builtin` | 创建内置任务 | 需要 |
| POST | `/tasks/execute-all` | 批量执行任务 | 需要 |

### 系统管理接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/dashboard/` | 仪表板首页 | 需要 |
| GET | `/dashboard/api/overview` | 系统概览API | 需要 |
| GET | `/logs/` | 日志管理 | 需要 |
| GET | `/params/` | 参数管理 | 需要 |
| GET | `/admin/` | 管理后台 | 需要 |

### 健康检查接口

| 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|
| GET | `/api/health` | 系统健康检查 | 无 |

## 任务调度系统

### 任务类型

| 类型 | 功能 | 数据库支持 | 说明 |
|------|------|------------|------|
| **sync_accounts** | 账户同步 | PostgreSQL, MySQL | 同步数据库用户账户信息 |
| **sync_version** | 版本同步 | PostgreSQL, MySQL | 同步数据库版本信息 |
| **sync_size** | 大小同步 | PostgreSQL, MySQL | 同步数据库大小信息 |
| **custom** | 自定义任务 | 全部 | 用户自定义Python代码 |

### 任务执行流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant T as 任务调度器
    participant E as 任务执行器
    participant D as 数据库
    participant I as 外部实例
    
    U->>T: 创建/触发任务
    T->>E: 执行任务
    E->>D: 查询匹配实例
    D-->>E: 返回实例列表
    
    loop 遍历每个实例
        E->>I: 连接数据库
        E->>E: 执行Python代码
        E->>D: 保存同步数据
        E->>D: 更新任务统计
    end
    
    E-->>T: 返回执行结果
    T-->>U: 显示执行状态
```

### 内置任务模板

#### PostgreSQL账户同步
```python
def sync_postgresql_accounts(instance, config):
    """同步PostgreSQL数据库账户信息"""
    # 连接数据库
    # 查询用户信息
    # 更新账户记录
    # 返回同步结果
```

#### MySQL账户同步
```python
def sync_mysql_accounts(instance, config):
    """同步MySQL数据库账户信息"""
    # 连接数据库
    # 查询用户权限
    # 更新账户记录
    # 返回同步结果
```

#### 版本同步任务
```python
def sync_postgresql_version(instance, config):
    """同步PostgreSQL数据库版本信息"""
    # 查询版本信息
    # 更新实例标签
    # 返回版本信息
```

## 安全设计

### 认证与授权

1. **用户认证**
   - 基于Flask-Login的会话管理
   - 密码使用bcrypt加密存储
   - 支持JWT令牌认证

2. **权限控制**
   - 基于角色的访问控制(RBAC)
   - 路由级别的权限验证
   - API接口认证保护

3. **数据安全**
   - 敏感数据加密存储
   - SQL注入防护
   - XSS攻击防护
   - CSRF保护

### 安全配置

```python
# 密码加密
bcrypt = Bcrypt()

# JWT配置
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# 会话安全
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF保护
CSRFProtect(app)

# CORS配置
CORS(app, origins=['http://localhost:5001'])
```

## 性能优化

### 数据库优化

1. **索引策略**
   - 主键自动索引
   - 外键索引
   - 查询字段索引
   - 复合索引优化

2. **查询优化**
   - 使用SQLAlchemy的join查询
   - 避免N+1查询问题
   - 分页查询优化
   - 查询结果缓存

3. **连接池管理**
   - 数据库连接池
   - Redis连接池
   - 外部数据库连接管理

### 缓存策略

1. **Redis缓存**
   - 用户会话缓存
   - 查询结果缓存
   - 任务执行结果缓存

2. **应用缓存**
   - 静态资源缓存
   - 模板缓存
   - 配置参数缓存

### 异步处理

1. **Celery任务队列**
   - 长时间运行的任务
   - 定时任务调度
   - 批量数据处理

2. **异步API**
   - 非阻塞的数据库操作
   - 异步任务执行
   - 实时状态更新

## 监控与日志

### 日志系统

1. **日志分类**
   - 应用日志 (app.log)
   - 认证日志 (auth.log)
   - 数据库日志 (database.log)
   - 安全日志 (security.log)
   - 同步日志 (sync.log)
   - API日志 (api.log)
   - 缓存日志 (cache.log)

2. **日志格式**
   - 结构化日志记录
   - 时间戳和时区处理
   - 用户操作追踪
   - 错误堆栈记录

3. **日志轮转**
   - 按大小轮转
   - 按时间轮转
   - 日志压缩存储
   - 历史日志清理

### 监控指标

1. **系统指标**
   - CPU使用率
   - 内存使用率
   - 磁盘使用率
   - 网络连接数

2. **应用指标**
   - 请求响应时间
   - 错误率统计
   - 任务执行成功率
   - 数据库连接状态

3. **业务指标**
   - 用户活跃度
   - 实例连接数
   - 同步任务执行次数
   - 数据同步量

## 部署架构

### 开发环境

```yaml
# 本地开发环境
services:
  app:
    build: .
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=sqlite:///instance.db
    volumes:
      - ./userdata:/app/userdata
  
  redis:
    image: redis:7.2.5
    ports:
      - "6379:6379"
    volumes:
      - ./userdata/redis:/data
```

### 生产环境

```yaml
# 生产环境
services:
  app:
    build: .
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@postgres:5432/taifish
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:16.3
    environment:
      - POSTGRES_DB=taifish
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7.2.5
    volumes:
      - redis_data:/data
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
```

## 开发规范

### 代码结构

```
app/
├── __init__.py          # 应用初始化
├── config.py            # 配置文件
├── models/              # 数据模型
│   ├── __init__.py
│   ├── user.py
│   ├── instance.py
│   ├── credential.py
│   ├── account.py
│   ├── task.py
│   ├── log.py
│   ├── global_param.py
│   └── sync_data.py
├── routes/              # 路由控制器
│   ├── __init__.py
│   ├── auth.py
│   ├── instances.py
│   ├── credentials.py
│   ├── accounts.py
│   ├── tasks.py
│   ├── dashboard.py
│   ├── logs.py
│   ├── params.py
│   ├── api.py
│   └── main.py
├── services/            # 业务服务层
│   ├── database_service.py
│   ├── database_drivers.py
│   └── task_executor.py
├── utils/               # 工具类
│   ├── logger.py
│   ├── security.py
│   ├── timezone.py
│   ├── cache_manager.py
│   ├── rate_limiter.py
│   ├── error_handler.py
│   └── env_manager.py
└── templates/           # 模板文件
    ├── base.html
    ├── auth/
    ├── instances/
    ├── credentials/
    ├── accounts/
    ├── tasks/
    ├── dashboard/
    ├── logs/
    ├── params/
    └── errors/
```

### 命名规范

1. **文件命名**
   - 使用小写字母和下划线
   - 模型文件使用单数形式
   - 路由文件使用复数形式

2. **类命名**
   - 使用大驼峰命名法
   - 模型类使用单数形式
   - 服务类以Service结尾

3. **函数命名**
   - 使用小写字母和下划线
   - 动词开头，描述功能
   - 私有方法以下划线开头

4. **变量命名**
   - 使用小写字母和下划线
   - 常量使用大写字母和下划线
   - 布尔变量使用is_、has_、can_前缀

### 代码质量

1. **代码注释**
   - 使用JSDoc风格的函数注释
   - 复杂逻辑添加行内注释
   - 类和模块添加文档字符串

2. **错误处理**
   - 使用try-catch处理异常
   - 记录详细的错误日志
   - 返回用户友好的错误信息

3. **测试覆盖**
   - 单元测试覆盖核心功能
   - 集成测试覆盖API接口
   - 端到端测试覆盖用户流程

## 版本历史

### v1.0.0 (2025-09-08)
- ✅ 基础用户认证系统
- ✅ 多数据库实例管理
- ✅ 凭据管理系统
- ✅ 账户信息管理
- ✅ 系统参数管理
- ✅ 任务调度系统
- ✅ 操作日志记录
- ✅ 实时监控仪表板
- ✅ RESTful API接口
- ✅ 安全防护机制
- ✅ 性能优化
- ✅ 完整的文档

## 未来规划

### 短期目标 (v1.1.0)
- [ ] 数据库备份与恢复
- [ ] 数据导入导出功能
- [ ] 更丰富的监控指标
- [ ] 移动端适配

### 中期目标 (v1.2.0)
- [ ] 多租户支持
- [ ] 插件系统
- [ ] 自动化运维
- [ ] 机器学习集成

### 长期目标 (v2.0.0)
- [ ] 微服务架构
- [ ] 云原生部署
- [ ] 大数据分析
- [ ] AI智能运维

---

**文档版本**: v1.0.0  
**最后更新**: 2025-09-08  
**维护者**: 泰摸鱼吧开发团队