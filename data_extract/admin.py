from django.contrib import admin
from .models import QueryTemplate, QueryHistory


@admin.register(QueryTemplate)
class QueryTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'db_connection', 'is_public', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'is_public', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    fieldsets = (
        (None, {'fields': ('name', 'description', 'category', 'db_connection')}),
        ('SQL配置', {'fields': ('sql_template', 'parameters_json')}),
        ('权限', {'fields': ('is_public', 'is_active', 'created_by')}),
    )


@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'template', 'db_connection', 'row_count', 'duration', 'status', 'executed_at']
    list_filter = ['status', 'executed_at']
    search_fields = ['sql_executed']
    readonly_fields = ['user', 'template', 'db_connection', 'sql_executed', 'row_count', 'duration', 'status', 'error_message', 'executed_at']