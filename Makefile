# AI投资分析师 Value-Seeker Makefile

.PHONY: help install install-dev setup test lint format clean run docker-build docker-run

# 默认目标
help:
	@echo "AI投资分析师 Value-Seeker 开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  setup          - 完整环境设置 (conda + poetry)"
	@echo "  install        - 安装生产依赖"
	@echo "  install-dev    - 安装开发依赖"
	@echo "  test           - 运行测试"
	@echo "  test-cov       - 运行测试并生成覆盖率报告"
	@echo "  lint           - 代码检查"
	@echo "  format         - 代码格式化"
	@echo "  clean          - 清理临时文件"
	@echo "  run            - 运行主程序"
	@echo "  docker-build   - 构建Docker镜像"
	@echo "  docker-run     - 运行Docker容器"

# 完整环境设置
setup:
	@echo "🚀 设置开发环境..."
	@if ! command -v conda >/dev/null 2>&1; then \
		echo "❌ 请先安装 Anaconda 或 Miniconda"; \
		exit 1; \
	fi
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "📦 安装 Poetry..."; \
		curl -sSL https://install.python-poetry.org | python3 -; \
	fi
	@echo "🐍 创建 conda 环境..."
	conda env create -f environment.yml --force
	@echo "📚 安装 Python 依赖..."
	conda run -n value-seeker poetry install
	@echo "📋 复制环境变量配置..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "✅ 环境设置完成!"
	@echo ""
	@echo "激活环境: conda activate value-seeker"

# 安装生产依赖
install:
	poetry install --only=main

# 安装开发依赖
install-dev:
	poetry install

# 运行测试
test:
	poetry run pytest

# 运行测试并生成覆盖率报告
test-cov:
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

# 代码检查
lint:
	poetry run flake8 src tests
	poetry run mypy src
	poetry run black --check src tests
	poetry run isort --check-only src tests

# 代码格式化
format:
	poetry run black src tests
	poetry run isort src tests

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# 运行主程序
run:
	poetry run python main.py

# 构建Docker镜像
docker-build:
	docker build -t value-seeker:latest .

# 运行Docker容器
docker-run:
	docker run -it --rm \
		--gpus all \
		-p 7860:7860 \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/deploy:/app/deploy \
		-v $(PWD)/logs:/app/logs \
		value-seeker:latest

# 开发模式运行 (带热重载)
dev:
	poetry run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 安装pre-commit钩子
install-hooks:
	poetry run pre-commit install

# 运行pre-commit检查
pre-commit:
	poetry run pre-commit run --all-files