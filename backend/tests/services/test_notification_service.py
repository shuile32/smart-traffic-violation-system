# tests/services/test_notification_service.py
from app.models.violation import Notification, NotificationTemplate, Violation
from app.services.notification_provider import FakeNotificationProvider
from app.services.notification_service import NotificationService


def _seed_template(db):
    db.add(NotificationTemplate(code="violation_notice", subject_template="违章通知:{violation_type}",
                                body_template="车牌{plate_no}于{occurred_at}在{location_text}{violation_type}，罚款{fine_amount}元扣{points}分。"))
    db.commit()


def test_send_with_owner_email_records_sent(db):
    _seed_template(db)
    v = Violation(violation_no="VIO1", case_id=1, plate_no="粤A12345", violation_type="超速",
                  fine_amount=200, points=6, location_text="路口A")
    db.add(v); db.commit()
    svc = NotificationService(db, FakeNotificationProvider())
    n = svc.send_violation_notification(v, "owner@e.com")
    assert n.status == "sent"
    assert n.recipient == "owner@e.com"
    assert "粤A12345" in n.content


def test_send_without_owner_email_records_failed(db):
    _seed_template(db)
    v = Violation(violation_no="VIO2", case_id=1, plate_no="粤B99999", violation_type="超速",
                  fine_amount=200, points=6)
    db.add(v); db.commit()
    svc = NotificationService(db, FakeNotificationProvider())
    n = svc.send_violation_notification(v, None)
    assert n.status == "failed"
    assert n.recipient is None
