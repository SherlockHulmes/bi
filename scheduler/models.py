from django.db import models
from django.conf import settings
from sql_scripts.models import SqlScript


class ScheduledTask(models.Model):
    """定时任务配置"""
    NOTIFY_CHOICES = [
        ('none', '不通知'),
        ('dingtalk', '钉钉'),
        ('wecom', '企业微信'),
        ('email', '邮件'),
    ]
    SCHEDULE_TYPE_CHOICES = [
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('custom', '自定义'),
    ]
    WEEKDAY_CHOICES = [
        (0, '周一'), (1, '周二'), (2, '周三'), (3, '周四'),
        (4, '周五'), (5, '周六'), (6, '周日'),
    ]

    script = models.ForeignKey(SqlScript, on_delete=models.CASCADE, related_name='scheduled_tasks', verbose_name='脚本')
    name = models.CharField('任务名称', max_length=200)
    schedule_type = models.CharField('调度类型', max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='daily')
    schedule_hour = models.IntegerField('执行小时', default=8)
    schedule_minute = models.IntegerField('执行分钟', default=0)
    schedule_days = models.CharField('周几执行', max_length=50, blank=True, help_text='逗号分隔的数字，0=周一 6=周日')
    schedule_day_of_month = models.IntegerField('每月几号', default=1)
    cron_expr = models.CharField('Cron 表达式（自动生成）', max_length=100, blank=True)
    is_enabled = models.BooleanField('是否启用', default=True)
    notify_channel = models.CharField('通知渠道', max_length=20, choices=NOTIFY_CHOICES, default='none')
    email_recipients = models.TextField('收件人邮箱', blank=True, help_text='多个邮箱用逗号分隔，用于发送执行结果文件')
    last_run_at = models.DateTimeField('上次执行时间', null=True, blank=True)
    last_status = models.CharField('上次状态', max_length=20, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'scheduler_task'
        verbose_name = '定时任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_schedule_display()})"

    def get_schedule_display(self):
        """获取人类可读的调度描述"""
        hour = f"{self.schedule_hour:02d}:{self.schedule_minute:02d}"
        if self.schedule_type == 'daily':
            return f"每天 {hour}"
        elif self.schedule_type == 'weekly':
            day_names = dict(self.WEEKDAY_CHOICES)
            days = [day_names.get(int(d), '?') for d in self.schedule_days.split(',') if d.strip()]
            return f"每周 {', '.join(days)} {hour}"
        elif self.schedule_type == 'monthly':
            return f"每月 {self.schedule_day_of_month} 号 {hour}"
        else:
            return self.cron_expr or '未配置'

    def save(self, *args, **kwargs):
        """自动根据可视化配置生成 cron 表达式"""
        self._generate_cron()
        super().save(*args, **kwargs)

    def _generate_cron(self):
        """根据 schedule_type 等字段生成 cron 表达式"""
        h = str(self.schedule_hour)
        m = str(self.schedule_minute)
        if self.schedule_type == 'daily':
            self.cron_expr = f"{m} {h} * * *"
        elif self.schedule_type == 'weekly':
            days = ','.join(d.strip() for d in self.schedule_days.split(',') if d.strip())
            # cron 中 0=周日，需要转换：Python 0=周一 → cron 1=周一
            day_map = {'0': '1', '1': '2', '2': '3', '3': '4', '4': '5', '5': '6', '6': '0'}
            cron_days = ','.join(day_map.get(d, d) for d in self.schedule_days.split(',') if d.strip())
            self.cron_expr = f"{m} {h} * * {cron_days}"
        elif self.schedule_type == 'monthly':
            self.cron_expr = f"{m} {h} {self.schedule_day_of_month} * *"
        # custom 模式直接使用用户输入的 cron_expr


class ScheduledTaskLog(models.Model):
    """定时任务执行日志"""
    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
    ]
    TRIGGER_CHOICES = [
        ('manual', '手动执行'),
        ('scheduled', '定时执行'),
        ('send_file', '发送文件'),
        ('data_query', '数据查询'),
        ('quality_check', '质量检查'),
    ]

    task = models.ForeignKey(ScheduledTask, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs', verbose_name='关联任务')
    task_name = models.CharField('任务名称快照', max_length=200)
    script_name = models.CharField('脚本名称快照', max_length=200, blank=True)
    sql_executed = models.TextField('执行的SQL', blank=True)
    trigger_type = models.CharField('触发方式', max_length=20, choices=TRIGGER_CHOICES, default='manual')
    status = models.CharField('执行状态', max_length=20, choices=STATUS_CHOICES, default='success')
    row_count = models.IntegerField('影响行数', null=True, blank=True)
    duration = models.FloatField('执行耗时(秒)', null=True, blank=True)
    error_message = models.TextField('错误信息', blank=True)
    notify_channel = models.CharField('通知渠道', max_length=20, blank=True)
    notify_target = models.TextField('通知对象', blank=True, help_text='邮箱地址等')
    notify_status = models.BooleanField('通知是否成功', null=True, blank=True)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='执行人'
    )
    executed_at = models.DateTimeField('执行时间', auto_now_add=True)

    class Meta:
        db_table = 'scheduler_task_log'
        verbose_name = '任务执行日志'
        verbose_name_plural = verbose_name
        ordering = ['-executed_at']

    def __str__(self):
        return f"{self.task_name} - {self.get_status_display()} ({self.executed_at})"
