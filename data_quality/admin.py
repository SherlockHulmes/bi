from django.contrib import admin
from .models import QualityRule, QualityCheckLog


@admin.register(QualityRule)
class QualityRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_db', 'condition_type', 'schedule_type', 'notify_channel', 'is_enabled', 'last_check_status', 'last_check_at']
    list_filter = ['is_enabled', 'condition_type', 'schedule_type', 'notify_channel', 'last_check_status']
    search_fields = ['name', 'description', 'sql_query']
    list_editable = ['is_enabled']
    list_per_page = 20


@admin.register(QualityCheckLog)
class QualityCheckLogAdmin(admin.ModelAdmin):
    list_display = ['rule', 'status', 'triggered_by', 'duration', 'executed_at']
    list_filter = ['status', 'triggered_by', 'executed_at']
    search_fields = ['rule__name', 'result_value', 'alert_message', 'error_message']
    readonly_fields = ['rule', 'status', 'result_value', 'alert_message', 'error_message', 'duration', 'executed_at', 'triggered_by']
    list_per_page = 50