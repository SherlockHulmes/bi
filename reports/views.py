from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import ReportRequest, ReportComment
from .forms import ReportRequestForm, ReportCommentForm
from core.decorators import admin_required


@login_required
def report_list(request):
    """需求列表"""
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    reports = ReportRequest.objects.all()
    if status_filter:
        reports = reports.filter(status=status_filter)
    if priority_filter:
        reports = reports.filter(priority=priority_filter)
    
    from django.contrib.auth.models import User
    users = User.objects.filter(is_active=True)
    return render(request, 'reports/list.html', {
        'reports': reports,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': ReportRequest.STATUS_CHOICES,
        'priority_choices': ReportRequest.PRIORITY_CHOICES,
        'users': users,
    })


@login_required
def report_create(request):
    """创建需求"""
    if request.method == 'POST':
        form = ReportRequestForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()
            form.save_m2m()
            messages.success(request, '需求已创建')
            return redirect('reports:detail', pk=report.pk)
    else:
        form = ReportRequestForm()
    return render(request, 'reports/create.html', {'form': form})


@login_required
def report_detail(request, pk):
    """需求详情"""
    report = get_object_or_404(ReportRequest, pk=pk)
    comments = report.comments.all()
    comment_form = ReportCommentForm()
    
    if request.method == 'POST':
        comment_form = ReportCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.report = report
            comment.author = request.user
            comment.save()
            messages.success(request, '评论已添加')
            return redirect('reports:detail', pk=pk)
    
    return render(request, 'reports/detail.html', {
        'report': report,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
@require_POST
def report_inline_update(request, pk):
    """列表页内联更新字段"""
    import json
    from django.http import JsonResponse
    report = get_object_or_404(ReportRequest, pk=pk)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '无效数据'})
    
    field = data.get('field')
    value = data.get('value', '')
    
    if field == 'requester':
        report.requester = value
    elif field == 'developer':
        if value:
            from django.contrib.auth.models import User
            try:
                report.developer = User.objects.get(pk=value)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': '用户不存在'})
        else:
            report.developer = None
    elif field == 'created_by':
        if value:
            from django.contrib.auth.models import User
            try:
                report.created_by = User.objects.get(pk=value)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': '用户不存在'})
        else:
            report.created_by = None
    else:
        return JsonResponse({'success': False, 'error': '不支持的字段'})
    
    report.save()
    return JsonResponse({'success': True})


@login_required
@admin_required
@require_POST
def report_update_status(request, pk):
    """更新需求状态（需要管理员权限）"""
    report = get_object_or_404(ReportRequest, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(ReportRequest.STATUS_CHOICES):
        report.status = new_status
        report.save()
        messages.success(request, f'状态已更新为 {report.get_status_display()}')
    return redirect('reports:detail', pk=pk)