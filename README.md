# BI 工具箱

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

### 方式一：一键启动（Windows，推荐）

**前置要求**：Python 3.7+

```bash
# 双击 run.bat 即可（首次运行自动安装依赖、创建数据库、创建管理员）
run.bat
```

启动后自动打开浏览器访问 http://127.0.0.1:8000

默认管理员：`admin` / `admin123`（**首次部署后请立即修改密码！**）

停止服务：双击 `stop.bat`

### 方式二：手动启动（开发）

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填写数据库连接信息等

# 初始化数据库
python manage.py migrate

# 创建管理员
python manage.py createsuperuser

# 启动
python manage.py runserver
```

### 方式三：Docker 部署（推荐服务器部署）

**前置要求**：Docker Engine 20.10+、Docker Compose v2.0+

```bash
# 1. 配置环境变量
cd deploy
cp .env.example .env
# 编辑 .env 填写配置

# 2. 构建并启动
cd ..
docker compose -f deploy/docker-compose.yml up -d --build

# 3. 查看日志
docker compose -f deploy/docker-compose.yml logs -f web
```

访问 http://你的服务器IP:8000

## 配置说明

项目根目录的 `.env` 文件（本地开发）或 `deploy/.env`（Docker 部署）：

```env
# Django 密钥（必填，用此命令生成）
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=your-secret-key

# 调试模式（生产环境务必设为 False）
DEBUG=False

# 允许访问的 IP/域名（逗号分隔）
ALLOWED_HOSTS=127.0.0.1,localhost
```

> 完整配置请参考 `.env.example` 和 `deploy/.env.example`

## ⚠️ 安全注意事项

- **生产环境必须**：修改 SECRET_KEY、关闭 DEBUG、配置 ALLOWED_HOSTS
- **首次部署后**：立即修改默认管理员密码
- **敏感信息**：`.env` 文件已被 `.gitignore` 排除，**切勿提交到 Git**
- 详见 [SECURITY.md](SECURITY.md)

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
├── run.bat              # Windows 一键启动
├── stop.bat             # Windows 一键停止
├── manage.py            # Django 管理命令
├── requirements.txt     # Python 依赖
└── .env                 # 环境变量（不提交 Git）
```

## 技术栈

- **后端**：Django 3.2 + Celery 5.2 + SQLAlchemy
- **前端**：Bootstrap 5 + Bootstrap Icons
- **数据库**：SQLite（元数据）+ MySQL/RDS（数据查询）
- **消息队列**：Redis
- **部署**：Docker + Gunicorn + Nginx

## 贡献

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 许可证

本项目使用 [MIT 许可证](LICENSE)。