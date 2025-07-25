# AI投资分析师 Value-Seeker Makefile

.PHONY: help install install-dev setup test lint format clean run docker-build docker-run

# 默认目标
help:
	@echo "AI投资分析师 Value-Seeker 开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  setup          - 完整环境设置 (conda + pip)"
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
	@echo "🐍 创建 conda 环境..."
	conda env create -f environment.yml --force
	@echo "📚 Python 依赖通过 conda 自动安装"
	@echo "📋 复制环境变量配置..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "✅ 环境设置完成!"
	@echo ""
	@echo "激活环境: conda activate value-seeker"

# 安装生产依赖
install:
	pip install -r requirements.txt

# 安装开发依赖
install-dev:
	pip install -r requirements.txt

# 运行测试
test:
	pytest

# 运行测试并生成覆盖率报告
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# 代码检查
lint:
	flake8 src tests
	mypy src
	black --check src tests
	isort --check-only src tests

# 代码格式化
format:
	black src tests
	isort src tests

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
	python main.py

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
	python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 安装pre-commit钩子
install-hooks:
	pre-commit install

# 运行pre-commit检查
pre-commit:
	pre-commit run --all-files