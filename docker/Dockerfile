# 泰摸鱼吧 - Flask应用Docker镜像 (最新稳定版)
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# 更新包列表并安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    wget \
    unzip \
    build-essential \
    pkg-config \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    freetds-bin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建用户数据目录
RUN mkdir -p /app/userdata/{backups,logs,exports,uploads} && \
    chmod -R 755 /app/userdata

# 创建非root用户
RUN groupadd -r taifish && useradd -r -g taifish taifish && \
    chown -R taifish:taifish /app

# 切换到非root用户
USER taifish

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV FLASK_APP=app
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--worker-class", "sync", "app:create_app()"]