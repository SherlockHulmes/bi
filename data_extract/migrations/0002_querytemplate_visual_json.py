from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_extract', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='querytemplate',
            name='visual_json',
            field=models.TextField(blank=True, help_text='存储画布表格、连接、条件等可视化构建器状态', verbose_name='可视化状态(JSON)'),
        ),
    ]