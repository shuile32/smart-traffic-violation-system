"""图片接入事件模型"""

from datetime import datetime
from sqlalchemy import String, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IntakeEvent(Base):
    __tablename__ = "intake_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # citizen / camera / admin
    source_id: Mapped[int | None] = mapped_column(nullable=True)  # 举报人/摄像头/管理员 ID
    location_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(nullable=False)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # 车速，供超速判定
    image_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256，防重复
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="uploaded", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "location_text": self.location_text,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "speed": self.speed,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
