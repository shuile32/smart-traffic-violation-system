from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.models.violation import AuditLog


class AnnouncementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, title: str, content: str, actor_id: int) -> Announcement:
        announcement = Announcement(
            title=title.strip(), content=content.strip(), created_by=actor_id
        )
        self.db.add(announcement)
        self.db.flush()
        self._audit(
            actor_id=actor_id,
            action="announcement_create",
            announcement=announcement,
        )
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def list_announcements(self, *, page: int, page_size: int) -> dict:
        query = self.db.query(Announcement)
        total = query.count()
        items = (
            query.order_by(Announcement.updated_at.desc(), Announcement.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get(self, announcement_id: int) -> Announcement:
        announcement = self.db.get(Announcement, announcement_id)
        if announcement is None:
            raise HTTPException(status_code=404, detail="公告不存在")
        return announcement

    def update(
        self,
        announcement_id: int,
        *,
        title: str | None,
        content: str | None,
        actor_id: int,
    ) -> Announcement:
        announcement = self.get(announcement_id)
        if title is not None:
            announcement.title = title.strip()
        if content is not None:
            announcement.content = content.strip()
        announcement.updated_at = datetime.now(timezone.utc)
        self._audit(
            actor_id=actor_id,
            action="announcement_update",
            announcement=announcement,
        )
        self.db.commit()
        self.db.refresh(announcement)
        return announcement

    def delete(self, announcement_id: int, *, actor_id: int) -> None:
        announcement = self.get(announcement_id)
        self._audit(
            actor_id=actor_id,
            action="announcement_delete",
            announcement=announcement,
        )
        self.db.delete(announcement)
        self.db.commit()

    def _audit(
        self, *, actor_id: int, action: str, announcement: Announcement
    ) -> None:
        self.db.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                target_type="announcement",
                target_id=announcement.id,
                detail=f"公告：{announcement.title}",
            )
        )
