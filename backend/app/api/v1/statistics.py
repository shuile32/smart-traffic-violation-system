"""统计分析路由 — 第一阶段：基础聚合接口，无前端图表"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import RequireReviewer
from app.models.case import Case
from app.models.violation import Violation
from schemas.common import APIResponse

router = APIRouter()


@router.get("/overview", response_model=APIResponse[dict])
async def get_overview(
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    st = datetime.fromisoformat(start_time) if start_time else datetime(2026, 1, 1)
    et = datetime.fromisoformat(end_time) if end_time else datetime.now()

    total = db.query(Case).filter(Case.created_at.between(st, et)).count()
    approved = db.query(Case).filter(Case.created_at.between(st, et), Case.status == "approved").count()
    rejected = db.query(Case).filter(Case.created_at.between(st, et), Case.status == "rejected").count()
    pending = db.query(Case).filter(Case.status == "pending_human_review").count()

    approval_rate = round(approved / total * 100, 1) if total > 0 else 0.0

    return APIResponse(data={
        "total_cases": total,
        "approved_count": approved,
        "rejected_count": rejected,
        "pending_count": pending,
        "approval_rate": approval_rate,
        "period": {"start": st.isoformat(), "end": et.isoformat()},
    })


@router.get("/by-location", response_model=APIResponse[dict])
async def get_by_location(
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    st = datetime.fromisoformat(start_time) if start_time else datetime(2026, 1, 1)
    et = datetime.fromisoformat(end_time) if end_time else datetime.now()

    from sqlalchemy import func as sa_func
    results = (
        db.query(Violation.location_text, sa_func.count(Violation.id).label("cnt"))
        .filter(Violation.created_at.between(st, et))
        .group_by(Violation.location_text)
        .order_by(sa_func.count(Violation.id).desc())
        .limit(limit)
        .all()
    )

    return APIResponse(data={"items": [{"location_text": r[0], "count": r[1]} for r in results]})


@router.get("/by-type", response_model=APIResponse[dict])
async def get_by_type(
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    st = datetime.fromisoformat(start_time) if start_time else datetime(2026, 1, 1)
    et = datetime.fromisoformat(end_time) if end_time else datetime.now()

    from sqlalchemy import func as sa_func
    total = db.query(Violation).filter(Violation.created_at.between(st, et)).count()
    results = (
        db.query(Violation.violation_type, sa_func.count(Violation.id).label("cnt"))
        .filter(Violation.created_at.between(st, et))
        .group_by(Violation.violation_type)
        .all()
    )

    return APIResponse(data={
        "items": [
            {"violation_type": r[0], "count": r[1], "percentage": round(r[1] / total * 100, 1) if total > 0 else 0}
            for r in results
        ],
    })


@router.get("/by-time", response_model=APIResponse[dict])
async def get_by_time(
    start_time: str | None = Query(None),
    end_time: str | None = Query(None),
    _: bool = Depends(RequireReviewer),
    db: Session = Depends(get_db),
):
    st = datetime.fromisoformat(start_time) if start_time else datetime(2026, 1, 1)
    et = datetime.fromisoformat(end_time) if end_time else datetime.now()

    from sqlalchemy import func as sa_func, cast, Date
    results = (
        db.query(cast(Violation.created_at, Date).label("date"), sa_func.count(Violation.id).label("cnt"))
        .filter(Violation.created_at.between(st, et))
        .group_by(cast(Violation.created_at, Date))
        .order_by(cast(Violation.created_at, Date))
        .all()
    )

    return APIResponse(data={
        "items": [{"date": str(r[0]), "count": r[1]} for r in results],
    })
