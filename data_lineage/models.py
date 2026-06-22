from django.db import models
from django.conf import settings
from sql_scripts.models import DbConnection


class LineageScan(models.Model):
    """血缘扫描记录"""
    source_db = models.ForeignKey(
        DbConnection, on_delete=models.CASCADE,
        verbose_name='数据库连接',
        related_name='lineage_scans'
    )
    scanned_at = models.DateTimeField('扫描时间', auto_now_add=True)
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, verbose_name='操作人'
    )
    event_count = models.IntegerField('事件数', default=0)
    table_count = models.IntegerField('表数', default=0)
    edge_count = models.IntegerField('依赖关系数', default=0)

    class Meta:
        db_table = 'data_lineage_scan'
        verbose_name = '扫描记录'
        verbose_name_plural = verbose_name
        ordering = ['-scanned_at']

    def __str__(self):
        return f"扫描 {self.source_db.name} ({self.scanned_at})"


class LineageTable(models.Model):
    """血缘表信息"""
    scan = models.ForeignKey(
        LineageScan, on_delete=models.CASCADE,
        related_name='tables', verbose_name='扫描记录'
    )
    table_name = models.CharField('表名', max_length=200)
    database_name = models.CharField('所属数据库', max_length=200, blank=True)
    table_comment = models.TextField('表注释', blank=True)
    columns_json = models.TextField('字段列表(JSON)', blank=True,
                                     help_text='JSON 格式的字段信息：[{"name":"col","type":"int","comment":"注释"}]')
    is_source = models.BooleanField('是否为基础表', default=False,
                                     help_text='基础表来自源库(A)，中间表来自开发库(B)')

    class Meta:
        db_table = 'data_lineage_table'
        verbose_name = '血缘表'
        verbose_name_plural = verbose_name
        ordering = ['table_name']

    def __str__(self):
        return f"{self.database_name}.{self.table_name}"

    def get_columns(self):
        """获取字段列表"""
        import json
        if not self.columns_json:
            return []
        try:
            return json.loads(self.columns_json)
        except:
            return []


class LineageEdge(models.Model):
    """血缘依赖关系"""
    scan = models.ForeignKey(
        LineageScan, on_delete=models.CASCADE,
        related_name='edges', verbose_name='扫描记录'
    )
    source_table = models.CharField('源表名', max_length=200)
    source_database = models.CharField('源表数据库', max_length=200, blank=True)
    target_table = models.CharField('目标表名', max_length=200)
    target_database = models.CharField('目标表数据库', max_length=200, blank=True)
    event_name = models.CharField('事件名', max_length=200, blank=True)
    event_sql = models.TextField('事件SQL', blank=True)

    class Meta:
        db_table = 'data_lineage_edge'
        verbose_name = '血缘关系'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.source_table} → {self.target_table}"