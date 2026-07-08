"""YOLOv8 检测结果 — append-only"""

from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AIDetectionResult(Base):
    __tablename__ = "ai_detection_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(20), nullable=False)
    detected_objects: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    object_confidences: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    plate_bbox: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    vehicle_bbox: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    raw_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    annotated_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "case_id": self.case_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "detected_objects": json.loads(self.detected_objects) if self.detected_objects else [],
            "plate_bbox": json.loads(self.plate_bbox) if self.plate_bbox else None,
            "vehicle_bbox": json.loads(self.vehicle_bbox) if self.vehicle_bbox else None,
            "annotated_image_url": self.annotated_image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
