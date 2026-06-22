#!/bin/bash
# ============================================================
# BI 工具箱 - Docker 容器启动脚本
# ============================================================

set -e

echo "=========================================="
echo "  BI 工具箱 - 启动中..."
echo "=========================================="

# 确保数据目录存在
mkdir -p /app/data
mkdir -p /app/logs

# 等待 Redis 可用
echo "[1/5] 等待 Redis 连接..."
while ! python -c "import redis; r = redis.from_url('${REDIS_URL:-redis://redis:6379/0}'); r.ping()" 2>/dev/null; do
    echo "  Redis 未就绪，等待 2 秒..."
    sleep 2
done
echo "  Redis 已连接 ✓"

# 数据库迁移
echo "[2/5] 执行数据库迁移..."
python manage.py migrate --noinput

# 收集静态文件
echo "[3/5] 收集静态文件..."
python manage.py collectstatic --noinput --clear

# 创建超级用户（如果环境变量存在）
echo "[4/5] 检查管理员账户..."
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '', '$DJANGO_SUPERUSER_PASSWORD')
    print('  管理员账户已创建')
else:
    print('  管理员账户已存在')
" 2>/dev/null || echo "  跳过管理员创建"
else
    echo "  未配置管理员环境变量，跳过"
fi

# 启动应用
if [ $# -gt 0 ]; then
    # docker-compose 中指定了 command，直接执行
    echo "[5/5] 启动服务: $@"
    echo "=========================================="
    exec "$@"
else
    # 默认启动 Gunicorn（web 服务）
    echo "[5/5] 启动 Gunicorn..."
    echo "=========================================="
    echo "  BI 工具箱已启动!"
    echo "  访问地址: http://localhost:${WEB_PORT:-8000}"
    echo "=========================================="
    exec gunicorn bi_toolkit.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers ${GUNICORN_WORKERS:-3} \
        --threads ${GUNICORN_THREADS:-2} \
        --timeout 300 \
        --access-logfile - \
        --error-logfile - \
        --log-level info
fi
