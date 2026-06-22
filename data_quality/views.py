import time
import logging
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from sqlalchemy import text

from .models import QualityRule, QualityCheckLog
from sql_scripts.models import DbConnection
from core.utils import get_engine_from_db_conn
from notifications.base import send_notification
from core.decorators import admin_required

logger = logging.getLogger('data_quality')


def _evaluate_condition(rule, result_data):
    """
    评估 SQL 查询结果是否触发告警。
    返回 (is_alert, result_value_str, alert_message)
    """
    condition = rule.condition_type
    row_count = result_data.get('row_count', 0)
    rows = result_data.get('rows', [])
    columns = result_data.get('columns', [])

    if condition == 'rows_gt_0':
        if row_count > 0:
            return True, f"返回 {row_count} 行", f"存在 {row_count} 条异常数据"
        return False, f"返回 {row_count} 行", ""

    elif condition == 'rows_eq_0':
        if row_count == 0:
            return True, f"返回 0 行", "数据缺失，查询结果为空"
        return False, f"返回 {row_count} 行", ""

    elif condition in ('value_gt', 'value_lt', 'value_eq'):
        column = rule.check_column
        threshold = rule.threshold

        if not column:
            return False, "未配置检查列", ""

        if column not in columns:
            return False, f"列 {column} 不存在于查询结果中", f"列 {column} 不存在"

        col_idx = columns.index(column)
        if len(rows) == 0:
            return False, "查询结果为空", ""

        try:
            value = float(rows[0][col_idx] if rows[0][col_idx] is not None else 0)
        except (ValueError, TypeError):
            return False, f"列 {column} 值无法转为数字: {rows[0][col_idx]}", ""

        if condition == 'value_gt' and value > threshold:
            return True, f"{column}={value}", f"{column}={value} 超过阈值 {threshold}"
        elif condition == 'value_lt' and value < threshold:
            return True, f"{column}={value}", f"{column}={value} 低于阈值 {threshold}"
        elif condition == 'value_eq' and value == threshold:
            return True, f"{column}={value}", f"{column}={value} 等于阈值 {threshold}"

        return False, f"{column}={value}", ""

    return False, "未知条件类型", ""


def execute_rule(rule, triggered_by='manual'):
    """
    执行质量规则检查。返回 QualityCheckLog 对象。
    """
    log = QualityCheckLog(
        rule=rule,
        status='error',
        triggered_by=triggered_by,
    )

    try:
        engine = get_engine_from_db_conn(rule.target_db)
        start_time = time.time()

        with engine.connect() as conn:
            result = conn.execute(text(rule.sql_query))
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                result_data = {
                    'columns': columns,
                    'rows': [[str(v) if v is not None else None for v in row] for row in rows[:100]],
                    'row_count': len(rows),
                }
            else:
                conn.commit()
                result_data = {'columns': [], 'rows': [], 'row_count': 0}

        duration = time.time() - start_time
        log.duration = round(duration, 2)

        is_alert, result_value, alert_message = _evaluate_condition(rule, result_data)
        log.result_value = result_value

        if is_alert:
            log.status = 'alert'
            log.alert_message = alert_message
        else:
            log.status = 'normal'

        # 更新规则状态
        rule.last_check_at = timezone.now()
        rule.last_check_status = log.status
        rule.save()

        # 如果告警，发送通知
        if is_alert and rule.notify_channel != 'none':
            now_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
            notify_content = (
                f'**BI工具箱 - 数据质量告警**\n\n'
                f'| 项目 | 详情 |\n'
                f'|------|------|\n'
                f'| 规则名称 | {rule.name} |\n'
                f'| 告警条件 | {rule.get_condition_type_display()} |\n'
                f'| 查询结果 | {result_value} |\n'
                f'| 告警信息 | {alert_message} |\n'
                f'| 目标数据库 | {rule.target_db.name} |\n'
                f'| 检查时间 | {now_str} |\n'
            )
            if rule.description:
                notify_content += f'| 规则描述 | {rule.description[:100]} |\n'

            send_notification(
                channel=rule.notify_channel,
                title='数据质量告警',
                content=notify_content,
            )

            # 如果有邮件收件人，单独发邮件
            if rule.email_recipients and rule.notify_channel != 'email':
                from notifications.email_sender import send_email_notification
                send_email_notification(
                    title=f'BI工具箱 - 数据质量告警: {rule.name}',
                    content=notify_content,
                )

    except Exception as e:
        log.error_message = str(e)[:500]
        log.result_value = f"执行错误: {str(e)[:200]}"
        rule.last_check_at = timezone.now()
        rule.last_check_status = 'error'
        rule.save()

    log.save()

    # 记录到全局执行日志
    from scheduler.models import ScheduledTaskLog
    try:
        ScheduledTaskLog.objects.create(
            task_name=f'质量检查: {rule.name}',
            script_name=rule.target_db.name if rule.target_db else '',
            sql_executed=rule.sql_query or '',
            trigger_type='quality_check',
            status='success' if log.status == 'normal' else 'failed',
            duration=log.duration,
            error_message=log.alert_message or log.error_message or '',
            notify_channel=rule.notify_channel if rule.notify_channel != 'none' else '',
        )
    except Exception:
        pass

    return log


