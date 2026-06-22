import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bi_toolkit.settings')

app = Celery('bi_toolkit')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 每分钟检查一次是否有到期的定时任务和质量规则需要执行
app.conf.beat_schedule = {
    'check-scheduled-tasks-every-minute': {
        'task': 'scheduler.tasks.check_scheduled_tasks',
        'schedule': crontab(minute='*/1'),
    },
    'check-quality-rules-every-minute': {
        'task': 'data_quality.tasks.check_quality_rules',
        'schedule': crontab(minute='*/1'),
    },
}
