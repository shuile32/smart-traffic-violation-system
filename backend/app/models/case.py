"""案件模型"""

from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    intake_event_id: Mapped[int] = mapped_column(ForeignKey("intake_events.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="uploaded", index=True, nullable=False)
    # uploaded / detecting / ai_reviewing / pending_human_review / approved / rejected / archived / notified
    plate_no: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 允许人工补录
    violation_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 人工确认后的违章类型
    ai_review_id: Mapped[int | None] = mapped_column(ForeignKey("ai_review_results.id"), nullable=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_opinion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    ai_failed: Mapped[bool] = mapped_column(default=False, nullable=False)  # AI 流程失败标记
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "case_no": self.case_no,
            "intake_event_id": self.intake_event_id,
            "status": self.status,
            "plate_no": self.plate_no,
            "violation_type": self.violation_type,
            "reviewer_id": self.reviewer_id,
            "review_opinion": self.review_opinion,
            "reject_reason": self.reject_reason,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "ai_failed": self.ai_failed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
