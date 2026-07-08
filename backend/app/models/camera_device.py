"""摄像头设备模型"""

from datetime import datetime
from sqlalchemy import String, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CameraDevice(Base):
    __tablename__ = "camera_devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[int] = mapped_column(default=1, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_name": self.device_name,
            "device_code": self.device_code,
            "location_text": self.location_text,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
