import logging
from django.utils import timezone

logger = logging.getLogger('notifications')

# 固定关键词，钉钉机器人需要消息中包含此关键词
KEYWORD = 'BI工具箱'


def send_notification(channel, title, content):
    """统一通知接口，自动添加关键词前缀"""
    # 确保标题包含关键词
    if KEYWORD not in title:
        title = f'{KEYWORD} - {title}'

    logger.info(f"发送通知 [{channel}]: {title}")

    if channel == 'dingtalk':
        from .dingtalk import send_dingtalk_message
        return send_dingtalk_message(title, content)
    elif channel == 'wecom':
        from .wecom import send_wecom_message
        return send_wecom_message(title, content)
    elif channel == 'email':
        from .email_sender import send_email_notification
        return send_email_notification(title, content)
    else:
        logger.warning(f"不支持的通知渠道: {channel}")
        return False


def format_import_notification(table_name, success, row_count, error_message=None):
    """数据导入通知格式"""
    now = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
    result = '✅ 成功' if success else '❌ 失败'

    lines = [
        f'**{KEYWORD} - 数据导入通知**',
        '',
        f'| 项目 | 详情 |',
        f'|------|------|',
        f'| 导入结果 | {result} |',
        f'| 目标表名 | `{table_name}` |',
        f'| 影响行数 | {row_count} 行 |',
        f'| 执行时间 | {now} |',
    ]
    if error_message:
        lines.append(f'| 错误信息 | {error_message[:200]} |')

    return '\n'.join(lines)


def format_task_notification(task_name, success, row_count=None, duration=None, error_message=None, schedule_display=None):
    """定时任务执行通知格式"""
    now = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
    result = '✅ 成功' if success else '❌ 失败'

    lines = [
        f'**{KEYWORD} - 定时任务通知**',
        '',
        f'| 项目 | 详情 |',
        f'|------|------|',
        f'| 任务名称 | {task_name} |',
        f'| 执行结果 | {result} |',
    ]
    if row_count is not None:
        lines.append(f'| 影响行数 | {row_count} 行 |')
    if duration is not None:
        lines.append(f'| 执行耗时 | {duration:.2f} 秒 |')
    lines.append(f'| 执行时间 | {now} |')
    if error_message:
        lines.append(f'| 错误信息 | {error_message[:200]} |')

    return '\n'.join(lines)


def format_status_notification(task_name, schedule_display, is_enabled, last_run_at=None, last_status=None):
    """任务状态通知格式（手动发送）"""
    status = '🟢 启用' if is_enabled else '🔴 停用'
    if last_run_at and last_status:
        last_run_local = timezone.localtime(last_run_at)
        last_run_text = f"{'✅ 成功' if last_status == 'success' else '❌ 失败'} ({last_run_local.strftime('%Y-%m-%d %H:%M')})"
    else:
        last_run_text = '从未执行'

    lines = [
        f'**{KEYWORD} - 任务状态通知**',
        '',
        f'| 项目 | 详情 |',
        f'|------|------|',
        f'| 任务名称 | {task_name} |',
        f'| 执行计划 | {schedule_display} |',
        f'| 当前状态 | {status} |',
        f'| 上次执行 | {last_run_text} |',
    ]

    return '\n'.join(lines)


def format_test_notification():
    """测试通知格式"""
    now = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
    return f'**{KEYWORD} - 通知测试**\n\n这是一条测试消息。\n发送时间：{now}'
