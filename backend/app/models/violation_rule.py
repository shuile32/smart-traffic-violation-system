"""违章规则配置 — 上游方案细化版：rule_type + params JSON"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ViolationRule(Base):
    __tablename__ = "violation_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # SPD-001 / LANE-001
    violation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 超速 / 占用专用车道
    rule_type: Mapped[str] = mapped_column(String(30), nullable=False)  # speed / special_lane
    params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON，按 rule_type 不同
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "violation_type": self.violation_type,
            "rule_type": self.rule_type,
            "params": self.params,
            "description": self.description,
            "is_active": self.is_active,
        }
