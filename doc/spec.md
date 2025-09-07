# 泰摸鱼吧 - 详细技术规格文档

## 1. 项目概述

### 1.1 项目信息
- **项目名称**: 泰摸鱼吧 (TaifishV4)
- **项目类型**: DBA数据库管理Web应用
- **技术栈**: Flask 3.0.3 + SQLite (开发) / PostgreSQL (生产) + Redis 8.2.1 + Celery 5.3.6
- **部署方式**: 本地开发 + Docker容器化生产环境
- **开发模式**: 前后端统一使用Flask + Jinja2模板
- **当前状态**: 开发环境已部署完成，数据库和Redis服务正常运行

### 1.2 核心功能
1. **用户认证与权限管理** - 基于JWT的RBAC权限控制
2. **数据库实例管理** - 支持SQL Server/MySQL/Oracle实例CRUD
3. **凭据管理** - 全局凭据存储与加密
4. **账户信息统计** - 多维度数据统计分析
5. **账户搜索筛选** - 分数据库类型的账户查询
6. **定时任务管理** - 模块化同步任务调度
7. **全局参数管理** - 系统配置参数统一管理
8. **操作日志记录** - 完整的系统变更审计

### 1.3 数据要求
- **严格禁止**: 代码中不得包含任何模拟数据、假数据或硬编码测试数据
- **真实数据**: 所有数据必须来自真实数据库连接或通过脚本自动生成
- **数据生成**: 提供完整的数据生成脚本，支持开发和生产环境数据初始化

## 2. 系统架构设计

### 2.1 整体架构图

```mermaid
graph TB
    subgraph "前端层"
        A[Flask Web Server]
        B[Jinja2 Templates]
        C[Static Assets]
    end
    
    subgraph "应用层"
        D[Flask Routes]
        E[API Endpoints]
        F[Business Logic]
    end
    
    subgraph "服务层"
        G[Authentication Service]
        H[Database Service]
        I[Cache Service]
        J[Task Service]
    end
    
    subgraph "数据层"
        K[PostgreSQL]
        L[Redis Cache]
        M[File Storage]
    end
    
    subgraph "外部系统"
        N[SQL Server]
        O[MySQL]
        P[Oracle]
    end
    
    A --> D
    B --> A
    D --> E
    E --> F
    F --> G
    F --> H
    F --> I
    F --> J
    G --> K
    H --> K
    I --> L
    J --> L
    H --> N
    H --> O
    H --> P
```

### 2.2 模块关系图

```mermaid
graph LR
    subgraph "核心模块"
        A[用户管理]
        B[实例管理]
        C[凭据管理]
        D[账户统计]
        E[账户搜索]
        F[定时任务]
        G[全局参数]
        H[日志管理]
    end
    
    subgraph "支撑模块"
        I[认证服务]
        J[权限控制]
        K[缓存服务]
        L[数据同步]
    end
    
    A --> I
    B --> I
    C --> I
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    
    A --> J
    B --> J
    C --> J
    D --> J
    E --> J
    F --> J
    G --> J
    H --> J
    
    B --> K
    C --> K
    D --> K
    E --> K
    F --> K
    G --> K
    H --> K
    
    B --> L
    F --> L
```

## 3. 数据库设计

### 3.1 数据库表结构

```mermaid
erDiagram
    Users {
        int id PK
        varchar username UK
        varchar password
        varchar role
        datetime created_at
        datetime last_login
    }
    
    Instances {
        int id PK
        varchar name
        varchar db_type
        varchar host
        int port
        int credential_id FK
        text description
        json tags
        datetime deleted_at
    }
    
    Credentials {
        int id PK
        varchar name
        varchar credential_type
        varchar db_type
        varchar username
        varchar password
        json instance_ids
        int category_id FK
        datetime deleted_at
    }
    
    Accounts {
        int id PK
        varchar username
        varchar db_type
        int instance_id FK
        datetime created_at
        datetime last_active
        json permissions
        int category_id FK
    }
    
    Tasks {
        int id PK
        int instance_id FK
        varchar sync_type
        varchar db_type
        varchar frequency
        varchar time_window
        datetime last_run
        varchar status
        text log
        json code
        datetime deleted_at
    }
    
    Logs {
        int id PK
        varchar operation_type
        int user_id FK
        datetime timestamp
        json details
        varchar status
    }
    
    Global_Params {
        int id PK
        varchar param_type
        varchar name
        json config
        datetime deleted_at
    }
    
    Sync_Data {
        int id PK
        varchar sync_type
        int instance_id FK
        json data
        datetime sync_time
    }
    
    Users ||--o{ Logs : creates
    Instances ||--o{ Accounts : contains
    Instances ||--o{ Tasks : has
    Instances ||--o{ Sync_Data : generates
    Credentials ||--o{ Instances : used_by
    Accounts }o--|| Instances : belongs_to
    Tasks }o--|| Instances : runs_on
```

