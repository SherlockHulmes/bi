# BI 工具箱 - Docker 部署指南

## 目录结构

```
deploy/
├── Dockerfile           # 镜像构建文件
├── docker-compose.yml   # 服务编排（Web + Celery + Redis + Nginx）
├── .env.example         # 环境变量模板
├── nginx.conf           # Nginx 反向代理配置
├── entrypoint.sh        # 容器启动脚本
└── README.md            # 本文档
```

## 快速部署（3 步）

### 第 1 步：配置环境变量

```bash
cd deploy
cp .env.example .env
```

编辑 `.env`，填写以下必填项：

| 变量 | 说明 | 示例 |
|------|------|------|
| `SECRET_KEY` | Django 密钥 | 用 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` 生成 |
| `DB_HOST` | MySQL/RDS 地址 | `your-rds-host` |
| `DB_USER` | 数据库用户 | `your-user` |
| `DB_PASSWORD` | 数据库密码 | `your-password` |
| `DB_NAME` | 数据库名 | `your-db` |
| `ALLOWED_HOSTS` | 允许访问的 IP | `192.168.1.100` |

### 第 2 步：构建并启动

```bash
cd ..
docker compose -f deploy/docker-compose.yml up -d --build
```

### 第 3 步：访问

- 应用地址：`http://你的服务器IP:8000`（直连）或 `http://你的服务器IP`（Nginx）
- 默认管理员：`admin` / `admin123456`

## 服务说明

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| web | bi-web | 8000 | Django 应用（Gunicorn） |
| celery-worker | bi-celery-worker | - | 异步任务处理 |
| celery-beat | bi-celery-beat | - | 定时任务调度 |
| redis | bi-redis | 6379 | 消息队列 |
| nginx | bi-nginx | 80 | 反向代理（可选） |

## 常用命令

```bash
# 查看状态
docker compose -f deploy/docker-compose.yml ps

# 查看日志
docker compose -f deploy/docker-compose.yml logs -f web
docker compose -f deploy/docker-compose.yml logs -f celery-worker
docker compose -f deploy/docker-compose.yml logs -f celery-beat

# 重启服务
docker compose -f deploy/docker-compose.yml restart web

# 停止所有服务
docker compose -f deploy/docker-compose.yml down

# 重新构建
docker compose -f deploy/docker-compose.yml build --no-cache
docker compose -f deploy/docker-compose.yml up -d

# 进入容器
docker compose -f deploy/docker-compose.yml exec web bash

# 执行 Django 命令
docker compose -f deploy/docker-compose.yml exec web python manage.py createsuperuser
docker compose -f deploy/docker-compose.yml exec web python manage.py migrate
```

## 数据持久化

| Volume | 说明 |
|--------|------|
| `sqlite_data` | SQLite 数据库（Django 元数据）+ Celery Beat 调度文件 |
| `redis_data` | Redis 数据 |
| `static_volume` | Django 静态文件 |
| `media_volume` | 用户上传文件 |
| `logs_volume` | 应用日志 |

## 不使用 Nginx

如果不需要 Nginx（如使用云服务商负载均衡），只启动核心服务：

```bash
docker compose -f deploy/docker-compose.yml up -d redis web celery-worker celery-beat
```

## 分享项目

### 方式一：Git 仓库（推荐）

```bash
git init
git add .
git commit -m "init: BI 工具箱"
git remote add origin https://your-git/repo.git
git push -u origin main
```

对方：
```bash
git clone https://your-git/repo.git
cd repo
cp deploy/.env.example deploy/.env
# 编辑 deploy/.env
docker compose -f deploy/docker-compose.yml up -d --build
```

### 方式二：Docker 镜像导出

```bash
# 在你的机器上导出
docker save deploy-web deploy-celery-worker deploy-celery-beat -o bi-toolkit-images.tar

# 在对方机器上导入
docker load -i bi-toolkit-images.tar
# 然后创建容器（需要 docker-compose.yml 和 .env）
docker compose -f deploy/docker-compose.yml up -d
```

## 安全注意事项

1. `.env` 文件包含敏感信息，绝不能提交到 Git
2. 生产环境 `DEBUG` 设为 `False`
3. `SECRET_KEY` 必须随机生成
4. `ALLOWED_HOSTS` 只配置实际使用的 IP/域名