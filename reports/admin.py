from django.contrib import admin
from .models import ReportRequest, ReportComment


class ReportCommentInline(admin.TabularInline):
    model = ReportComment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(ReportRequest)
class ReportRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'status', 'requester', 'developer', 'created_by', 'expected_date', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'requester']
    list_editable = ['status', 'priority', 'developer']
    inlines = [ReportCommentInline]
    list_per_page = 20
    fieldsets = (
        (None, {'fields': ('title', 'description', 'priority', 'status')}),
        ('人员', {'fields': ('requester', 'developer', 'created_by')}),
        ('时间', {'fields': ('expected_date', 'notes')}),
    )


@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ['report', 'author', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content']