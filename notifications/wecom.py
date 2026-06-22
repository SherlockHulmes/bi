import logging
import requests
from django.conf import settings

logger = logging.getLogger('notifications')


def get_wecom_config():
    """从数据库获取企业微信配置"""
    try:
        from .models import NotificationConfig
        config = NotificationConfig.objects.filter(channel='wecom', is_active=True).first()
        if config:
            return config.webhook_url
    except Exception:
        pass
    return settings.WECOM_WEBHOOK


def send_wecom_message(title, content):
    """发送企业微信机器人消息"""
    webhook = get_wecom_config()
    if not webhook:
        logger.warning("企业微信 Webhook 未配置，请在管理后台 → 通知配置 中设置")
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"## {title}\n\n{content}"
        }
    }

    try:
        resp = requests.post(webhook, json=payload, timeout=10)
        result = resp.json()
        if result.get('errcode') == 0:
            logger.info(f"企业微信通知发送成功: {title}")
            return True
        else:
            logger.error(f"企业微信通知发送失败: {result}")
            return False
    except Exception as e:
        logger.error(f"企业微信通知发送异常: {e}")
        return False