@login_required
def rule_list(request):
    """规则列表"""
    rules = QualityRule.objects.select_related('target_db').all()
    return render(request, 'data_quality/rules.html', {'rules': rules})


@login_required
def rule_create(request):
    """创建规则"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '')
        target_db_id = request.POST.get('target_db')
        sql_query = request.POST.get('sql_query', '').strip()
        condition_type = request.POST.get('condition_type', 'rows_gt_0')
        check_column = request.POST.get('check_column', '').strip()
        threshold = request.POST.get('threshold', 0)
        schedule_type = request.POST.get('schedule_type', 'manual')
        interval_minutes = int(request.POST.get('interval_minutes', 5))
        schedule_hour = int(request.POST.get('hour', 8))
        schedule_minute = int(request.POST.get('minute', 0))
        days = request.POST.get('days', '')
        day_of_month = int(request.POST.get('day_of_month', 1))
        notify_channel = request.POST.get('notify_channel', 'none')
        email_recipients = request.POST.get('email_recipients', '').strip()
        is_enabled = request.POST.get('is_enabled') == 'on'

        if not name or not target_db_id or not sql_query:
            messages.error(request, '请填写完整信息（规则名称、目标数据库、SQL 查询必填）')
            db_connections = DbConnection.objects.filter(is_active=True)
            return render(request, 'data_quality/create.html', {
                'db_connections': db_connections,
                'condition_choices': QualityRule.CONDITION_CHOICES,
                'schedule_choices': QualityRule.SCHEDULE_CHOICES,
                'notify_choices': QualityRule.NOTIFY_CHOICES,
            })

        try:
            threshold = float(threshold)
        except ValueError:
            threshold = 0

        rule = QualityRule(
            name=name,
            description=description,
            target_db_id=target_db_id,
            sql_query=sql_query,
            condition_type=condition_type,
            check_column=check_column,
            threshold=threshold,
            schedule_type=schedule_type,
            interval_minutes=interval_minutes,
            schedule_hour=schedule_hour,
            schedule_minute=schedule_minute,
            schedule_days=days,
            schedule_day_of_month=day_of_month,
            notify_channel=notify_channel,
            email_recipients=email_recipients,
            is_enabled=is_enabled,
            created_by=request.user,
        )
        rule.save()
        messages.success(request, f'质量规则 "{name}" 已创建')
        return redirect('data_quality:rule_list')

    db_connections = DbConnection.objects.filter(is_active=True)
    return render(request, 'data_quality/create.html', {
        'db_connections': db_connections,
        'condition_choices': QualityRule.CONDITION_CHOICES,
        'schedule_choices': QualityRule.SCHEDULE_CHOICES,
        'notify_choices': QualityRule.NOTIFY_CHOICES,
    })


@login_required
def rule_edit(request, pk):
    """编辑规则"""
    rule = get_object_or_404(QualityRule, pk=pk)

    if request.method == 'POST':
        rule.name = request.POST.get('name', '').strip()
        rule.description = request.POST.get('description', '')
        target_db_id = request.POST.get('target_db')
        rule.sql_query = request.POST.get('sql_query', '').strip()
        rule.condition_type = request.POST.get('condition_type', 'rows_gt_0')
        rule.check_column = request.POST.get('check_column', '').strip()
        threshold = request.POST.get('threshold', 0)
        rule.schedule_type = request.POST.get('schedule_type', 'manual')
        rule.interval_minutes = int(request.POST.get('interval_minutes', 5))
        rule.schedule_hour = int(request.POST.get('hour', 8))
        rule.schedule_minute = int(request.POST.get('minute', 0))
        rule.schedule_days = request.POST.get('days', '')
        rule.schedule_day_of_month = int(request.POST.get('day_of_month', 1))
        rule.notify_channel = request.POST.get('notify_channel', 'none')
        rule.email_recipients = request.POST.get('email_recipients', '').strip()
        rule.is_enabled = request.POST.get('is_enabled') == 'on'

        try:
            rule.threshold = float(threshold)
        except ValueError:
            rule.threshold = 0

        if target_db_id:
            rule.target_db_id = target_db_id

        rule.save()
        messages.success(request, f'质量规则 "{rule.name}" 已更新')
        return redirect('data_quality:rule_list')

    db_connections = DbConnection.objects.filter(is_active=True)
    return render(request, 'data_quality/edit.html', {
        'rule': rule,
        'db_connections': db_connections,
        'condition_choices': QualityRule.CONDITION_CHOICES,
        'schedule_choices': QualityRule.SCHEDULE_CHOICES,
        'notify_choices': QualityRule.NOTIFY_CHOICES,
    })


@login_required
@require_POST
def rule_execute(request, pk):
    """手动执行规则检查"""
    rule = get_object_or_404(QualityRule, pk=pk)
    log = execute_rule(rule, triggered_by='manual')

    if log.status == 'alert':
        messages.warning(request, f'⚠️ 规则 "{rule.name}" 触发告警: {log.alert_message}')
    elif log.status == 'error':
        messages.error(request, f'❌ 规则 "{rule.name}" 执行错误: {log.error_message}')
    else:
        messages.success(request, f'✅ 规则 "{rule.name}" 检查正常: {log.result_value}')

    return redirect('data_quality:rule_list')


@login_required
def rule_logs(request, pk):
    """规则检查日志"""
    rule = get_object_or_404(QualityRule, pk=pk)
    logs = rule.logs.all()[:50]
    return render(request, 'data_quality/logs.html', {'rule': rule, 'logs': logs})


@login_required
@require_POST
def rule_copy(request, pk):
    """复制质量规则"""
    original = get_object_or_404(QualityRule, pk=pk)
    new_rule = QualityRule(
        name=f"{original.name} - 副本",
        description=original.description,
        target_db=original.target_db,
        sql_query=original.sql_query,
        condition_type=original.condition_type,
        check_column=original.check_column,
        threshold=original.threshold,
        schedule_type=original.schedule_type,
        interval_minutes=original.interval_minutes,
        schedule_hour=original.schedule_hour,
        schedule_minute=original.schedule_minute,
        schedule_days=original.schedule_days,
        schedule_day_of_month=original.schedule_day_of_month,
        notify_channel=original.notify_channel,
        email_recipients=original.email_recipients,
        is_enabled=False,
        created_by=request.user,
    )
    new_rule.save()
    messages.success(request, f'已复制规则 "{original.name}" → "{new_rule.name}"')
    return redirect('data_quality:rule_edit', pk=new_rule.pk)


@login_required
@admin_required
@require_POST
def rule_delete(request, pk):
    """删除规则（需要管理员权限）"""
    rule = get_object_or_404(QualityRule, pk=pk)
    name = rule.name
    rule.delete()
    messages.success(request, f'质量规则 "{name}" 已删除')
    return redirect('data_quality:rule_list')


@login_required
def all_logs(request):
    """所有检查日志"""
    logs = QualityCheckLog.objects.select_related('rule').all()[:100]
    return render(request, 'data_quality/logs.html', {'rule': None, 'logs': logs})