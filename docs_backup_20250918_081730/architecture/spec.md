# 泰摸鱼吧 - 技术规格文档

## 项目概述

**泰摸鱼吧** 是一个基于Flask的DBA数据库管理Web应用，提供多数据库实例管理、账户管理、任务调度、日志监控等功能。支持PostgreSQL、MySQL、SQL Server、Oracle等主流数据库。

### 核心特性

- 🔐 **用户认证与权限管理** - 基于Flask-Login的会话管理，支持JWT令牌认证
- 🗄️ **多数据库实例管理** - 支持PostgreSQL、MySQL、SQL Server、Oracle
- 👥 **账户信息管理** - 数据库用户账户同步与管理，支持权限信息实时查询
- 🏷️ **账户分类管理** - 智能账户分类与权限规则管理
  - 🎯 自动分类 - 基于权限规则自动分类账户
  - 📋 分类规则 - 支持MySQL、SQL Server、PostgreSQL、Oracle权限规则
  - 🔍 权限扫描 - 实时扫描账户权限信息
  - 📊 分类统计 - 高风险账户、特权账户统计
  - ⚙️ 规则管理 - 灵活的权限规则配置
  - 🔄 多分类支持 - 支持账户匹配多个分类规则
  - 🔧 功能修复 - 修复权限显示、分类规则评估、账户管理页面等问题
- 🔑 **凭据管理** - 安全的数据库连接凭据存储
- ⏰ **定时任务管理系统** - 高度可定制化的定时任务调度平台
  - 🚀 快速创建内置任务 - 一键创建常用同步任务
  - 📊 批量任务管理 - 支持批量启用/禁用/执行任务
  - 📈 执行统计监控 - 详细的运行统计和成功率分析
  - 🔄 实时任务执行 - 支持立即执行和定时执行
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
| **任务调度** | APScheduler | 3.10.4 | 定时任务调度 |
| **消息代理** | Redis | 8.2.1 | 缓存和消息队列 |
| **前端框架** | Bootstrap | 5.3.2 | UI组件库 |
| **图标库** | Font Awesome | 6.4.0 | 图标库 |
| **时区处理** | pytz | 2023.3 | 时区转换 |

### 数据库支持

| 数据库 | 驱动 | 版本 | 状态 | 权限支持 |
|--------|------|------|------|----------|
| **PostgreSQL** | psycopg2-binary | 2.9.9 | ✅ 完全支持 | 角色属性、数据库权限、表空间权限 |
| **MySQL** | PyMySQL | 1.1.1 | ✅ 完全支持 | 全局权限、数据库权限 |
| **SQL Server** | pyodbc | 5.1.0 | ✅ 完全支持 | 服务器角色、服务器权限、数据库角色、数据库权限 |
| **SQL Server** | pymssql | 2.2.11 | ✅ 完全支持 | 服务器角色、服务器权限、数据库角色、数据库权限 |
| **Oracle** | python-oracledb | 2.0.0 | ✅ 完全支持 | 系统权限、角色、表空间权限、表空间配额 |

### 数据库类型抽象架构

#### 设计目标
- **统一管理**: 集中管理所有数据库类型配置
- **动态扩展**: 支持通过界面动态添加新数据库类型
- **类型安全**: 使用枚举和验证确保数据一致性
- **配置复用**: 避免重复配置信息
- **维护简单**: 修改配置只需在一个地方

#### 核心组件

##### 1. 数据库类型管理器 (DatabaseTypeManager)
```python
# 核心功能
- 数据库类型配置管理
- 支持状态控制
- 特性标签管理
- 排序和显示控制
- 系统内置类型保护
```

##### 2. 连接工厂模式 (ConnectionFactory)
```python
# 设计模式
- 抽象连接工厂基类
- 具体数据库连接实现
- 统一连接管理接口
- 连接池管理
- 连接测试和验证
```

##### 3. 权限查询抽象 (PermissionQueryFactory)
```python
# 权限管理
- 统一权限查询接口
- 数据库特定权限实现
- 权限数据标准化
- 权限规则管理
```

#### 数据库类型配置模型

