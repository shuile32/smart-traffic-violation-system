"""通知模板（原 sms_templates 通用化）"""

from datetime import datetime
from sqlalchemy import String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # violation_notify
    template_name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="email", nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "template_code": self.template_code,
            "template_name": self.template_name,
            "channel": self.channel,
            "subject": self.subject,
            "body_html": self.body_html,
            "variables": self.variables,
            "is_active": self.is_active,
        }
