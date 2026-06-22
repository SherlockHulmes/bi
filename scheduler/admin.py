from django.contrib import admin
from .models import ScheduledTask


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'script', 'cron_expr', 'is_enabled', 'notify_channel', 'last_run_at', 'last_status']
    list_filter = ['is_enabled', 'notify_channel', 'last_status']
    search_fields = ['name', 'script__name']
    list_editable = ['is_enabled']
    list_per_page = 20