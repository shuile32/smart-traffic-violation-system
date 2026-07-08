"""通知记录模型 — channel 通用化为 email（预留 sms/inapp）"""

from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    violation_id: Mapped[int] = mapped_column(ForeignKey("violations.id"), index=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="email", nullable=False)  # email / sms(预留) / inapp(预留)
    recipient: Mapped[str] = mapped_column(String(100), nullable=False)  # 邮箱地址
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending / sent / failed
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    provider_msg_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "violation_id": self.violation_id,
            "owner_id": self.owner_id,
            "channel": self.channel,
            "recipient": self.recipient,
            "status": self.status,
            "retry_count": self.retry_count,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