### 3.2 数据生成脚本要求

#### 3.2.1 初始化数据脚本
```python
# scripts/init_data.py
"""
数据初始化脚本 - 生成真实可用的初始数据
禁止使用模拟数据，必须生成真实可连接的数据
"""

def init_global_params():
    """初始化全局参数 - 真实配置数据"""
    pass

def init_database_types():
    """初始化数据库类型配置"""
    pass

def init_credential_types():
    """初始化凭据类型配置"""
    pass

def init_sync_types():
    """初始化同步类型配置"""
    pass

def init_role_types():
    """初始化角色类型配置"""
    pass

def init_sample_instances():
    """初始化示例数据库实例 - 必须可真实连接"""
    pass

def init_sample_credentials():
    """初始化示例凭据 - 真实凭据信息"""
    pass

def init_admin_user():
    """初始化管理员用户"""
    pass
```

#### 3.2.2 数据生成器
```python
# scripts/data_generator.py
"""
数据生成器 - 用于生成测试和生产环境数据
所有生成的数据必须真实可用，不得使用假数据
"""

class DatabaseInstanceGenerator:
    """数据库实例生成器"""
    def generate_sql_server_instances(self):
        """生成SQL Server实例 - 使用真实连接信息"""
        pass
    
    def generate_mysql_instances(self):
        """生成MySQL实例 - 使用真实连接信息"""
        pass
    
    def generate_oracle_instances(self):
        """生成Oracle实例 - 使用真实连接信息"""
        pass

class CredentialGenerator:
    """凭据生成器"""
    def generate_database_credentials(self):
        """生成数据库凭据 - 真实凭据信息"""
        pass

class AccountDataGenerator:
    """账户数据生成器"""
    def sync_real_account_data(self, instance_id):
        """同步真实账户数据 - 从实际数据库获取"""
        pass
```

## 4. API设计规范

### 4.1 认证API

```mermaid
sequenceDiagram
    participant C as Client
    participant A as Auth Service
    participant R as Redis
    participant D as Database
    
    C->>A: POST /api/auth/login
    A->>D: 验证用户凭据
    D-->>A: 返回用户信息
    A->>R: 存储JWT令牌
    A-->>C: 返回认证令牌
```

### 4.2 实例管理API

```mermaid
sequenceDiagram
    participant C as Client
    participant I as Instance Service
    participant R as Redis
    participant D as Database
    participant DB as External DB
    
    C->>I: POST /api/instances
    I->>D: 保存实例信息
    I->>DB: 测试连接
    DB-->>I: 连接结果
    I->>R: 缓存实例状态
    I-->>C: 返回实例信息
```

## 5. 缓存策略

### 5.1 Redis缓存键设计

```mermaid
graph TD
    A[Redis Cache Keys] --> B[Session Keys]
    A --> C[Data Keys]
    A --> D[Status Keys]
    
    B --> B1[session:user_id]
    B --> B2[user:role:user_id]
    
    C --> C1[instances:list]
    C --> C2[instance:instance_id]
    C --> C3[credentials:list]
    C --> C4[account:stats:user_id]
    
    D --> D1[sync:status:instance_id]
    D --> D2[task:status:task_id]
```

### 5.2 缓存失效策略

| 数据类型 | TTL | 失效条件 |
|---------|-----|----------|
| 用户会话 | 1小时 | 登出/过期 |
| 实例列表 | 10分钟 | 实例变更 |
| 凭据列表 | 10分钟 | 凭据变更 |
| 统计数据 | 5分钟 | 数据同步 |
| 任务状态 | 10分钟 | 任务完成 |

## 6. 安全规范

### 6.1 数据加密

```mermaid
graph LR
    A[敏感数据] --> B[bcrypt加密]
    A --> C[AES加密]
    B --> D[密码存储]
    C --> E[凭据存储]
    D --> F[数据库]
    E --> F
```

