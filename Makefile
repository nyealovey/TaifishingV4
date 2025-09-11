# 泰摸鱼吧 (TaifishV4) - UV Makefile
# 使用 make 命令简化常用操作

.PHONY: help install install-dev run dev test clean format lint type-check deps-add deps-remove deps-update

# 默认目标
help:
	@echo "泰摸鱼吧 (TaifishV4) - UV 管理命令"
	@echo "=================================="
	@echo ""
	@echo "环境管理:"
	@echo "  install     安装生产依赖"
	@echo "  install-dev 安装开发依赖"
	@echo "  clean       清理缓存和临时文件"
	@echo ""
	@echo "运行应用:"
	@echo "  run         启动应用"
	@echo "  dev         启动开发环境"
	@echo ""
	@echo "代码质量:"
	@echo "  format      格式化代码"
	@echo "  lint        代码检查"
	@echo "  type-check  类型检查"
	@echo "  test        运行测试"
	@echo ""
	@echo "依赖管理:"
	@echo "  deps-add    添加依赖 (用法: make deps-add PACKAGE=requests)"
	@echo "  deps-remove 移除依赖 (用法: make deps-remove PACKAGE=requests)"
	@echo "  deps-update 更新依赖"
	@echo ""
	@echo "示例:"
	@echo "  make install"
	@echo "  make run"
	@echo "  make deps-add PACKAGE=requests"

# 环境管理
install:
	@echo "📦 安装生产依赖..."
	uv sync

install-dev:
	@echo "📦 安装开发依赖..."
	uv sync --dev

clean:
	@echo "🧹 清理缓存和临时文件..."
	uv cache clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# 运行应用
run:
	@echo "🚀 启动应用..."
	uv run python app.py

dev:
	@echo "🛠️  启动开发环境..."
	./dev_uv.sh

# 代码质量
format:
	@echo "🎨 格式化代码..."
	uv run black app/ --line-length 88

lint:
	@echo "🔍 代码检查..."
	uv run flake8 app/ --max-line-length=88 --ignore=E203,W503

type-check:
	@echo "🔬 类型检查..."
	uv run mypy app/ --ignore-missing-imports

test:
	@echo "🧪 运行测试..."
	uv run pytest tests/ -v

# 依赖管理
deps-add:
	@if [ -z "$(PACKAGE)" ]; then \
		echo "❌ 错误: 请指定包名"; \
		echo "用法: make deps-add PACKAGE=requests"; \
		exit 1; \
	fi
	@echo "➕ 添加依赖: $(PACKAGE)"
	uv add $(PACKAGE)

deps-remove:
	@if [ -z "$(PACKAGE)" ]; then \
		echo "❌ 错误: 请指定包名"; \
		echo "用法: make deps-remove PACKAGE=requests"; \
		exit 1; \
	fi
	@echo "➖ 移除依赖: $(PACKAGE)"
	uv remove $(PACKAGE)

deps-update:
	@echo "🔄 更新依赖..."
	uv sync --upgrade

# 快速检查
check: format lint type-check test
	@echo "✅ 所有检查完成！"
