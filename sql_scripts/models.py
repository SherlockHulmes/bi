from django.db import models
from django.conf import settings


class DbConnection(models.Model):
    """数据库连接配置"""
    name = models.CharField('连接名称', max_length=100)
    host = models.CharField('主机', max_length=200)
    port = models.IntegerField('端口', default=3306)
    username = models.CharField('用户名', max_length=100)
    password = models.CharField('密码', max_length=200)
    database = models.CharField('数据库名', max_length=100)
    charset = models.CharField('字符集', max_length=20, default='utf8mb4')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sql_scripts_db_connection'
        verbose_name = '数据库连接'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port}/{self.database})"


class SqlScript(models.Model):
    """SQL 脚本管理"""
    name = models.CharField('脚本名称', max_length=200)
    description = models.TextField('脚本说明', blank=True)
    file = models.FileField('SQL文件', upload_to='scripts/', null=True, blank=True)
    content = models.TextField('脚本内容', blank=True, help_text='可以直接粘贴 SQL，或上传文件')
    target_db = models.ForeignKey(
        DbConnection,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='目标数据库',
        related_name='scripts'
    )
    is_active = models.BooleanField('是否启用', default=True)
    timeout = models.IntegerField('执行超时(秒)', default=300)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'sql_scripts_script'
        verbose_name = 'SQL脚本'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_sql_content(self):
        """获取 SQL 内容，优先从文件读取"""
        if self.file:
            try:
                with open(self.file.path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        return self.content


class ExecutionLog(models.Model):
    """SQL 执行日志"""
    TRIGGER_CHOICES = [
        ('manual', '手动执行'),
        ('scheduled', '定时执行'),
    ]
    STATUS_CHOICES = [
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    script = models.ForeignKey(SqlScript, on_delete=models.CASCADE, related_name='logs', verbose_name='脚本')
    trigger_type = models.CharField('触发类型', max_length=20, choices=TRIGGER_CHOICES, default='manual')
    status = models.CharField('执行状态', max_length=20, choices=STATUS_CHOICES, default='running')
    output = models.TextField('执行结果', blank=True)
    error_message = models.TextField('错误信息', blank=True)
    duration = models.FloatField('执行耗时(秒)', null=True, blank=True)
    row_count = models.IntegerField('影响行数', null=True, blank=True)
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, verbose_name='执行人'
    )
    executed_at = models.DateTimeField('执行时间', auto_now_add=True)

    class Meta:
        db_table = 'sql_scripts_log'
        verbose_name = '执行日志'
        verbose_name_plural = verbose_name
        ordering = ['-executed_at']

    def __str__(self):
        return f"{self.script.name} - {self.get_status_display()} ({self.executed_at})"