### 6.2 权限控制流程

```mermaid
flowchart TD
    A[用户请求] --> B{验证JWT}
    B -->|无效| C[返回401]
    B -->|有效| D{检查角色权限}
    D -->|无权限| E[返回403]
    D -->|有权限| F[执行业务逻辑]
    F --> G[记录操作日志]
    G --> H[返回结果]
```

## 7. 部署架构

### 7.1 Docker容器架构

```mermaid
graph TB
    subgraph "Docker Compose"
        A[Flask App Container]
        B[PostgreSQL Container]
        C[Redis Container]
        D[Celery Worker Container]
        E[Celery Beat Container]
    end
    
    subgraph "External Systems"
        F[SQL Server]
        G[MySQL]
        H[Oracle]
    end
    
    A --> B
    A --> C
    D --> C
    E --> C
    A --> F
    A --> G
    A --> H
    D --> F
    D --> G
    D --> H
```

### 7.2 环境配置

#### 7.2.1 开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  flask:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://user:pass@postgres:5432/taifish_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:13.5
    environment:
      - POSTGRES_DB=taifish_dev
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

#### 7.2.2 生产环境
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  flask:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@postgres:5432/taifish_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:13.5
    environment:
      - POSTGRES_DB=taifish_prod
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
  
  redis:
    image: redis:4.0.2
    command: redis-server --appendonly yes --requirepass your_redis_password
    volumes:
      - redis_data:/data
```

## 8. 测试规范

### 8.1 测试数据要求

```python
# tests/test_data_requirements.py
"""
测试数据要求 - 确保所有测试使用真实数据
禁止在测试中使用模拟数据或假数据
"""

class TestDataRequirements:
    def test_no_mock_data_in_code(self):
        """确保代码中不包含模拟数据"""
        pass
    
    def test_real_database_connections(self):
        """确保使用真实数据库连接进行测试"""
        pass
    
    def test_data_generation_scripts(self):
        """测试数据生成脚本的有效性"""
        pass
```

### 8.2 测试覆盖范围

```mermaid
graph TD
    A[测试覆盖] --> B[单元测试]
    A --> C[集成测试]
    A --> D[API测试]
    A --> E[缓存测试]
    A --> F[任务测试]
    
    B --> B1[用户管理]
    B --> B2[实例管理]
    B --> B3[凭据管理]
    B --> B4[权限控制]
    
    C --> C1[数据库交互]
    C --> C2[Redis缓存]
    C --> C3[外部数据库连接]
    
    D --> D1[认证API]
    D --> D2[CRUD API]
    D --> D3[搜索API]
    D --> D4[同步API]
    
    E --> E1[缓存命中率]
    E --> E2[缓存失效]
    E --> E3[缓存性能]
    
    F --> F1[定时任务]
    F --> F2[数据同步]
    F --> F3[任务调度]
```

## 9. 监控与日志

### 9.1 系统监控

```mermaid
graph LR
    A[系统监控] --> B[性能监控]
    A --> C[错误监控]
    A --> D[业务监控]
    
    B --> B1[响应时间]
    B --> B2[吞吐量]
    B --> B3[资源使用率]
    
    C --> C1[错误率]
    C --> C2[异常日志]
    C --> C3[系统告警]
    
    D --> D1[用户活跃度]
    D --> D2[数据同步状态]
    D --> D3[任务执行情况]
```

### 9.2 日志规范

```python
# 日志格式规范
LOG_FORMAT = {
    'timestamp': '2025-01-27T10:30:00Z',
    'level': 'INFO',
    'module': 'user_management',
    'function': 'create_user',
    'user_id': 123,
    'operation': 'user_create',
    'status': 'success',
    'details': {
        'username': 'admin',
        'role': 'admin'
    }
}
```

## 10. 数据迁移与备份

### 10.1 数据迁移策略

```mermaid
flowchart TD
    A[数据迁移] --> B[结构迁移]
    A --> C[数据迁移]
    A --> D[验证迁移]
    
    B --> B1[创建表结构]
    B --> B2[创建索引]
    B --> B3[创建约束]
    
    C --> C1[迁移用户数据]
    C --> C2[迁移实例数据]
    C --> C3[迁移凭据数据]
    
    D --> D1[数据完整性检查]
    D --> D2[性能测试]
    D --> D3[功能验证]
