# app/services/reward_service.py
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.violation import Reward


class RewardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def grant_reward(self, *, citizen_id: int, case_id: int, violation_id: int, violation_type: str) -> Reward:
        reward = Reward(
            citizen_id=citizen_id, case_id=case_id, violation_id=violation_id,
            amount=settings.REWARD_DEFAULT_AMOUNT,
            reason=f"举报{violation_type}成立",
            status="pending",
        )
        self.db.add(reward)
        self.db.flush()
        self.db.commit()
        self.db.refresh(reward)
        return reward
