from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """要求管理员权限的装饰器（用于 AJAX 和普通视图）"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '请先登录'}, status=401)
            return redirect('login')
        if not request.user.is_staff and not request.user.is_superuser:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '需要管理员权限'}, status=403)
            messages.error(request, '需要管理员权限才能执行此操作')
            return redirect('core:homepage')
        return view_func(request, *args, **kwargs)
    return wrapper


def superuser_required(view_func):
    """要求超级管理员权限的装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '请先登录'}, status=401)
            return redirect('login')
        if not request.user.is_superuser:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': '需要超级管理员权限'}, status=403)
            messages.error(request, '需要超级管理员权限才能执行此操作')
            return redirect('core:homepage')
        return view_func(request, *args, **kwargs)
    return wrapper