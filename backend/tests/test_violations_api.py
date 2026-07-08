"""violations 路由测试：list / get / owner 违章查询的越权校验。"""
from datetime import datetime

from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.violation import Violation


def _seed_violation(db_session, plate="京A12345", vtype="违停", owner_id=None):
    intake = IntakeEvent(
        source_type="admin", source_id=1,
        captured_at=datetime(2026, 7, 8, 10, 0, 0),
        image_hash="h" * 64, status="uploaded",
    )
    db_session.add(intake)
    db_session.flush()
    case = Case(case_no=f"CASE{plate}", intake_event_id=intake.id, status="approved")
    db_session.add(case)
    db_session.flush()
    v = Violation(
        violation_no=f"VIO{plate}", case_id=case.id,
        plate_no=plate, violation_type=vtype,
        occurred_at=datetime(2026, 7, 8, 10, 0, 0),
        owner_id=owner_id, fine_amount=200, points=3, status="pending",
    )
    db_session.add(v)
    db_session.commit()
    return v


def test_list_violations_filter_by_type(client, make_user, auth_header, db_session):
    _seed_violation(db_session, plate="京A111", vtype="违停")
    _seed_violation(db_session, plate="京B222", vtype="超速")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/violations?violation_type=超速",
                      headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 1


def test_list_violations_filter_by_plate(client, make_user, auth_header, db_session):
    _seed_violation(db_session, plate="京A111")
    _seed_violation(db_session, plate="京B222")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/violations?plate_no=京A",
                      headers=auth_header("reviewer", u.id))
    assert resp.json()["data"]["total"] == 1


def test_get_violation_404(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/violations/9999",
                      headers=auth_header("reviewer", u.id))
    assert resp.status_code == 404


def test_owner_violations_self_ok(client, make_user, auth_header, db_session):
    u = make_user(role="citizen")
    _seed_violation(db_session, owner_id=u.id)
    resp = client.get(f"/api/v1/violations/owners/{u.id}/violations",
                      headers=auth_header("citizen", u.id))
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 1


def test_owner_violations_other_forbidden(client, make_user, auth_header):
    u = make_user(role="citizen")
    other = make_user(role="citizen")
    resp = client.get(f"/api/v1/violations/owners/{other.id}/violations",
                      headers=auth_header("citizen", u.id))
    assert resp.status_code == 403


def test_owner_violations_admin_can_view_other(client, make_user, auth_header, db_session):
    other = make_user(role="citizen")
    _seed_violation(db_session, owner_id=other.id)
    admin = make_user(role="admin")
    resp = client.get(f"/api/v1/violations/owners/{other.id}/violations",
                      headers=auth_header("admin", admin.id))
    assert resp.status_code == 200