```mermaid
erDiagram
    DatabaseTypeConfig {
        int id PK
        string name UK "数据库类型名称"
        string display_name "显示名称"
        string driver "驱动名称"
        int default_port "默认端口"
        string default_schema "默认Schema"
        int connection_timeout "连接超时"
        text description "描述信息"
        string icon "图标类名"
        string color "主题颜色"
        text features "特性列表(JSON)"
        boolean is_active "是否启用"
        boolean is_system "是否系统内置"
        int sort_order "排序顺序"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
    }

    Instance }o--|| DatabaseTypeConfig : uses
    Task }o--|| DatabaseTypeConfig : targets
```

#### 系统架构更新

```mermaid
graph TB
    subgraph "前端层"
        A[Web浏览器] --> B[Bootstrap UI]
        B --> C[JavaScript/AJAX]
        C --> D[数据库类型管理界面]
        C --> E[实例管理界面]
        C --> F[任务管理界面]
    end

    subgraph "应用层"
        D --> G[Flask应用]
        E --> G
        F --> G
        G --> H[路由控制器]
        H --> I[业务逻辑层]
        I --> J[服务层]
        J --> K[数据库类型服务]
        J --> L[连接工厂]
        J --> M[权限查询工厂]
    end

    subgraph "数据层"
        J --> N[SQLAlchemy ORM]
        N --> O[SQLite/PostgreSQL]
        J --> P[Redis缓存]
        J --> Q[文件存储]
    end

    subgraph "数据库类型管理"
        K --> R[DatabaseTypeConfig]
        R --> S[系统内置类型]
        R --> T[自定义类型]
        L --> U[MySQL连接工厂]
        L --> V[PostgreSQL连接工厂]
        L --> W[SQL Server连接工厂]
        L --> X[Oracle连接工厂]
    end

    subgraph "外部数据库"
        Y[PostgreSQL实例]
        Z[MySQL实例]
        AA[SQL Server实例]
        BB[Oracle实例]
        CC[其他数据库实例]
    end

    U --> Z
    V --> Y
    W --> AA
    X --> BB
    L --> CC
```

#### 功能特性

##### 数据库类型管理界面
- **动态管理**: 通过界面添加、编辑、删除数据库类型
- **系统保护**: 系统内置类型不能删除，只能修改部分字段
- **状态控制**: 可以启用/禁用数据库类型
- **排序管理**: 支持自定义排序顺序
- **特性标识**: 支持为每个数据库类型添加特性标签
- **使用检查**: 删除前检查是否有实例在使用

##### 连接管理优化
- **统一接口**: 所有数据库连接通过统一接口创建
- **连接池**: 支持连接池管理，提高性能
- **错误处理**: 统一的错误处理和重试机制
- **连接测试**: 自动连接测试和验证

##### 权限查询标准化
- **统一格式**: 所有数据库权限查询返回统一格式
- **类型安全**: 使用强类型确保数据一致性
- **扩展性**: 易于添加新的数据库类型支持

### 系统架构图

