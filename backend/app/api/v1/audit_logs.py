from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.audit_log import AuditLogListResponse, AuditLogOut
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/admin/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                    action: str | None = None,
                    db: Session = Depends(get_db),
                    _: User = Depends(require_role("admin"))) -> AuditLogListResponse:
    res = AuditLogService(db).list_logs(page=page, page_size=page_size, action=action)
    return AuditLogListResponse(
        items=[AuditLogOut.model_validate(r) for r in res["items"]],
        total=res["total"], page=res["page"], page_size=res["page_size"])
