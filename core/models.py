import uuid
import os
from django.db import models
from django.conf import settings


class FileUpload(models.Model):
    """文件上传记录，替代 Flask 版的内存 _file_registry"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_name = models.CharField('原始文件名', max_length=255)
    stored_path = models.CharField('存储路径', max_length=500)
    file_size = models.BigIntegerField('文件大小(bytes)', default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, verbose_name='上传用户'
    )
    created_at = models.DateTimeField('上传时间', auto_now_add=True)
    is_imported = models.BooleanField('是否已导入', default=False)

    class Meta:
        db_table = 'core_file_upload'
        verbose_name = '文件上传'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_name} ({self.get_size_display()})"

    def get_size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / 1024 / 1024:.1f} MB"

    def delete_file(self):
        """删除物理文件"""
        if self.stored_path and os.path.exists(self.stored_path):
            try:
                os.remove(self.stored_path)
            except OSError:
                pass

    @classmethod
    def cleanup_stale(cls):
        """清理超过 1 小时未导入的临时文件"""
        from django.utils import timezone
        from datetime import timedelta
        threshold = timezone.now() - timedelta(hours=1)
        stale = cls.objects.filter(is_imported=False, created_at__lt=threshold)
        for f in stale:
            f.delete_file()
        stale.delete()


class ExternalLink(models.Model):
    """主页外部链接配置"""
    title = models.CharField('链接标题', max_length=100)
    url = models.URLField('链接地址', max_length=500)
    icon = models.CharField('图标', max_length=50, default='bi-link-45deg',
                            help_text='Bootstrap Icons 图标类名，如 bi-google')
    description = models.CharField('描述', max_length=200, blank=True)
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'core_external_link'
        verbose_name = '外部链接'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title


class DashboardCard(models.Model):
    """主页数据大屏卡片配置"""
    title = models.CharField('卡片标题', max_length=100)
    description = models.CharField('卡片描述', max_length=200, blank=True)
    sql_script = models.ForeignKey(
        'sql_scripts.SqlScript', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='关联SQL脚本',
        help_text='选择要执行的SQL脚本来获取数据'
    )
    db_connection = models.ForeignKey(
        'sql_scripts.DbConnection', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='数据库连接'
    )
    card_type = models.CharField('卡片类型', max_length=20, default='table', choices=[
        ('table', '数据表格'),
        ('stat', '统计数字'),
        ('chart', '图表'),
    ])
    chart_type = models.CharField('图表类型', max_length=20, default='bar', choices=[
        ('bar', '柱状图'),
        ('line', '折线图'),
        ('pie', '饼图'),
        ('doughnut', '环形图'),
        ('horizontal_bar', '横向柱状图'),
    ])
    x_axis_field = models.TextField('X轴/标签字段', blank=True,
                                    help_text='SQL查询结果中的列名，支持逗号分隔多个字段（多个字段会拼接为标签），如：渠道类型,公司名称')
    y_axis_field = models.TextField('Y轴/数值字段', blank=True,
                                    help_text='SQL查询结果中的列名，支持逗号分隔多个字段，如：本金,利息。饼图只取第一个字段')
    group_by_field = models.CharField('维度字段', max_length=100, blank=True,
                                      help_text='按该字段分组生成多条数据系列，如：资金方。留空则不分组')
    stacked = models.BooleanField('堆叠模式', default=False,
                                  help_text='柱状图/折线图是否堆叠显示')
    show_data_label = models.BooleanField('显示数值标签', default=False,
                                          help_text='在图表上显示具体数值')
    sort_field = models.CharField('排序字段', max_length=100, blank=True,
                                  help_text='按该字段排序，留空则按数据原始顺序')
    chart_sort_dir = models.CharField('排序方向', max_length=10, default='none', choices=[
        ('none', '不排序'),
        ('ASC', '升序'),
        ('DESC', '降序'),
    ])
    sql_query = models.TextField('自定义SQL', blank=True,
                                 help_text='直接输入SQL（优先于关联的脚本）')
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    refresh_interval = models.IntegerField('自动刷新间隔(秒)', default=0,
                                           help_text='0表示不自动刷新')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'core_dashboard_card'
        verbose_name = '大屏卡片'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title
