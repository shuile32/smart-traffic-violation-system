# app/api/v1/statistics.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.statistics import ByLocationOut, ByTimeOut, ByTypeOut, OverviewOut
from app.services.statistics_service import StatisticsService

router = APIRouter(tags=["statistics"])


@router.get("/statistics/overview", response_model=OverviewOut)
def overview(start_time: str | None = None, end_time: str | None = None,
             db: Session = Depends(get_db),
             _: User = Depends(require_role("reviewer", "admin"))) -> OverviewOut:
    return StatisticsService(db).overview(start_time, end_time)


@router.get("/statistics/by-location", response_model=ByLocationOut)
def by_location(start_time: str | None = None, end_time: str | None = None,
                limit: int = Query(10, ge=1, le=50),
                db: Session = Depends(get_db),
                _: User = Depends(require_role("reviewer", "admin"))) -> ByLocationOut:
    return StatisticsService(db).by_location(start_time, end_time, limit)


@router.get("/statistics/by-type", response_model=ByTypeOut)
def by_type(start_time: str | None = None, end_time: str | None = None,
            db: Session = Depends(get_db),
            _: User = Depends(require_role("reviewer", "admin"))) -> ByTypeOut:
    return StatisticsService(db).by_type(start_time, end_time)


@router.get("/statistics/by-time", response_model=ByTimeOut)
def by_time(start_time: str | None = None, end_time: str | None = None,
            db: Session = Depends(get_db),
            _: User = Depends(require_role("reviewer", "admin"))) -> ByTimeOut:
    return StatisticsService(db).by_time(start_time, end_time)