```mermaid
graph TB
    subgraph "前端层"
        A[Web浏览器] --> B[Bootstrap UI]
        B --> C[JavaScript/AJAX]
        C --> D[任务管理界面]
        C --> E[批量操作界面]
        C --> F[快速创建界面]
    end

    subgraph "应用层"
        D --> G[Flask应用]
        E --> G
        F --> G
        G --> H[路由控制器]
        H --> I[业务逻辑层]
        I --> J[服务层]
        J --> K[任务调度服务]
    end

    subgraph "数据层"
        J --> L[SQLAlchemy ORM]
        L --> M[SQLite/PostgreSQL]
        J --> N[Redis缓存]
        J --> O[文件存储]
    end

    subgraph "任务执行层"
        K --> P[任务执行器]
        P --> Q[批量任务处理器]
        P --> R[快速任务创建器]
        P --> S[数据库连接池]
        S --> T[外部数据库]
    end

    subgraph "外部系统"
        U[PostgreSQL实例]
        V[MySQL实例]
        W[SQL Server实例]
        X[Oracle实例]
    end

    G --> K
    T --> U
    T --> V
    T --> W
    T --> X

    subgraph "任务类型"
        Y[账户同步任务]
        Z[版本同步任务]
        AA[大小同步任务]
        BB[自定义任务]
    end

    P --> Y
    P --> Z
    P --> AA
    P --> BB
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
        string host
        string plugin
        boolean password_expired
        datetime password_last_changed
        boolean is_locked
        text permissions
        boolean is_superuser
        boolean can_grant
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

    AccountClassification {
        int id PK
        string name UK
        text description
        string risk_level
        string color
        int priority
        boolean is_active
        boolean is_system
        datetime created_at
        datetime updated_at
    }

    ClassificationRule {
        int id PK
        int classification_id FK
        string db_type
        string rule_name
        text rule_expression
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    AccountClassificationAssignment {
        int id PK
        int account_id FK
        int classification_id FK
        int assigned_by FK
        string assignment_type
        float confidence_score
        text notes
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    PermissionConfig {
        int id PK
        string db_type
        string category
        string permission_name
        text description
        boolean is_active
        int sort_order
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

#### 9. 账户分类模型 (AccountClassification)
- **功能**: 账户分类定义管理
- **字段**: 分类名、描述、风险级别、颜色、优先级、系统标识等
- **关系**: 一对多关联分类规则和分类分配

#### 10. 分类规则模型 (ClassificationRule)
- **功能**: 账户分类规则定义
- **字段**: 规则名、数据库类型、规则表达式、状态等
- **关系**: 多对一关联账户分类

#### 11. 账户分类分配模型 (AccountClassificationAssignment)
- **功能**: 账户与分类的关联关系
- **字段**: 分配类型、置信度、备注、状态等
- **关系**: 多对一关联账户和分类

#### 12. 权限配置模型 (PermissionConfig)
- **功能**: 数据库权限配置管理
- **字段**: 数据库类型、权限类别、权限名、描述、排序等

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

| 方法 | 路径 | 功能 | 认证 | 说明 |
|------|------|------|------|------|
| GET | `/tasks/` | 获取任务列表 | 需要 | 支持分页和筛选 |
| POST | `/tasks/create` | 创建任务 | 需要 | 创建自定义任务 |
| GET | `/tasks/<id>` | 获取任务详情 | 需要 | 获取单个任务信息 |
| PUT | `/tasks/<id>/edit` | 更新任务 | 需要 | 更新任务配置 |
| DELETE | `/tasks/<id>/delete` | 删除任务 | 需要 | 删除指定任务 |
| POST | `/tasks/<id>/toggle` | 启用/禁用任务 | 需要 | 切换任务状态 |
| POST | `/tasks/<id>/execute` | 执行任务 | 需要 | 立即执行单个任务 |
| POST | `/tasks/create-builtin` | 创建内置任务 | 需要 | 创建所有内置任务 |
| POST | `/tasks/create-quick` | 快速创建任务 | 需要 | 按类型快速创建任务 |
| POST | `/tasks/batch-toggle` | 批量启用/禁用 | 需要 | 批量切换任务状态 |
| POST | `/tasks/batch-execute` | 批量执行任务 | 需要 | 批量执行选中任务 |
| POST | `/tasks/execute-all` | 执行所有任务 | 需要 | 执行所有活跃任务 |

### 账户分类管理接口

| 方法 | 路径 | 功能 | 认证 | 说明 |
|------|------|------|------|------|
| GET | `/account-classification/` | 分类管理首页 | 需要 | 显示分类和规则列表 |
| GET | `/account-classification/classifications` | 获取分类列表 | 需要 | 获取所有账户分类 |
| POST | `/account-classification/classifications` | 创建分类 | 需要 | 创建新的账户分类 |
| PUT | `/account-classification/classifications/<id>` | 更新分类 | 需要 | 更新分类信息 |
| DELETE | `/account-classification/classifications/<id>` | 删除分类 | 需要 | 删除指定分类 |
| GET | `/account-classification/rules` | 获取规则列表 | 需要 | 获取所有分类规则 |
| POST | `/account-classification/rules` | 创建规则 | 需要 | 创建新的分类规则 |
| PUT | `/account-classification/rules/<id>` | 更新规则 | 需要 | 更新规则配置 |
| DELETE | `/account-classification/rules/<id>` | 删除规则 | 需要 | 删除指定规则 |
| POST | `/account-classification/auto-classify` | 自动分类 | 需要 | 执行自动分类操作 |
| GET | `/account-classification/permissions/<db_type>` | 获取权限配置 | 需要 | 获取指定数据库类型的权限配置 |

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

## 定时任务管理系统

### 系统概述

泰摸鱼吧的定时任务管理系统是一个高度可定制化的任务调度平台，支持多种数据库类型的自动化同步任务。系统提供了直观的Web界面和强大的API接口，让用户能够轻松创建、管理和监控各种定时任务。

### 核心功能

- 🚀 **快速创建内置任务** - 一键创建常用同步任务
- ⏰ **定时任务调度** - 支持Cron表达式的定时执行
- 📊 **批量任务管理** - 支持批量启用/禁用/执行任务
- 📈 **执行统计监控** - 详细的运行统计和成功率分析
- 🔄 **实时任务执行** - 支持立即执行和定时执行
- 🎯 **智能任务匹配** - 根据数据库类型自动匹配实例

### 任务类型

| 类型 | 功能 | 数据库支持 | 调度频率 | 说明 |
|------|------|------------|----------|------|
| **sync_accounts** | 账户同步 | PostgreSQL, MySQL, SQL Server, Oracle | 每6小时 | 同步数据库用户账户信息 |
| **sync_version** | 版本同步 | PostgreSQL, MySQL, SQL Server, Oracle | 每天 | 同步数据库版本信息 |
| **sync_size** | 大小同步 | PostgreSQL, MySQL, SQL Server, Oracle | 每天凌晨2点 | 同步数据库大小信息 |
| **custom** | 自定义任务 | 全部 | 用户定义 | 用户自定义Python代码 |

### 任务执行流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant W as Web界面
    participant T as 任务调度器
    participant E as 任务执行器
    participant D as 数据库
    participant I as 外部实例

    U->>W: 访问任务管理页面
    W->>U: 显示快速创建选项

    alt 快速创建任务
        U->>W: 点击快速创建按钮
        W->>T: 调用快速创建API
        T->>D: 创建任务记录
        T-->>W: 返回创建结果
        W-->>U: 显示创建成功
    end

    alt 批量操作
        U->>W: 选择多个任务
        U->>W: 点击批量操作按钮
        W->>T: 调用批量操作API
        T->>D: 批量更新任务状态
        T-->>W: 返回操作结果
        W-->>U: 显示操作成功
    end

    alt 任务执行
        U->>W: 触发任务执行
        W->>T: 调用任务执行API
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
        T-->>W: 更新任务状态
        W-->>U: 显示执行状态
    end
```

