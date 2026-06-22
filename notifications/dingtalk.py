import time
import hmac
import hashlib
import base64
import logging
import requests
from urllib.parse import quote_plus
from django.conf import settings

logger = logging.getLogger('notifications')


def get_dingtalk_config():
    """从数据库获取钉钉配置，优先级高于 .env"""
    try:
        from .models import NotificationConfig
        config = NotificationConfig.objects.filter(channel='dingtalk', is_active=True).first()
        if config:
            return config.webhook_url, config.secret
    except Exception:
        pass
    # 回退到 settings（.env）
    return settings.DINGTALK_WEBHOOK, settings.DINGTALK_SECRET


def send_dingtalk_message(title, content):
    """发送钉钉机器人消息"""
    webhook, secret = get_dingtalk_config()
    if not webhook:
        logger.warning("钉钉 Webhook 未配置，请在管理后台 → 通知配置 中设置")
        return False

    # 加签
    if secret:
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f'{timestamp}\n{secret}'
        hmac_code = hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))
        webhook = f"{webhook}&timestamp={timestamp}&sign={sign}"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": f"### {title}\n\n{content}"
        }
    }

    try:
        resp = requests.post(webhook, json=payload, timeout=10)
        result = resp.json()
        if result.get('errcode') == 0:
            logger.info(f"钉钉通知发送成功: {title}")
            return True
        else:
            logger.error(f"钉钉通知发送失败: {result}")
            return False
    except Exception as e:
        logger.error(f"钉钉通知发送异常: {e}")
        return False