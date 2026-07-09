# app/models/violation_rule.py
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ViolationRule(Base):
    __tablename__ = "violation_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    violation_type: Mapped[str] = mapped_column(String(32))  # 超速 / 占用专用车道
    rule_type: Mapped[str] = mapped_column(String(32))  # speed / special_lane
    params: Mapped[str | None] = mapped_column(String(512))  # JSON（speed_limit / lane_roi 等）
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
