from django.db import models
from django.conf import settings
from sql_scripts.models import DbConnection


class QueryTemplate(models.Model):
    """自助取数查询模板"""
    name = models.CharField('模板名称', max_length=100)
    description = models.CharField('模板说明', max_length=200, blank=True)
    db_connection = models.ForeignKey(
        DbConnection, on_delete=models.CASCADE,
        verbose_name='数据库连接', related_name='query_templates'
    )
    sql_template = models.TextField('SQL模板',
                                    help_text='支持 ${param} 参数占位符')
    parameters_json = models.TextField('参数定义(JSON)', blank=True,
                                       help_text='[{"name":"start_date","label":"开始日期","type":"date","default":"2024-01-01"}]')
    visual_json = models.TextField('可视化状态(JSON)', blank=True,
                                   help_text='存储画布表格、连接、条件等可视化构建器状态')
    category = models.CharField('分类', max_length=50, blank=True)
    is_public = models.BooleanField('是否公开', default=True,
                                    help_text='公开模板所有用户可用，否则仅创建人可用')
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'data_extract_query_template'
        verbose_name = '查询模板'
        verbose_name_plural = verbose_name
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def get_parameters(self):
        import json
        if not self.parameters_json:
            return []
        try:
            return json.loads(self.parameters_json)
        except Exception:
            return []


class QueryHistory(models.Model):
    """查询执行历史"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        verbose_name='查询人', related_name='query_history'
    )
    template = models.ForeignKey(
        QueryTemplate, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='关联模板'
    )
    db_connection = models.ForeignKey(
        DbConnection, on_delete=models.CASCADE,
        verbose_name='数据库连接'
    )
    sql_executed = models.TextField('执行的SQL')
    row_count = models.IntegerField('结果行数', default=0)
    duration = models.FloatField('耗时(秒)', null=True, blank=True)
    status = models.CharField('状态', max_length=20, default='success',
                              choices=[('success', '成功'), ('failed', '失败')])
    error_message = models.TextField('错误信息', blank=True)
    result_json = models.TextField('结果数据(JSON)', blank=True)
    executed_at = models.DateTimeField('执行时间', auto_now_add=True)

    class Meta:
        db_table = 'data_extract_query_history'
        verbose_name = '查询历史'
        verbose_name_plural = verbose_name
        ordering = ['-executed_at']