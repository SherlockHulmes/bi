# BI 工具箱

SQL 脚本管理、定时执行、数据质量监控与数据血缘分析平台。

## 功能列表

- **SQL 脚本管理**：在线编辑、执行 SQL，支持多数据库连接
- **自助取数**：拖拽式可视化查询构建器，无需写 SQL
- **定时任务**：支持每日/每周/每月/自定义 Cron 调度
- **数据质量**：配置质量规则，自动检测数据问题
- **数据血缘**：解析 MySQL EVENT，自动生成数据血缘图
- **通知推送**：支持钉钉、企业微信、邮件通知
- **查询模板**：保存常用查询，一键复用
- **数据导出**：查询结果导出 Excel/CSV

## 快速开始

### 方式一：本地开发（Windows，推荐日常开发）

**前置要求**：
- Python 3.8+（Anaconda）
- Redis（本地安装或使用远程）

```bash
# 安装依赖
pip install -r requirements.txt

# 复制并编辑环境变量
copy .env.example .env
# 编辑 .env，填写数据库连接信息

# 一键启动（Django + Celery Worker + Celery Beat）
run.bat
```

访问 http://127.0.0.1:8000

停止服务：双击 `stop.bat` 或在终端按 `Ctrl+C`

### 方式二：Docker 部署（推荐服务器部署）

**前置要求**：
- Docker Engine 20.10+
- Docker Compose v2.0+

```bash
# 1. 配置环境变量
cd deploy
cp .env.example .env
# 编辑 .env 填写配置（见下方说明）

# 2. 构建并启动
cd ..
docker compose -f deploy/docker-compose.yml up -d --build

# 3. 查看日志
docker compose -f deploy/docker-compose.yml logs -f web
```

访问 http://你的服务器IP:8000

默认管理员：`admin` / `admin123456`（首次部署自动创建）

## 配置说明

在项目根目录创建 `.env` 文件（本地开发）或 `deploy/.env`（Docker 部署）：

```env
# Django 密钥（必填，用此命令生成）
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=your-secret-key

# 允许访问的 IP/域名（逗号分隔）
ALLOWED_HOSTS=127.0.0.1,localhost

# 数据库连接（用于 SQL 脚本查询，非 Django 元数据）
DB_HOST=your-mysql-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-database
```

> **说明**：Django 元数据（用户、任务配置等）存储在 SQLite (`db.sqlite3`)，`DB_*` 配置用于数据查询的 MySQL/RDS 连接。

## 项目结构

```
├── bi_toolkit/          # Django 项目配置
├── core/                # 首页、数据库连接管理
├── sql_scripts/         # SQL 脚本管理与执行
├── scheduler/           # 定时任务调度
├── data_quality/        # 数据质量监控
├── data_lineage/        # 数据血缘分析
├── data_extract/        # 自助取数
├── reports/             # 报表管理
├── notifications/       # 通知推送（钉钉/企微/邮件）
├── templates/           # HTML 模板
├── static/              # 静态资源
├── deploy/              # Docker 部署配置
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── nginx.conf
│   ├── entrypoint.sh
│   └── README.md
├── run.bat              # Windows 一键启动（本地开发）
├── stop.bat             # Windows 一键停止
├── manage.py            # Django 管理命令
├── requirements.txt     # Python 依赖
└── .env                 # 环境变量（不提交 Git）
```

## 常用命令

```bash
# 本地开发
python manage.py createsuperuser        # 创建管理员
python manage.py makemigrations         # 生成迁移
python manage.py migrate                # 执行迁移

# Docker
docker compose -f deploy/docker-compose.yml up -d          # 启动
docker compose -f deploy/docker-compose.yml down            # 停止
docker compose -f deploy/docker-compose.yml logs -f web     # 查看日志
docker compose -f deploy/docker-compose.yml exec web python manage.py createsuperuser  # 创建管理员
```

## 分享项目

| 方式 | 适用场景 | 操作 |
|------|---------|------|
| **Git 仓库** | 给开发者 | `git push` 到 GitHub/GitLab，对方 `git clone` |
| **Docker 镜像** | 给无源码的人 | `docker save` 导出镜像，对方 `docker load` 导入 |
| **源码打包** | 通用 | 压缩项目（不含 `.env`、`__pycache__`、`db.sqlite3`） |

### Docker 镜像导出/导入
```bash
# 导出（在你的机器上）
docker save deploy-web deploy-celery-worker deploy-celery-beat -o bi-toolkit-images.tar

# 导入（在对方机器上）
docker load -i bi-toolkit-images.tar
```

## 技术栈

- **后端**：Django 3.2 + Celery 5.2 + SQLAlchemy
- **前端**：Bootstrap 5 + Bootstrap Icons
- **数据库**：SQLite（元数据）+ MySQL/RDS（数据查询）
- **消息队列**：Redis
- **部署**：Docker + Gunicorn + Nginx