import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ⚠️ 安全提示：
# - 生产环境必须设置 SECRET_KEY 环境变量！
# - 生产环境必须设置 DEBUG=False
# - 详见 .env.example 和 SECURITY.md
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

if DEBUG and SECRET_KEY == 'django-insecure-change-me-in-production':
    import warnings
    warnings.warn("⚠️ 正在使用默认 SECRET_KEY 和 DEBUG=True，请勿在生产环境中使用！")

# 安全配置：ALLOWED_HOSTS 必须配置具体域名
_hosts = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [h.strip() for h in _hosts.split(',') if h.strip()]

# Session 安全
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# 安全 Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# ==================== 应用注册 ====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 项目应用
    'core',
    'reports',
    'sql_scripts',
    'scheduler',
    'notifications',
    'data_quality',
    'data_lineage',
    'data_extract',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bi_toolkit.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bi_toolkit.wsgi.application'

# ==================== 数据库配置 ====================
# Django 元数据使用 SQLite（用户、定时任务、脚本配置等）
# 数据查询使用阿里云 RDS（通过 DbConnection 模型配置）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.getenv('DB_PATH', str(BASE_DIR / 'db.sqlite3')),
    }
}

RDS_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', ''),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', ''),
    'charset': 'utf8mb4',
}

# ==================== 密码验证 ====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================== 国际化 ====================
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# ==================== 静态文件 ====================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ==================== 媒体文件 ====================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==================== 文件上传配置 ====================
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024

ALLOWED_UPLOAD_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# ==================== 登录配置 ====================
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ==================== Celery 配置 ====================
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = False  # 使用本地时区（Asia/Shanghai），不用 UTC
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')  # 用 Redis 存储结果（支持 inspect 命令）
CELERY_RESULT_EXPIRES = 3600  # 结果保留1小时
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ==================== 通知配置 ====================
NOTIFY_CHANNEL = os.getenv('NOTIFY_CHANNEL', 'dingtalk')
DINGTALK_WEBHOOK = os.getenv('DINGTALK_WEBHOOK', '')
DINGTALK_SECRET = os.getenv('DINGTALK_SECRET', '')
WECOM_WEBHOOK = os.getenv('WECOM_WEBHOOK', '')

# ==================== 日志配置 ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'app.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'core': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sql_scripts': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'scheduler': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'notifications': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'data_quality': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'data_lineage': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'data_extract': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== Django Admin 配置 ====================
ADMIN_SITE_HEADER = 'BI 工具箱 · 管理后台'
ADMIN_SITE_TITLE = 'BI 工具箱管理'
ADMIN_INDEX_TITLE = '系统管理'
