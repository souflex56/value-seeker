# AI投资分析师 Value-Seeker Dockerfile

FROM nvidia/cuda:11.8-devel-ubuntu20.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3-pip \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建符号链接
RUN ln -s /usr/bin/python3.9 /usr/bin/python

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt ./
COPY src/ ./src/
COPY config/ ./config/
COPY prompts/ ./prompts/
COPY main.py ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p data/reports data/dyp_corpus deploy/vector_store logs

# 设置权限
RUN chmod +x main.py

# 暴露端口
EXPOSE 7860

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# 启动命令
CMD ["python", "main.py"]