"""规则判定结果 — append-only"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ViolationRuleResult(Base):
    __tablename__ = "violation_rule_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True, nullable=False)
    candidate_violation_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rule_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rule_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_level: Mapped[str] = mapped_column(String(20), nullable=False)  # complete / partial / insufficient
    evidence_items: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    missing_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "case_id": self.case_id,
            "candidate_violation_type": self.candidate_violation_type,
            "rule_code": self.rule_code,
            "rule_matched": self.rule_matched,
            "evidence_level": self.evidence_level,
            "evidence_items": json.loads(self.evidence_items) if self.evidence_items else [],
            "missing_evidence": json.loads(self.missing_evidence) if self.missing_evidence else [],
            "reason": self.reason,
        }