```

### 10.2 备份策略

| 数据类型 | 备份频率 | 保留期限 | 存储位置 |
|---------|----------|----------|----------|
| 数据库 | 每日 | 30天 | 本地+云存储 |
| Redis | 每日 | 7天 | 本地存储 |
| 配置文件 | 每周 | 90天 | 版本控制 |
| 日志文件 | 每日 | 30天 | 本地存储 |

## 11. 性能要求

### 11.1 响应时间要求

| 操作类型 | 目标响应时间 | 最大响应时间 |
|---------|-------------|-------------|
| 页面加载 | < 2秒 | < 5秒 |
| API调用 | < 500ms | < 2秒 |
| 数据库查询 | < 100ms | < 1秒 |
| 缓存查询 | < 10ms | < 50ms |
| 连接测试 | < 10秒 | < 30秒 |
| 数据同步 | < 1分钟 | < 5分钟 |

### 11.2 并发要求

- **同时在线用户**: 100+
- **API并发请求**: 500+ QPS
- **数据库连接池**: 20-50个连接
- **Redis连接池**: 10-20个连接

## 12. 开发规范

### 12.1 代码规范

```python
# 代码注释规范
def sync_account_data(instance_id: int, sync_type: str) -> dict:
    """
    同步账户数据
    
    Args:
        instance_id (int): 数据库实例ID
        sync_type (str): 同步类型
        
    Returns:
        dict: 同步结果，包含状态和数据量
        
    Raises:
        DatabaseConnectionError: 数据库连接失败
        SyncDataError: 数据同步失败
        
    Note:
        此函数会连接真实数据库获取账户数据，
        禁止使用模拟数据或假数据
    """
    pass
```

### 12.2 错误处理规范

```python
# 错误处理示例
try:
    result = sync_real_database_data(instance_id)
except DatabaseConnectionError as e:
    logger.error(f"数据库连接失败: {e}")
    return {"status": "error", "message": "数据库连接失败"}
except SyncDataError as e:
    logger.error(f"数据同步失败: {e}")
    return {"status": "error", "message": "数据同步失败"}
except Exception as e:
    logger.error(f"未知错误: {e}")
    return {"status": "error", "message": "系统内部错误"}
```

## 13. 扩展性设计

### 13.1 模块扩展接口

```python
# 扩展接口设计
class SyncModuleInterface:
    """同步模块接口"""
    def sync_data(self, instance_id: int) -> dict:
        """同步数据 - 子类必须实现"""
        raise NotImplementedError
    
    def validate_connection(self, instance_config: dict) -> bool:
        """验证连接 - 子类必须实现"""
        raise NotImplementedError

class DatabaseSyncModule(SyncModuleInterface):
    """数据库同步模块基类"""
    pass

class MySQLSyncModule(DatabaseSyncModule):
    """MySQL同步模块"""
    pass

class SQLServerSyncModule(DatabaseSyncModule):
    """SQL Server同步模块"""
    pass

class OracleSyncModule(DatabaseSyncModule):
    """Oracle同步模块"""
    pass
```

### 13.2 配置扩展

```python
# 配置扩展设计
class ConfigManager:
    """配置管理器"""
    def load_database_config(self, db_type: str) -> dict:
        """加载数据库配置"""
        pass
    
    def load_sync_config(self, sync_type: str) -> dict:
        """加载同步配置"""
        pass
    
    def load_credential_config(self, cred_type: str) -> dict:
        """加载凭据配置"""
        pass
```

## 14. 质量保证

### 14.1 代码质量检查

```yaml
# .github/workflows/quality-check.yml
name: Quality Check
on: [push, pull_request]
jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run linting
        run: flake8 .
      - name: Run type checking
        run: mypy .
      - name: Run security check
        run: bandit -r .
      - name: Check for mock data
        run: python scripts/check_mock_data.py
```

### 14.2 数据质量检查

```python
# scripts/check_data_quality.py
"""
数据质量检查脚本
确保所有数据都是真实可用的，没有模拟数据
"""

def check_no_mock_data():
    """检查代码中是否包含模拟数据"""
    pass

def check_real_database_connections():
    """检查数据库连接是否真实可用"""
    pass

def check_data_integrity():
    """检查数据完整性"""
    pass
```

---

**重要提醒**: 本规格文档严格要求所有代码实现必须使用真实数据，禁止使用任何形式的模拟数据、假数据或硬编码测试数据。所有数据必须通过真实数据库连接获取或通过脚本自动生成。
