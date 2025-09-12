# 泰摸鱼吧生产环境Makefile
# 提供便捷的Docker操作命令

.PHONY: help build up down restart logs shell backup restore clean

# 默认目标
help:
	@echo "🐟 泰摸鱼吧生产环境管理命令"
	@echo "=========================================="
	@echo "📦 构建和部署:"
	@echo "  make build     - 构建Docker镜像"
	@echo "  make up        - 启动所有服务"
	@echo "  make down      - 停止所有服务"
	@echo "  make restart   - 重启所有服务"
	@echo ""
	@echo "🔍 监控和调试:"
	@echo "  make logs      - 查看所有服务日志"
	@echo "  make logs-app  - 查看应用日志"
	@echo "  make logs-db   - 查看数据库日志"
	@echo "  make shell     - 进入应用容器"
	@echo "  make shell-db  - 进入数据库容器"
	@echo ""
	@echo "💾 数据管理:"
	@echo "  make backup    - 备份数据库"
	@echo "  make restore   - 恢复数据库"
	@echo "  make init-db   - 初始化数据库"
	@echo ""
	@echo "🧹 清理:"
	@echo "  make clean     - 清理所有容器和镜像"
	@echo "  make clean-volumes - 清理数据卷"
	@echo "=========================================="

# 构建镜像
build:
	@echo "🔨 构建Docker镜像..."
	docker compose build --no-cache

# 启动服务
up:
	@echo "🚀 启动所有服务..."
	docker compose up -d
	@echo "✅ 服务启动完成"

# 停止服务
down:
	@echo "🛑 停止所有服务..."
	docker compose down
	@echo "✅ 服务停止完成"

# 重启服务
restart: down up
	@echo "🔄 服务重启完成"

# 查看日志
logs:
	@echo "📋 查看所有服务日志..."
	docker compose logs -f

# 查看应用日志
logs-app:
	@echo "📋 查看应用日志..."
	docker compose logs -f app

# 查看数据库日志
logs-db:
	@echo "📋 查看数据库日志..."
	docker compose logs -f postgres

# 进入应用容器
shell:
	@echo "🐚 进入应用容器..."
	docker compose exec app /bin/bash

# 进入数据库容器
shell-db:
	@echo "🐚 进入数据库容器..."
	docker compose exec postgres psql -U taifish_user -d taifish_prod

# 备份数据库
backup:
	@echo "💾 备份数据库..."
	@mkdir -p backups
	docker compose exec postgres pg_dump -U taifish_user taifish_prod > backups/taifish_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ 数据库备份完成"

# 恢复数据库
restore:
	@echo "📥 恢复数据库..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ 请指定备份文件: make restore FILE=backups/taifish_backup_20240101_120000.sql"; \
		exit 1; \
	fi
	docker compose exec -T postgres psql -U taifish_user -d taifish_prod < $(FILE)
	@echo "✅ 数据库恢复完成"

# 初始化数据库
init-db:
	@echo "🗄️ 初始化数据库..."
	docker compose exec app python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('数据库表创建完成')"
	docker compose exec app python scripts/init_permission_config.py
	docker compose exec app python scripts/init_default_classification_rules.py
	docker compose exec app python scripts/create_admin_user.py
	@echo "✅ 数据库初始化完成"

# 清理容器和镜像
clean:
	@echo "🧹 清理容器和镜像..."
	docker compose down --rmi all --volumes --remove-orphans
	docker system prune -f
	@echo "✅ 清理完成"

# 清理数据卷
clean-volumes:
	@echo "🧹 清理数据卷..."
	docker compose down -v
	docker volume prune -f
	@echo "✅ 数据卷清理完成"

# 查看服务状态
status:
	@echo "📊 服务状态:"
	docker compose ps

# 查看资源使用情况
stats:
	@echo "📊 资源使用情况:"
	docker stats --no-stream

# 更新服务
update:
	@echo "🔄 更新服务..."
	git pull
	docker compose build --no-cache
	docker compose up -d
	@echo "✅ 服务更新完成"

# 健康检查
health:
	@echo "🏥 健康检查..."
	@curl -f http://localhost/health || echo "❌ 健康检查失败"
	@docker compose exec postgres pg_isready -U taifish_user -d taifish_prod || echo "❌ 数据库连接失败"
	@docker compose exec redis redis-cli ping || echo "❌ Redis连接失败"
	@echo "✅ 健康检查完成"

# 生产环境部署
deploy-prod:
	@echo "🚀 生产环境部署..."
	@if [ ! -f .env.production ]; then \
		echo "❌ 请先创建 .env.production 文件"; \
		exit 1; \
	fi
	cp .env.production .env
	make build
	make up
	sleep 30
	make init-db
	@echo "✅ 生产环境部署完成"

# 开发环境部署
deploy-dev:
	@echo "🛠️ 开发环境部署..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "📝 已创建 .env 文件，请根据需要修改"; \
	fi
	make build
	make up
	sleep 30
	make init-db
	@echo "✅ 开发环境部署完成"