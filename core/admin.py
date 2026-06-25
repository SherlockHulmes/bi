from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import ExternalLink, DashboardCard, FileUpload
from .widgets import ColorPaletteWidget


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
            'fields': ('chart_type', 'chart_height', 'color_scheme', 'custom_colors', 'x_axis_field', 'y_axis_field', 'group_by_field'),
            'classes': ('collapse',),
            'description': '配置X轴/标签字段和Y轴/数值字段。选择"自定义"配色方案时，点击色块可弹出取色器选择颜色'
        }),
        ('图表高级配置', {
            'fields': ('stacked', 'show_data_label', 'sort_field', 'chart_sort_dir'),
            'classes': ('collapse',),
            'description': '堆叠模式、数值标签、数据排序'
        }),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'custom_colors':
            kwargs['widget'] = ColorPaletteWidget(num_colors=12)
            kwargs['help_text'] = '点击色块选择颜色，选完后自动保存为HEX值'
        if db_field.name == 'color_scheme':
            kwargs['help_text'] = ''
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    class Media:
        css = {'all': ('admin/css/color_scheme_preview.css',)}
        js = ('admin/js/color_scheme_preview.js',)


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'file_size', 'uploaded_by', 'is_imported', 'created_at')
    list_filter = ('is_imported',)
    readonly_fields = ('id', 'original_name', 'stored_path', 'file_size', 'uploaded_by', 'created_at')
