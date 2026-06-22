from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sql_scripts', '0002_auto_20260529_1429'),
    ]

    operations = [
        migrations.CreateModel(
            name='QueryTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='模板名称')),
                ('description', models.CharField(blank=True, max_length=200, verbose_name='模板说明')),
                ('sql_template', models.TextField(help_text='支持 ${param} 参数占位符', verbose_name='SQL模板')),
                ('parameters_json', models.TextField(blank=True, help_text='[{"name":"start_date","label":"开始日期","type":"date","default":"2024-01-01"}]', verbose_name='参数定义(JSON)')),
                ('category', models.CharField(blank=True, max_length=50, verbose_name='分类')),
                ('is_public', models.BooleanField(default=True, help_text='公开模板所有用户可用，否则仅创建人可用', verbose_name='是否公开')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('db_connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='query_templates', to='sql_scripts.dbconnection', verbose_name='数据库连接')),
            ],
            options={
                'verbose_name': '查询模板',
                'verbose_name_plural': '查询模板',
                'db_table': 'data_extract_query_template',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='QueryHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sql_executed', models.TextField(verbose_name='执行的SQL')),
                ('row_count', models.IntegerField(default=0, verbose_name='结果行数')),
                ('duration', models.FloatField(blank=True, null=True, verbose_name='耗时(秒)')),
                ('status', models.CharField(choices=[('success', '成功'), ('failed', '失败')], default='success', max_length=20, verbose_name='状态')),
                ('error_message', models.TextField(blank=True, verbose_name='错误信息')),
                ('result_json', models.TextField(blank=True, verbose_name='结果数据(JSON)')),
                ('executed_at', models.DateTimeField(auto_now_add=True, verbose_name='执行时间')),
                ('db_connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sql_scripts.dbconnection', verbose_name='数据库连接')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='data_extract.querytemplate', verbose_name='关联模板')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='query_history', to=settings.AUTH_USER_MODEL, verbose_name='查询人')),
            ],
            options={
                'verbose_name': '查询历史',
                'verbose_name_plural': '查询历史',
                'db_table': 'data_extract_query_history',
                'ordering': ['-executed_at'],
            },
        ),
    ]