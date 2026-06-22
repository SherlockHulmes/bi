from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django import forms
from .models import DbConnection, SqlScript, ExecutionLog


class DbConnectionForm(forms.ModelForm):
    """自定义表单：密码字段隐藏显示"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '输入数据库密码'}),
        label='密码',
        required=True,
    )

    class Meta:
        model = DbConnection
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 编辑时：密码字段留空表示不修改
        if self.instance and self.instance.pk:
            self.fields['password'].required = False
            self.fields['password'].widget.attrs['placeholder'] = '留空则不修改密码'

    def clean_password(self):
        password = self.cleaned_data.get('password')
        # 编辑时如果密码为空，保留原密码
        if self.instance and self.instance.pk and not password:
            return self.instance.password
        return password


@admin.register(DbConnection)
class DbConnectionAdmin(admin.ModelAdmin):
    form = DbConnectionForm
    list_display = ['name', 'host', 'port', 'database', 'username', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'host', 'database']
    list_editable = ['is_active']
    list_per_page = 20

    def save_model(self, request, obj, form, change):
        """保存时清除连接缓存"""
        super().save_model(request, obj, form, change)
        # 清除缓存以使用新密码
        from core.utils import _engine_cache
        cache_key = f"{obj.host}:{obj.port}/{obj.database}"
        _engine_cache.pop(cache_key, None)

    def response_change(self, request, obj):
        """处理自定义按钮点击"""
        if '_test_connection' in request.POST:
            from core.utils import get_engine_from_db_conn
            from core.utils import _engine_cache
            cache_key = f"{obj.host}:{obj.port}/{obj.database}"
            _engine_cache.pop(cache_key, None)
            try:
                engine = get_engine_from_db_conn(obj)
                with engine.connect() as c:
                    c.execute(__import__('sqlalchemy').text("SELECT 1"))
                self.message_user(request, f'✅ 连接测试成功: {obj.name}', messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f'❌ 连接测试失败: {str(e)[:200]}', messages.ERROR)
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)

    change_form_template = 'admin/sql_scripts/dbconnection_change_form.html'


@admin.register(SqlScript)
class SqlScriptAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_db', 'is_active', 'timeout', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    list_per_page = 20


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['script', 'trigger_type', 'status', 'duration', 'row_count', 'executed_by', 'executed_at']
    list_filter = ['status', 'trigger_type', 'executed_at']
    search_fields = ['script__name', 'output', 'error_message']
    readonly_fields = ['script', 'trigger_type', 'status', 'output', 'error_message', 'duration', 'row_count', 'executed_by', 'executed_at']
    list_per_page = 50