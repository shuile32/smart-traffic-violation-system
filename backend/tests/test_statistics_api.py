"""statistics 路由测试：overview / by-location / by-type / by-time。"""
from datetime import datetime

from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.violation import Violation

WIN = {"start_time": "2026-01-01T00:00:00", "end_time": "2026-12-31T23:59:59"}


def _seed(db_session, case_status="approved", vtype="违停", location="路口A",
          created=datetime(2026, 7, 8, 10, 0, 0)):
    intake = IntakeEvent(
        source_type="admin", source_id=1,
        captured_at=datetime(2026, 7, 8, 10, 0, 0),
        image_hash="h" * 64, status="uploaded",
    )
    db_session.add(intake)
    db_session.flush()
    case = Case(case_no=f"C{vtype}{location}", intake_event_id=intake.id,
                status=case_status, created_at=created)
    db_session.add(case)
    db_session.flush()
    v = Violation(
        violation_no=f"V{vtype}{location}", case_id=case.id,
        plate_no="京A1", violation_type=vtype,
        occurred_at=datetime(2026, 7, 8, 10, 0, 0),
        location_text=location, fine_amount=200, points=3,
        status="pending", created_at=created,
    )
    db_session.add(v)
    db_session.commit()
    return v


def test_overview_no_token_returns_401(client):
    assert client.get("/api/v1/statistics/overview", params=WIN).status_code == 401


def test_overview_counts(client, make_user, auth_header, db_session):
    _seed(db_session, case_status="approved")
    _seed(db_session, case_status="rejected", location="路口B")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["total_cases"] == 2
    assert d["approved_count"] == 1
    assert d["rejected_count"] == 1


def test_by_location_orders_by_count_desc(client, make_user, auth_header, db_session):
    _seed(db_session, location="路口A")
    _seed(db_session, location="路口A", vtype="超速")
    _seed(db_session, location="路口B")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/by-location",
                      headers=auth_header("reviewer", u.id), params=WIN)
    items = resp.json()["data"]["items"]
    assert items[0]["location_text"] == "路口A"
    assert items[0]["count"] == 2


def test_by_type_returns_all_types(client, make_user, auth_header, db_session):
    _seed(db_session, vtype="违停")
    _seed(db_session, vtype="超速", location="路口B")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/by-type",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 2


def test_by_time_returns_daily_bucket(client, make_user, auth_header, db_session):
    _seed(db_session, created=datetime(2026, 7, 8, 10, 0, 0))
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/by-time",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 1
    assert any(i["count"] == 1 for i in items)
