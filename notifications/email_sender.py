import io
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger('notifications')


def get_email_config():
    """从数据库获取邮件配置"""
    try:
        from .models import NotificationConfig
        config = NotificationConfig.objects.filter(channel='email', is_active=True).first()
        if config:
            return {
                'host': config.email_host,
                'port': config.email_port,
                'use_ssl': config.email_use_ssl,
                'user': config.email_host_user,
                'password': config.email_host_password,
                'recipients': [r.strip() for r in config.email_recipients.split(',') if r.strip()],
            }
    except Exception:
        pass
    return None


def send_email_notification(title, content, attachment_bytes=None, attachment_filename=None, recipients=None):
    """发送邮件通知
    
    Args:
        title: 邮件标题
        content: 邮件正文（Markdown 格式，转为纯文本）
        attachment_bytes: 附件文件字节内容（可选）
        attachment_filename: 附件文件名（可选）
        recipients: 收件人列表（可选，优先使用此参数，否则从配置读取）
    
    Returns:
        bool: 是否发送成功
    """
    config = get_email_config()
    if not config:
        logger.warning("邮件配置未设置，请在管理后台 → 通知配置 中设置")
        return False

    # 优先使用传入的收件人，否则使用配置中的收件人
    if recipients:
        config['recipients'] = recipients

    if not config['recipients']:
        logger.warning("未配置收件人邮箱")
        return False

    try:
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = config['user']
        msg['To'] = ', '.join(config['recipients'])

        # 正文
        msg.attach(MIMEText(content, 'plain', 'utf-8'))

        # 附件
        if attachment_bytes and attachment_filename:
            # 根据文件扩展名选择正确的 MIME 类型
            if attachment_filename.endswith('.xlsx'):
                mime_type = ('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            elif attachment_filename.endswith('.xls'):
                mime_type = ('application', 'vnd.ms-excel')
            elif attachment_filename.endswith('.csv'):
                mime_type = ('text', 'csv')
            else:
                mime_type = ('application', 'octet-stream')
            part = MIMEBase(*mime_type)
            part.set_payload(attachment_bytes)
            encoders.encode_base64(part)
            from email.header import Header
            part.add_header('Content-Disposition', f'attachment; filename="{Header(attachment_filename, "utf-8")}"')
            msg.attach(part)

        # 发送
        if config['use_ssl']:
            server = smtplib.SMTP_SSL(config['host'], config['port'], timeout=15)
        else:
            server = smtplib.SMTP(config['host'], config['port'], timeout=15)
            server.starttls()

        server.login(config['user'], config['password'])
        server.sendmail(config['user'], config['recipients'], msg.as_string())
        server.quit()

        logger.info(f"邮件通知发送成功: {title} -> {config['recipients']}")
        return True
    except Exception as e:
        logger.error(f"邮件通知发送失败: {e}")
        return False