from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django import forms
from .models import NotificationConfig


class NotificationConfigForm(forms.ModelForm):
    class Meta:
        model = NotificationConfig
        fields = '__all__'
        widgets = {
            'webhook_url': forms.TextInput(attrs={'placeholder': 'https://oapi.dingtalk.com/robot/send?access_token=xxx'}),
            'secret': forms.TextInput(attrs={'placeholder': '钉钉加签密钥（可选）'}),
        }


@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    form = NotificationConfigForm
    list_display = ['channel', 'webhook_url', 'is_active', 'updated_at']
    list_filter = ['is_active']
    list_editable = ['is_active']
    list_per_page = 10
    change_form_template = 'admin/notifications/notificationconfig_change_form.html'

    def response_change(self, request, obj):
        if '_test_notification' in request.POST:
            try:
                from .base import send_notification
                from .base import format_test_notification
                result = send_notification(
                    channel=obj.channel,
                    title='通知测试',
                    content=format_test_notification()
                )
                if result:
                    self.message_user(request, f'✅ 测试消息已发送到 {obj.get_channel_display()}', messages.SUCCESS)
                else:
                    self.message_user(request, f'❌ 发送失败，请检查 Webhook URL 和密钥配置', messages.ERROR)
            except Exception as e:
                self.message_user(request, f'❌ 发送异常: {str(e)[:200]}', messages.ERROR)
            return HttpResponseRedirect(request.path)
        return super().response_change(request, obj)