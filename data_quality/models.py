from django.db import models
from django.conf import settings
from sql_scripts.models import DbConnection


class QualityRule(models.Model):
    """数据质量规则"""

    CONDITION_CHOICES = [
        ('rows_gt_0', '查询返回行数 > 0（存在异常时告警）'),
        ('rows_eq_0', '查询返回行数 = 0（数据缺失时告警）'),
        ('value_gt', '某列值 > 阈值'),
        ('value_lt', '某列值 < 阈值'),
        ('value_eq', '某列值 = 阈值'),
    ]

    SCHEDULE_CHOICES = [
        ('manual', '仅手动执行'),
        ('every_minutes', '每N分钟'),
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
    ]

    NOTIFY_CHOICES = [
        ('none', '不通知'),
        ('dingtalk', '钉钉'),
        ('wecom', '企业微信'),
        ('email', '邮件'),
    ]

    name = models.CharField('规则名称', max_length=200)
    description = models.TextField('规则描述', blank=True)
    target_db = models.ForeignKey(
        DbConnection, on_delete=models.CASCADE,
        verbose_name='目标数据库',
        related_name='quality_rules'
    )
    sql_query = models.TextField('SQL 查询', help_text='输入要执行的 SQL 查询')
    condition_type = models.CharField('条件类型', max_length=20, choices=CONDITION_CHOICES, default='rows_gt_0')
    check_column = models.CharField('检查列名', max_length=100, blank=True, help_text='条件为列值比较时必填')
    threshold = models.FloatField('阈值', default=0, blank=True)

    schedule_type = models.CharField('调度类型', max_length=20, choices=SCHEDULE_CHOICES, default='daily')
    interval_minutes = models.IntegerField('执行间隔(分钟)', default=5, help_text='每N分钟执行一次，范围1-1440')
    schedule_hour = models.IntegerField('执行小时', default=8)
    schedule_minute = models.IntegerField('执行分钟', default=0)
    schedule_days = models.CharField('周几执行', max_length=50, blank=True, help_text='逗号分隔的数字，0=周一 6=周日')
    schedule_day_of_month = models.IntegerField('每月几号', default=1)

    notify_channel = models.CharField('通知渠道', max_length=20, choices=NOTIFY_CHOICES, default='none')
    email_recipients = models.TextField('收件人邮箱', blank=True, help_text='多个邮箱用逗号分隔')
    is_enabled = models.BooleanField('是否启用', default=True)

    last_check_at = models.DateTimeField('上次检查时间', null=True, blank=True)
    last_check_status = models.CharField('上次状态', max_length=20, blank=True, default='pending',
                                         choices=[('normal', '正常'), ('alert', '告警'), ('error', '错误'), ('pending', '未执行')])

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'data_quality_rule'
        verbose_name = '质量规则'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_condition_type_display()})"

    def get_schedule_display_text(self):
        """获取人类可读的调度描述"""
        hour = f"{self.schedule_hour:02d}:{self.schedule_minute:02d}"
        if self.schedule_type == 'manual':
            return '仅手动执行'
        elif self.schedule_type == 'every_minutes':
            return f"每 {self.interval_minutes} 分钟"
        elif self.schedule_type == 'daily':
            return f"每天 {hour}"
        elif self.schedule_type == 'weekly':
            from scheduler.models import ScheduledTask
            day_names = dict(ScheduledTask.WEEKDAY_CHOICES)
            days = [day_names.get(int(d), '?') for d in self.schedule_days.split(',') if d.strip()]
            return f"每周 {', '.join(days)} {hour}"
        elif self.schedule_type == 'monthly':
            return f"每月 {self.schedule_day_of_month} 号 {hour}"
        return '未知'


class QualityCheckLog(models.Model):
    """质量检查日志"""

    STATUS_CHOICES = [
        ('normal', '正常'),
        ('alert', '告警'),
        ('error', '错误'),
    ]

    rule = models.ForeignKey(QualityRule, on_delete=models.CASCADE, related_name='logs', verbose_name='规则')
    status = models.CharField('结果状态', max_length=20, choices=STATUS_CHOICES)
    result_value = models.TextField('查询结果摘要', blank=True)
    alert_message = models.TextField('告警消息', blank=True)
    error_message = models.TextField('错误信息', blank=True)
    duration = models.FloatField('执行耗时(秒)', default=0)
    executed_at = models.DateTimeField('执行时间', auto_now_add=True)
    triggered_by = models.CharField('触发方式', max_length=20, default='manual',
                                     choices=[('manual', '手动'), ('scheduled', '定时')])

    class Meta:
        db_table = 'data_quality_check_log'
        verbose_name = '检查日志'
        verbose_name_plural = verbose_name
        ordering = ['-executed_at']

    def __str__(self):
        return f"{self.rule.name} - {self.get_status_display()} ({self.executed_at})"