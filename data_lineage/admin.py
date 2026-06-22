from django.contrib import admin
from .models import LineageScan, LineageTable, LineageEdge


class LineageTableInline(admin.TabularInline):
    model = LineageTable
    extra = 0
    fields = ['table_name', 'database_name', 'is_source', 'table_comment']
    readonly_fields = fields


class LineageEdgeInline(admin.TabularInline):
    model = LineageEdge
    extra = 0
    fields = ['source_database', 'source_table', 'target_database', 'target_table', 'event_name']
    readonly_fields = fields


@admin.register(LineageScan)
class LineageScanAdmin(admin.ModelAdmin):
    list_display = ['source_db', 'event_count', 'table_count', 'edge_count', 'scanned_at', 'scanned_by']
    list_filter = ['source_db', 'scanned_at']
    readonly_fields = ['source_db', 'scanned_at', 'scanned_by', 'event_count', 'table_count', 'edge_count']
    inlines = [LineageTableInline, LineageEdgeInline]
    list_per_page = 20