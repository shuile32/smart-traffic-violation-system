"""车辆模型"""

from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plate_no: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    vehicle_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    owner: Mapped["User | None"] = relationship("User", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plate_no": self.plate_no,
            "vehicle_type": self.vehicle_type,
            "brand": self.brand,
            "color": self.color,
            "owner_id": self.owner_id,
            "owner_name": self.owner.username if self.owner else None,
            "owner_email": self.owner.email if self.owner else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
