# app/api/v1/roles.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import Role, User

router = APIRouter(prefix="/admin/roles", tags=["roles"])


@router.get("")
def list_roles(db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> list[dict]:
    roles = db.query(Role).all()
    return [{"id": r.id, "code": r.code, "name": r.name} for r in roles]
