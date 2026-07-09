from sqlalchemy.orm import Session

from app.models.violation import AuditLog


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_logs(self, *, page: int, page_size: int, action: str | None = None) -> dict:
        q = self.db.query(AuditLog)
        if action:
            q = q.filter(AuditLog.action == action)
        total = q.count()
        items = q.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
