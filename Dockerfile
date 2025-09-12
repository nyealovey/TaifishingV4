# 使用Ubuntu 22.04作为基础镜像
FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libpq-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -s /bin/bash taifish && \
    chown -R taifish:taifish /app

# 切换到非root用户
USER taifish

# 创建虚拟环境
RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# 复制requirements文件
COPY --chown=taifish:taifish requirements.txt /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=taifish:taifish . /app/

# 创建必要的目录
RUN mkdir -p /app/userdata/logs /app/userdata/exports /app/userdata/backups /app/userdata/uploads

# 设置权限
RUN chmod -R 755 /app/userdata

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["python", "app.py"]
