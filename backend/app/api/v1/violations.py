"""违章查询路由"""

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import RequireReviewer
from app.models.violation import Violation
from schemas.common import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse[dict])
async def list_violations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plate_no: str | None = None,
    violation_type: str | None = None,
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    query = db.query(Violation)
    if plate_no:
        query = query.filter(Violation.plate_no.ilike(f"%{plate_no}%"))
    if violation_type:
        query = query.filter(Violation.violation_type == violation_type)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items = query.order_by(Violation.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return APIResponse(data={
        "items": [v.to_dict() for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


@router.get("/{violation_id}", response_model=APIResponse[dict])
async def get_violation(
    violation_id: int,
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    v = db.query(Violation).filter(Violation.id == violation_id).first()
    if not v:
        from fastapi import HTTPException
        raise HTTPException(404, detail="违章记录不存在")
    return APIResponse(data=v.to_dict())


@router.get("/owners/{owner_id}/violations", response_model=APIResponse[dict])
async def get_owner_violations(
    owner_id: int,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 市民只能看自己的
    if payload.get("role") == "citizen" and int(payload["sub"]) != owner_id:
        from fastapi import HTTPException
        raise HTTPException(403, detail="无权查看他人违章")

    violations = (
        db.query(Violation)
        .filter(Violation.owner_id == owner_id)
        .order_by(Violation.created_at.desc())
        .all()
    )
    return APIResponse(data={"items": [v.to_dict() for v in violations]})
