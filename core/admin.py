from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import ExternalLink, DashboardCard, FileUpload


class BiToolkitAdminSite(AdminSite):
    site_header = 'BI 工具箱 · 管理后台'
    site_title = 'BI 工具箱管理'
    index_title = '系统管理'
    site_url = '/'


# 替换默认 admin site
admin_site = BiToolkitAdminSite(name='bi_admin')


@admin.register(ExternalLink)
class ExternalLinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'icon', 'sort_order', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('sort_order', 'is_active')
    search_fields = ('title', 'url', 'description')


@admin.register(DashboardCard)
class DashboardCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'card_type', 'db_connection', 'refresh_interval', 'sort_order', 'is_active')
    list_filter = ('is_active', 'card_type')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'card_type', 'sort_order', 'is_active', 'refresh_interval')
        }),
        ('数据源', {
            'fields': ('db_connection', 'sql_script', 'sql_query'),
            'description': '选择数据库连接，并关联SQL脚本或直接输入SQL'
        }),
    )


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'file_size', 'uploaded_by', 'is_imported', 'created_at')
    list_filter = ('is_imported',)
    readonly_fields = ('id', 'original_name', 'stored_path', 'file_size', 'uploaded_by', 'created_at')
