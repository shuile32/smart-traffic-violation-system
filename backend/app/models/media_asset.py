"""媒体文件模型"""

from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    intake_event_id: Mapped[int] = mapped_column(ForeignKey("intake_events.id"), index=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False)  # original / annotated / cropped_plate
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "intake_event_id": self.intake_event_id,
            "asset_type": self.asset_type,
            "url": self.url,
            "mime_type": self.mime_type,
            "size": self.size,
        }
