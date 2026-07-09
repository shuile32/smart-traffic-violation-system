# tests/services/test_violation_service.py
import pytest

from app.models.intake import IntakeEvent
from app.models.user import Role, User
from app.models.violation import Vehicle, Violation
from app.services.violation_service import ViolationService, get_owner_email


def _make_case(db):
    role = Role(code="citizen", name="市民"); db.add(role); db.commit()
    u = User(username="c1", password_hash="h", email="c@e.com", role_id=role.id); db.add(u); db.commit()
    ev = IntakeEvent(source_type="citizen", source_id=u.id, image_hash="h1"); db.add(ev); db.commit()
    from app.models.intake import Case
    case = Case(case_no="CASE1", intake_event_id=ev.id, status="pending_human_review")
    db.add(case); db.commit()
    return case, u


def test_create_violation_with_vehicle_links_owner(db):
    case, owner = _make_case(db)
    veh = Vehicle(plate_no="粤A12345", owner_id=owner.id, vehicle_type="小汽车"); db.add(veh); db.commit()
    svc = ViolationService(db)
    v = svc.create_violation(case, plate_no="粤A12345", violation_type="超速", fine_amount=200, points=6)
    assert v.violation_no.startswith("VIO")
    assert v.vehicle_id == veh.id
    assert v.owner_id == owner.id
    assert get_owner_email(db, v) == "c@e.com"


def test_create_violation_no_vehicle(db):
    case, _ = _make_case(db)
    svc = ViolationService(db)
    v = svc.create_violation(case, plate_no="粤X00000", violation_type="超速", fine_amount=200, points=6)
    assert v.vehicle_id is None
    assert v.owner_id is None
    assert get_owner_email(db, v) is None
