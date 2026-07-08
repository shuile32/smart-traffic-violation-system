"""cases 路由测试：list / get / approve / reject / request-recheck。"""
from datetime import datetime, timezone

from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.media_asset import MediaAsset


def _seed_case(db_session, status="pending_human_review", case_no="CASE001"):
    intake = IntakeEvent(
        source_type="admin", source_id=1,
        captured_at=datetime(2026, 7, 8, 10, 0, 0),
        image_hash="h" * 64, status="uploaded",
    )
    db_session.add(intake)
    db_session.flush()
    media = MediaAsset(
        intake_event_id=intake.id, asset_type="original",
        url="/media/x.jpg", mime_type="image/jpeg", size=10,
    )
    db_session.add(media)
    db_session.flush()
    case = Case(case_no=case_no, intake_event_id=intake.id, status=status)
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def test_list_cases_no_token_returns_401(client):
    assert client.get("/api/v1/cases").status_code == 401


def test_list_cases_citizen_forbidden(client, make_user, auth_header):
    u = make_user(role="citizen")
    resp = client.get("/api/v1/cases", headers=auth_header("citizen", u.id))
    assert resp.status_code == 403


def test_list_cases_reviewer_ok(client, make_user, auth_header, db_session):
    _seed_case(db_session)
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/cases", headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 1


def test_list_cases_filter_by_status(client, make_user, auth_header, db_session):
    _seed_case(db_session, status="approved", case_no="CASE001")
    _seed_case(db_session, status="pending_human_review", case_no="CASE002")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/cases?status=approved",
                      headers=auth_header("reviewer", u.id))
    assert resp.json()["data"]["total"] == 1


def test_get_case_404(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/cases/9999", headers=auth_header("reviewer", u.id))
    assert resp.status_code == 404


def test_approve_wrong_state_returns_400(client, make_user, auth_header, db_session):
    c = _seed_case(db_session, status="uploaded")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/approve",
                       json={"plate_no": "京A12345", "violation_type": "违停"},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 400


def test_approve_success_creates_violation_and_audit(client, make_user, auth_header,
                                                    db_session, celery_calls):
    c = _seed_case(db_session, status="pending_human_review")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/approve",
                       json={"plate_no": "京A12345", "violation_type": "违停",
                             "fine_amount": 200, "points": 3},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    from app.models.violation import Violation
    from app.models.audit_log import AuditLog
    assert db_session.query(Violation).count() == 1
    assert db_session.query(AuditLog).filter_by(action="case:approve").count() == 1
    db_session.refresh(c)
    assert c.status == "archived"


def test_reject_success(client, make_user, auth_header, db_session):
    c = _seed_case(db_session, status="pending_human_review")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/reject",
                       json={"reject_reason": "证据不足"},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    db_session.refresh(c)
    assert c.status == "rejected"


def test_request_recheck_success(client, make_user, auth_header, db_session, celery_calls):
    c = _seed_case(db_session, status="pending_human_review")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/request-recheck",
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    db_session.refresh(c)
    assert c.status == "detecting"
    assert any(call[0] == "delay" for call in celery_calls)
