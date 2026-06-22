from django.db import models
from django.conf import settings


class ReportRequest(models.Model):
    """报表需求登记"""
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('closed', '已关闭'),
    ]

    title = models.CharField('需求标题', max_length=200)
    description = models.TextField('需求描述', blank=True)
    priority = models.CharField('优先级', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    requester = models.CharField('提出人', max_length=100, blank=True, default='', help_text='需求提出人姓名')
    developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_reports',
        verbose_name='开发人员'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_reports',
        verbose_name='创建人',
        editable=False
    )
    expected_date = models.DateField('期望完成日期', null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'reports_request'
        verbose_name = '报表需求'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"


class ReportComment(models.Model):
    """需求评论/跟进记录"""
    report = models.ForeignKey(ReportRequest, on_delete=models.CASCADE, related_name='comments', verbose_name='需求')
    content = models.TextField('评论内容')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, verbose_name='评论人'
    )
    created_at = models.DateTimeField('评论时间', auto_now_add=True)

    class Meta:
        db_table = 'reports_comment'
        verbose_name = '需求评论'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author} - {self.content[:30]}"