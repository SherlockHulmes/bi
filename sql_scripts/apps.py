from django.apps import AppConfig


class SqlScriptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sql_scripts'
    verbose_name = 'SQL脚本管理'