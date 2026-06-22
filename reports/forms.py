from django import forms
from django.contrib.auth.models import User
from .models import ReportRequest, ReportComment


class ReportRequestForm(forms.ModelForm):
    developer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        label='开发人员',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='-- 请选择开发人员 --'
    )

    class Meta:
        model = ReportRequest
        fields = ['title', 'description', 'priority', 'requester', 'developer', 'expected_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入需求标题'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请详细描述需求'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'requester': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '需求提出人姓名'}),
            'expected_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ReportCommentForm(forms.ModelForm):
    class Meta:
        model = ReportComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': '添加评论或跟进记录...'
            }),
        }