### 用户界面功能

#### 任务管理主页面
- **快速创建区域**: 提供4个快速创建卡片，支持一键创建常用任务类型
- **任务列表**: 显示所有任务的详细信息，包括状态、统计、最后运行时间等
- **批量操作**: 支持全选、批量启用/禁用、批量执行任务
- **筛选功能**: 按状态、数据库类型、任务类型筛选任务

#### 任务状态显示
- **启用/禁用状态**: 绿色表示启用，红色表示禁用
- **定时/手动状态**: 蓝色表示定时任务，灰色表示手动任务
- **执行结果**: 成功显示绿色，失败显示红色
- **运行统计**: 显示运行次数、成功次数、成功率

#### 快速创建功能
- **账户同步**: 为所有数据库类型创建账户同步任务
- **版本同步**: 为所有数据库类型创建版本同步任务
- **大小同步**: 为所有数据库类型创建大小同步任务
- **全部同步**: 一次性创建所有类型的同步任务

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

#### 数据库大小同步
```python
def sync_postgresql_size(instance, config):
    """同步PostgreSQL数据库大小信息"""
    # 查询数据库大小
    # 更新实例标签
    # 返回大小信息
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
- ✅ 任务调度系统
- ✅ 操作日志记录
- ✅ 实时监控仪表板
- ✅ RESTful API接口
- ✅ 安全防护机制
- ✅ 性能优化
- ✅ 完整的文档


---

**文档版本**: v1.0.0
**最后更新**: 2025-09-08
**维护者**: 泰摸鱼吧开发团队
