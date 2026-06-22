# ============================================================
# BI 工具箱 - Docker 镜像构建文件
# 基础镜像: Python 3.11-slim (兼容 Django 3.2.25)
# ============================================================

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r biuser && useradd -r -g biuser -d /app -s /sbin/nologin biuser

# 设置工作目录
WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt /app/requirements.txt

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt gunicorn==21.2.0

# 复制项目代码（排除 .env 等敏感文件，通过 .dockerignore 控制）
COPY . /app/

# 创建必要目录并设置权限
RUN mkdir -p /app/media/uploads /app/staticfiles /app/logs /app/data && \
    chmod +x /app/deploy/entrypoint.sh && \
    chown -R biuser:biuser /app

# 切换到非 root 用户
USER biuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/accounts/login/ || exit 1

# 启动入口
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
