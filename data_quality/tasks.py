import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('data_quality')


def _match_quality_rule(rule, now):
    """判断规则是否应该在当前时间执行"""
    if rule.schedule_type == 'manual':
        return False
    if rule.schedule_type == 'every_minutes':
        # 每N分钟：检查当前分钟是否能被间隔整除
        interval = rule.interval_minutes or 5
        total_minutes = now.hour * 60 + now.minute
        return total_minutes % interval == 0
    if rule.schedule_hour != now.hour or rule.schedule_minute != now.minute:
        return False
    if rule.schedule_type == 'daily':
        return True
    if rule.schedule_type == 'weekly':
        days = [d.strip() for d in rule.schedule_days.split(',') if d.strip()]
        return str(now.weekday()) in days
    if rule.schedule_type == 'monthly':
        return now.day == rule.schedule_day_of_month
    return False


@shared_task
def check_quality_rules():
    """每分钟检查一次，执行到期的质量规则"""
    from .models import QualityRule
    from .views import execute_rule

    now = timezone.localtime(timezone.now())
    rules = QualityRule.objects.filter(is_enabled=True)

    for rule in rules:
        if not _match_quality_rule(rule, now):
            continue

        # 避免 2 分钟内重复执行
        if rule.last_check_at:
            last_run_local = timezone.localtime(rule.last_check_at)
            if (now - last_run_local).total_seconds() < 120:
                continue

        logger.info(f"质量规则到期，开始检查: {rule.name}")
        try:
            log = execute_rule(rule, triggered_by='scheduled')
            if log.status == 'alert':
                logger.warning(f"质量规则告警: {rule.name} - {log.alert_message}")
            elif log.status == 'error':
                logger.error(f"质量规则执行错误: {rule.name} - {log.error_message}")
            else:
                logger.info(f"质量规则检查正常: {rule.name} - {log.result_value}")
        except Exception as e:
            logger.error(f"质量规则执行异常: {rule.name} - {e}")