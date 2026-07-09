# app/services/statistics_service.py
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.intake import Case
from app.models.violation import Violation
from app.schemas.statistics import (
    ByLocationItem,
    ByLocationOut,
    ByTimeItem,
    ByTimeOut,
    ByTypeItem,
    ByTypeOut,
    OverviewOut,
    PeriodOut,
)

DEFAULT_START = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _parse(time_str: str | None, default: datetime) -> datetime:
    if time_str is None:
        return default
    dt = datetime.fromisoformat(time_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _end(end_time: str | None) -> datetime:
    return _parse(end_time, datetime.now(timezone.utc))


class StatisticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def overview(self, start_time: str | None, end_time: str | None) -> OverviewOut:
        st = _parse(start_time, DEFAULT_START)
        et = _end(end_time)
        base = self.db.query(Case).filter(Case.created_at.between(st, et))
        total = base.count()
        approved = base.filter(Case.status == "approved").count()
        rejected = base.filter(Case.status == "rejected").count()
        pending = self.db.query(Case).filter(Case.status == "pending_human_review").count()
        approval_rate = round(approved / total * 100, 1) if total > 0 else 0.0
        return OverviewOut(
            total_cases=total, approved_count=approved, rejected_count=rejected,
            pending_count=pending, approval_rate=approval_rate,
            period=PeriodOut(start=st.isoformat(), end=et.isoformat()),
        )

    def by_location(self, start_time: str | None, end_time: str | None, limit: int) -> ByLocationOut:
        st = _parse(start_time, DEFAULT_START)
        et = _end(end_time)
        rows = (
            self.db.query(Violation.location_text, func.count(Violation.id))
            .filter(Violation.created_at.between(st, et))
            .group_by(Violation.location_text)
            .order_by(func.count(Violation.id).desc())
            .limit(limit)
            .all()
        )
        return ByLocationOut(
            items=[ByLocationItem(location_text=r[0], count=r[1]) for r in rows]
        )

    def by_type(self, start_time: str | None, end_time: str | None) -> ByTypeOut:
        st = _parse(start_time, DEFAULT_START)
        et = _end(end_time)
        total = self.db.query(Violation).filter(Violation.created_at.between(st, et)).count()
        rows = (
            self.db.query(Violation.violation_type, func.count(Violation.id))
            .filter(Violation.created_at.between(st, et))
            .group_by(Violation.violation_type)
            .all()
        )
        return ByTypeOut(items=[
            ByTypeItem(violation_type=r[0], count=r[1],
                       percentage=round(r[1] / total * 100, 1) if total > 0 else 0.0)
            for r in rows
        ])

    def by_time(self, start_time: str | None, end_time: str | None) -> ByTimeOut:
        st = _parse(start_time, DEFAULT_START)
        et = _end(end_time)
        date_col = func.date(Violation.created_at)
        rows = (
            self.db.query(date_col, func.count(Violation.id))
            .filter(Violation.created_at.between(st, et))
            .group_by(date_col)
            .order_by(date_col)
            .all()
        )
        return ByTimeOut(items=[ByTimeItem(date=str(r[0]), count=r[1]) for r in rows])
