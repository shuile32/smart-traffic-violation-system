"""Celery 任务：发送通知（邮件）"""

from datetime import datetime, timezone

from celery import shared_task
from loguru import logger

from app.core.database import SessionLocal
from app.models.violation import Violation
from app.models.notification import Notification
from app.models.notification_template import NotificationTemplate
from app.models.user import User
from app.ai.adapters.email_smtp import EmailSmtpProvider, LogNotificationProvider
from jinja2 import Template


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_notification_task(self, violation_id: int):
    db = SessionLocal()
    try:
        violation = db.query(Violation).filter(Violation.id == violation_id).first()
        if not violation:
            return {"error": "violation not found"}

        # 获取车主邮箱
        owner = db.query(User).filter(User.id == violation.owner_id).first()
        if not owner or not owner.email:
            logger.warning(f"车主无邮箱: owner_id={violation.owner_id}")
            return {"error": "owner has no email"}

        # 获取通知模板
        template = (
            db.query(NotificationTemplate)
            .filter(NotificationTemplate.template_code == "violation_notify", NotificationTemplate.is_active == True)
            .first()
        )

        if template:
            subject = Template(template.subject).render(plate_no=violation.plate_no)
            body = Template(template.body_html).render(
                plate_no=violation.plate_no,
                violation_type=violation.violation_type,
                occurred_at=violation.occurred_at.strftime("%Y-%m-%d %H:%M") if violation.occurred_at else "",
                location_text=violation.location_text or "",
                fine_amount=violation.fine_amount,
                points=violation.points,
            )
        else:
            subject = f"交通违章通知: {violation.plate_no}"
            body = f"<p>车牌号 {violation.plate_no} 有一条新的违章记录，请登录系统查看详情。</p>"

        # 尝试真实 SMTP，失败则兜底
        try:
            provider = EmailSmtpProvider()
            result = provider.send(owner.email, subject, body)
        except Exception:
            provider = LogNotificationProvider()
            result = provider.send(owner.email, subject, body)

        # 记录通知
        notification = Notification(
            violation_id=violation_id,
            owner_id=violation.owner_id,
            channel="email",
            recipient=owner.email,
            content=subject,
            status="sent" if result.success else "failed",
            provider="smtp" if result.success else "log",
            provider_msg_id=result.provider_msg_id,
            sent_at=datetime.now(timezone.utc) if result.success else None,
        )
        db.add(notification)
        db.commit()

        logger.info(f"通知发送完成: violation_id={violation_id}, status={notification.status}")
        return {"notification_id": notification.id, "status": notification.status}

    except Exception as exc:
        logger.error(f"通知发送失败: violation_id={violation_id}, error={exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()
