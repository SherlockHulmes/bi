from django.apps import AppConfig


class DataLineageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_lineage'
    verbose_name = '数据血缘'