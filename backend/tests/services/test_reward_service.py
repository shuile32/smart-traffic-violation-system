# tests/services/test_reward_service.py
from app.services.reward_service import RewardService


def test_grant_reward_creates_record(db):
    svc = RewardService(db)
    r = svc.grant_reward(citizen_id=1, case_id=1, violation_id=1, violation_type="超速")
    assert r.id is not None
    assert r.amount == 10  # REWARD_DEFAULT_AMOUNT
    assert r.status == "pending"
    assert "超速" in r.reason
