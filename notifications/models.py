from django.db import models


class NotificationConfig(models.Model):
    """通知渠道配置"""
    CHANNEL_CHOICES = [
        ('dingtalk', '钉钉'),
        ('wecom', '企业微信'),
        ('email', '邮件'),
    ]

    channel = models.CharField('通知渠道', max_length=20, choices=CHANNEL_CHOICES, unique=True)
    webhook_url = models.URLField('Webhook URL', max_length=500, blank=True)
    secret = models.CharField('加签密钥', max_length=200, blank=True, help_text='钉钉加签密钥（可选）')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    email_host = models.CharField('SMTP 服务器', max_length=200, blank=True, default='smtp.qq.com')
    email_port = models.IntegerField('SMTP 端口', default=465)
    email_use_ssl = models.BooleanField('使用 SSL', default=True)
    email_host_user = models.CharField('发件人邮箱', max_length=200, blank=True)
    email_host_password = models.CharField('邮箱密码/授权码', max_length=200, blank=True)
    email_recipients = models.TextField('收件人邮箱', blank=True, help_text='多个邮箱用逗号分隔')

    class Meta:
        db_table = 'notifications_config'
        verbose_name = '通知配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.get_channel_display()} ({'启用' if self.is_active else '停用'})"