import time
import logging
from celery import shared_task
from django.utils import timezone
from sqlalchemy import text

from sql_scripts.models import SqlScript, ExecutionLog
from core.utils import get_engine_from_db_conn, get_default_engine
from notifications.base import send_notification, format_task_notification

logger = logging.getLogger('scheduler')


def _match_scheduled_task(task, now):
    """判断任务是否应该在当前时间执行"""
    if task.schedule_hour != now.hour or task.schedule_minute != now.minute:
        return False

    if task.schedule_type == 'daily':
        return True
    if task.schedule_type == 'weekly':
        days = [d.strip() for d in task.schedule_days.split(',') if d.strip()]
        return str(now.weekday()) in days
    if task.schedule_type == 'monthly':
        return now.day == task.schedule_day_of_month
    # 自定义模式由 cron_expr 驱动，不在这里判断
    return False


@shared_task
def check_scheduled_tasks():
    """每分钟检查一次，执行到期的定时任务"""
    from .models import ScheduledTask

    now = timezone.localtime(timezone.now())
    all_tasks = ScheduledTask.objects.all()
    enabled_tasks = ScheduledTask.objects.filter(is_enabled=True)

    logger.info(f"[定时检查] 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"总任务数: {all_tasks.count()}, 启用任务数: {enabled_tasks.count()}")

    for task in enabled_tasks:
        should_run = False
        logger.info(f"[定时检查] 任务: {task.name}, 类型: {task.schedule_type}, "
                    f"计划时间: {task.schedule_hour:02d}:{task.schedule_minute:02d}, "
                    f"启用: {task.is_enabled}")

        if task.schedule_type == 'custom' and task.cron_expr:
            # 自定义 cron 模式，用模型自带的 cron_expr 对比
            import croniter
            try:
                cron = croniter.croniter(task.cron_expr, now)
                prev_run = cron.get_prev()
                if abs((now.timestamp() - prev_run)) <= 61:
                    should_run = True
            except Exception as e:
                logger.error(f"解析 cron 表达式失败: {task.name} {task.cron_expr} {e}")
                continue
        else:
            should_run = _match_scheduled_task(task, now)

        if not should_run:
            continue

        # 避免在 2 分钟内重复执行
        if task.last_run_at:
            last_run_local = timezone.localtime(task.last_run_at)
            if (now - last_run_local).total_seconds() < 120:
                continue

        logger.info(f"定时任务到期，开始执行: {task.name}")
        execute_scheduled_script.delay(task.pk)


@shared_task
def execute_scheduled_script(task_id):
    """定时执行 SQL 脚本的 Celery 任务"""
    from .models import ScheduledTask, ScheduledTaskLog

    try:
        task = ScheduledTask.objects.get(pk=task_id, is_enabled=True)
    except ScheduledTask.DoesNotExist:
        logger.warning(f"定时任务 {task_id} 不存在或已禁用")
        return

    script = task.script
    sql_content = script.get_sql_content()

    if not sql_content or not sql_content.strip():
        logger.warning(f"脚本 {script.name} 内容为空，跳过执行")
        return

    # 创建任务日志
    task_log = ScheduledTaskLog.objects.create(
        task=task,
        task_name=task.name,
        script_name=script.name,
        sql_executed=sql_content,
        trigger_type='scheduled',
        status='success',
        notify_channel=task.notify_channel if task.notify_channel != 'none' else '',
        notify_target=task.email_recipients or '',
    )

    log = ExecutionLog.objects.create(
        script=script,
        trigger_type='scheduled',
        status='running',
    )

    try:
        if script.target_db:
            engine = get_engine_from_db_conn(script.target_db)
        else:
            engine = get_default_engine()

        from core.utils import execute_sql_statements
        all_results, all_output, total_affected, duration = execute_sql_statements(engine, sql_content)

        import json
        log.status = 'success'
        log.output = json.dumps(all_results, ensure_ascii=False, default=str)
        log.duration = round(duration, 2)
        log.row_count = total_affected
        log.save()

        task_log.row_count = total_affected
        task_log.duration = round(duration, 2)

        task.last_run_at = timezone.now()
        task.last_status = 'success'
        task.save()

        # 发送邮件（如果有收件人）
        email_sent = False
        if task.email_recipients and task.email_recipients.strip():
            try:
                import io
                import openpyxl
                from notifications.email_sender import send_email_notification

                wb = openpyxl.Workbook()
                wb.remove(wb.active)
                for idx, r in enumerate(all_results):
                    if 'columns' in r and 'rows' in r:
                        ws = wb.create_sheet(title=f"结果集{idx + 1}")
                        ws.append(r['columns'])
                        for row in r['rows']:
                            ws.append([str(v) if v is not None else '' for v in row])
                buf = io.BytesIO()
                wb.save(buf)
                buf.seek(0)
                excel_bytes = buf.getvalue()
                filename = f"{task.name}_{timezone.localtime(timezone.now()).strftime('%Y%m%d_%H%M%S')}.xlsx"

                email_content = format_task_notification(task_name=task.name, success=True, row_count=total_affected, duration=duration)
                recipients = [r.strip() for r in task.email_recipients.split(',') if r.strip()]
                email_sent = send_email_notification(
                    title=f'BI工具箱 - SQL执行结果: {task.name}',
                    content=email_content,
                    attachment_bytes=excel_bytes,
                    attachment_filename=filename,
                    recipients=recipients,
                )
            except Exception as em:
                logger.error(f"邮件发送失败: {em}")

        task_log.notify_status = email_sent if task.email_recipients and task.email_recipients.strip() else None

        # 发送通知
        if task.notify_channel != 'none':
            if email_sent:
                recipients = [r.strip() for r in task.email_recipients.split(',') if r.strip()]
                now_str = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
                notify_content = f'**BI工具箱 - 邮件发送通知**\n\n' \
                    f'| 项目 | 详情 |\n' \
                    f'|------|------|\n' \
                    f'| 任务名称 | {task.name} |\n' \
                    f'| 发送结果 | ✅ 成功发送到 {", ".join(recipients)} |\n' \
                    f'| 收件人 | {", ".join(recipients)} |\n' \
                    f'| 影响行数 | {total_affected} 行 |\n' \
                    f'| 执行时间 | {now_str} |'
                send_notification(channel=task.notify_channel, title='邮件发送通知', content=notify_content)
            else:
                content = format_task_notification(task_name=task.name, success=True, row_count=total_affected, duration=duration)
                send_notification(channel=task.notify_channel, title='定时任务通知', content=content)

        task_log.save()
        logger.info(f"定时任务执行成功: {task.name}, 耗时 {duration:.2f}s")

    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.save()

        task_log.status = 'failed'
        task_log.error_message = str(e)
        task_log.save()

        task.last_run_at = timezone.now()
        task.last_status = 'failed'
        task.save()

        if task.notify_channel != 'none':
            content = format_task_notification(
                task_name=task.name,
                success=False,
                error_message=str(e),
            )
            send_notification(
                channel=task.notify_channel,
                title='定时任务通知',
                content=content
            )

        logger.error(f"定时任务执行失败: {task.name}, 错误: {e}")
