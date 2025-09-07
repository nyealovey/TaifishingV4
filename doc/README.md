# 泰摸鱼吧 - 项目文档

## 文档导航

欢迎来到泰摸鱼吧项目文档中心！这里包含了项目的所有技术文档、开发指南和部署说明。

## 📚 文档结构

### 🚀 快速开始
- [项目主页](../README.md) - 项目概述和快速开始指南
- [环境设置指南](development/ENVIRONMENT_SETUP.md) - 详细的开发环境配置指南

### 🛠️ 开发文档

#### 环境配置
- [环境设置指南](development/ENVIRONMENT_SETUP.md) - 完整的开发环境搭建指南
- [故障排除指南](development/TROUBLESHOOTING.md) - 常见问题解决方案
- [数据库迁移指南](development/DATABASE_MIGRATION.md) - 数据库版本管理

#### 开发工具
- [开发工作流](../dev_workflow.sh) - 开发流程管理脚本
- [Redis管理工具](../redis_manager.sh) - Redis服务管理
- [数据库测试工具](../test_database.py) - 数据库连接测试

### 🏗️ 架构文档

#### 系统架构
- [技术规格文档](spec.md) - 详细的技术规格说明
- [项目结构说明](../README.md#项目结构) - 代码组织结构
- [API接口文档](api/) - RESTful API接口说明

#### 数据库设计
- [数据模型设计](spec.md#数据模型设计) - 数据库表结构设计
- [数据迁移策略](development/DATABASE_MIGRATION.md) - 数据库版本管理策略

### 🚀 部署文档

#### 环境部署
- [Docker部署指南](deployment/) - 容器化部署说明
- [生产环境配置](deployment/) - 生产环境优化配置
- [监控与维护](deployment/) - 系统监控和维护指南

### 📋 项目管理

#### 开发计划
- [任务清单](todolist.md) - 项目开发任务跟踪
- [开发报告](report.md) - 项目开发进度报告
- [架构决策记录](adr/) - 重要技术决策记录

## 🎯 快速导航

### 新开发者入门
1. 阅读 [项目主页](../README.md) 了解项目概况
2. 按照 [环境设置指南](development/ENVIRONMENT_SETUP.md) 配置开发环境
3. 运行 [一键安装脚本](../setup_dev_environment.sh) 快速启动
4. 查看 [故障排除指南](development/TROUBLESHOOTING.md) 解决常见问题

### 日常开发
1. 使用 [开发工作流](../dev_workflow.sh) 管理开发流程
2. 参考 [数据库迁移指南](development/DATABASE_MIGRATION.md) 处理数据库变更
3. 使用 [Redis管理工具](../redis_manager.sh) 管理缓存服务

### 部署上线
1. 查看 [Docker部署指南](deployment/) 了解容器化部署
2. 参考 [生产环境配置](deployment/) 优化生产环境
3. 使用 [监控与维护](deployment/) 指南进行系统维护

## 🔧 开发工具

### 脚本工具
- `setup_dev_environment.sh` - 一键安装开发环境
- `start_dev_with_redis.sh` - 启动开发环境
- `dev_workflow.sh` - 开发工作流管理
- `redis_manager.sh` - Redis服务管理
- `test_database.py` - 数据库连接测试

### 配置文件
- `requirements-local.txt` - 本地开发依赖
- `requirements.txt` - 生产环境依赖
- `.env` - 环境变量配置
- `docker-compose.yml` - Docker容器配置

## 📖 文档维护

### 更新原则
- 文档与代码同步更新
- 保持文档的准确性和时效性
- 定期检查和更新过时信息

### 贡献指南
- 发现文档问题请及时反馈
- 欢迎补充和完善文档内容
- 遵循统一的文档格式和风格

## 🆘 获取帮助

### 常见问题
- 查看 [故障排除指南](development/TROUBLESHOOTING.md)
- 搜索项目Issues页面
- 联系项目维护者

### 技术支持
- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目地址: [GitHub Repository URL]

---

**最后更新**: 2025年9月7日  
**文档版本**: v1.0.0  
**维护状态**: 活跃维护中