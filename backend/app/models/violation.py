"""正式违章模型"""

from datetime import datetime
from sqlalchemy import String, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    violation_no: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), nullable=False)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    plate_no: Mapped[str] = mapped_column(String(20), nullable=False)
    violation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    fine_amount: Mapped[int] = mapped_column(default=0, nullable=False)
    points: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "violation_no": self.violation_no,
            "case_id": self.case_id,
            "vehicle_id": self.vehicle_id,
            "owner_id": self.owner_id,
            "plate_no": self.plate_no,
            "violation_type": self.violation_type,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "location_text": self.location_text,
            "fine_amount": self.fine_amount,
            "points": self.points,
            "status": self.status,
        }
