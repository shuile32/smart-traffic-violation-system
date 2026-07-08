"""LLM 初审结果 — append-only"""

from datetime import datetime
from sqlalchemy import String, Text, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIReviewResult(Base):
    __tablename__ = "ai_review_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True, nullable=False)
    review_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # text_llm / vision_llm(预留)
    conclusion: Mapped[str] = mapped_column(String(30), nullable=False)  # suggest_approve / need_review / suggest_reject
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_points: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    missing_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    prompt_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "case_id": self.case_id,
            "review_mode": self.review_mode,
            "conclusion": self.conclusion,
            "ai_confidence": self.ai_confidence,
            "reason": self.reason,
            "risk_points": json.loads(self.risk_points) if self.risk_points else [],
            "missing_evidence": json.loads(self.missing_evidence) if self.missing_evidence else [],
            "prompt_version": self.prompt_version,
        }
