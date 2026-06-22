from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('sql_scripts', '0002_auto_20260529_1429'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='链接标题')),
                ('url', models.URLField(max_length=500, verbose_name='链接地址')),
                ('icon', models.CharField(default='bi-link-45deg', help_text='Bootstrap Icons 图标类名，如 bi-google', max_length=50, verbose_name='图标')),
                ('description', models.CharField(blank=True, max_length=200, verbose_name='描述')),
                ('sort_order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '外部链接',
                'verbose_name_plural': '外部链接',
                'db_table': 'core_external_link',
                'ordering': ['sort_order', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DashboardCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='卡片标题')),
                ('description', models.CharField(blank=True, max_length=200, verbose_name='卡片描述')),
                ('card_type', models.CharField(choices=[('table', '数据表格'), ('stat', '统计数字'), ('chart', '图表')], default='table', max_length=20, verbose_name='卡片类型')),
                ('sql_query', models.TextField(blank=True, help_text='直接输入SQL（优先于关联的脚本）', verbose_name='自定义SQL')),
                ('sort_order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('refresh_interval', models.IntegerField(default=0, help_text='0表示不自动刷新', verbose_name='自动刷新间隔(秒)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('db_connection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sql_scripts.dbconnection', verbose_name='数据库连接')),
                ('sql_script', models.ForeignKey(blank=True, help_text='选择要执行的SQL脚本来获取数据', null=True, on_delete=django.db.models.deletion.SET_NULL, to='sql_scripts.sqlscript', verbose_name='关联SQL脚本')),
            ],
            options={
                'verbose_name': '大屏卡片',
                'verbose_name_plural': '大屏卡片',
                'db_table': 'core_dashboard_card',
                'ordering': ['sort_order', '-created_at'],
            },
        ),
    ]