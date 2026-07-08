"""邮件通知适配器 — 标准库 smtplib 同步发送（Celery 任务中同步调用）"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from loguru import logger

from app.core.config import settings
from app.ai.adapters.base import NotificationProvider, SendResult


class EmailSmtpProvider(NotificationProvider):
    def send(self, to_email: str, subject: str, html_body: str) -> SendResult:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if settings.SMTP_PORT == 587:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                    server.starttls()
                    if settings.SMTP_USER:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                    if settings.SMTP_USER:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())

            logger.info(f"邮件已发送: {to_email}, subject={subject}")
            return SendResult(success=True)
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email}, error={e}")
            return SendResult(success=False, error=str(e))


class LogNotificationProvider(NotificationProvider):
    """开发阶段兜底：打日志不真发"""

    def send(self, to_email: str, subject: str, html_body: str) -> SendResult:
        logger.info(f"[LOG NOTIFY] to={to_email}, subject={subject}")
        logger.debug(f"[LOG NOTIFY] body={html_body[:200]}...")
        return SendResult(success=True, provider_msg_id="log-mock")
