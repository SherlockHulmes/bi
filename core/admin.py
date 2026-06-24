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
    list_display = ('title', 'card_type', 'chart_type', 'db_connection', 'refresh_interval', 'sort_order', 'is_active')
    list_filter = ('is_active', 'card_type', 'chart_type')
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
        ('图表配置（仅图表类型有效）', {
            'fields': ('chart_type', 'chart_height', 'x_axis_field', 'y_axis_field', 'group_by_field'),
            'classes': ('collapse',),
            'description': '配置X轴/标签字段和Y轴/数值字段（对应SQL查询结果的列名）。维度字段可按某列分组生成多条数据系列。多X字段时第一个作为X轴标签，其余作为子维度分组'
        }),
        ('图表高级配置', {
            'fields': ('stacked', 'show_data_label', 'sort_field', 'chart_sort_dir'),
            'classes': ('collapse',),
            'description': '堆叠模式、数值标签、数据排序'
        }),
    )


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'file_size', 'uploaded_by', 'is_imported', 'created_at')
    list_filter = ('is_imported',)
    readonly_fields = ('id', 'original_name', 'stored_path', 'file_size', 'uploaded_by', 'created_at')
