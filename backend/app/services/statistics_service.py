# app/services/statistics_service.py
from datetime import datetime, timezone

from sqlalchemy import case, extract, func
from sqlalchemy.orm import Session

from app.models.intake import Case, IntakeEvent
from app.models.violation import Violation
from app.schemas.statistics import (
    ByLocationItem, ByLocationOut, ByTimeItem, ByTimeOut,
    ByTypeItem, ByTypeOut, OverviewOut,
    RoadTimeHeatmapItem, RoadTimeHeatmapOut,
)

DEFAULT_START = datetime(2000, 1, 1, tzinfo=timezone.utc)
TIME_SLOTS = (
    (0, 2, "0-2"),
    (2, 4, "2-4"),
    (4, 6, "4-6"),
    (6, 7, "6-7"),
    (7, 9, "7-9"),
    (9, 11, "9-11"),
    (11, 13, "11-13"),
    (13, 17, "13-17"),
    (17, 19, "17-19"),
    (19, 21, "19-21"),
    (21, 24, "21-24"),
)


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
        case_base = self.db.query(Case).filter(Case.created_at.between(st, et))
        total_cases = case_base.count()
        total_violations = self.db.query(Violation).filter(Violation.created_at.between(st, et)).count()
        approved = case_base.filter(Case.status.in_(["approved", "notified", "archived"])).count()
        rejected = case_base.filter(Case.status == "rejected").count()
        pending = self.db.query(Case).filter(Case.status == "pending_human_review").count()
        approve_rate = round(approved / total_cases * 100, 1) if total_cases > 0 else 0.0
        reject_rate = round(rejected / total_cases * 100, 1) if total_cases > 0 else 0.0
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_new = self.db.query(Case).filter(Case.created_at >= today_start).count()
        return OverviewOut(
            total_cases=total_cases, total_violations=total_violations,
            approve_rate=approve_rate, reject_rate=reject_rate,
            pending_count=pending, today_new=today_new,
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
            items=[ByLocationItem(name=r[0], value=r[1]) for r in rows]
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
            ByTypeItem(name=r[0], value=r[1],
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

    def road_time_heatmap(
        self, start_time: str | None, end_time: str | None,
    ) -> RoadTimeHeatmapOut:
        st = _parse(start_time, DEFAULT_START)
        et = _end(end_time)
        hour_col = extract("hour", Violation.occurred_at)
        slot_col = case(
            *[
                (((hour_col >= start) & (hour_col < end)), label)
                for start, end, label in TIME_SLOTS
            ],
            else_=None,
        ).label("time_slot")
        rows = (
            self.db.query(
                Violation.location_text,
                slot_col,
                func.count(Violation.id),
            )
            .filter(
                Violation.created_at.between(st, et),
                Violation.location_text.isnot(None),
                func.trim(Violation.location_text) != "",
            )
            .group_by(Violation.location_text, slot_col)
            .all()
        )

        time_slots = [label for _, _, label in TIME_SLOTS]
        roads = sorted({row[0] for row in rows})
        counts = {(row[0], row[1]): row[2] for row in rows}
        items = [
            RoadTimeHeatmapItem(
                road=road,
                time_slot=time_slot,
                count=counts.get((road, time_slot), 0),
            )
            for road in roads
            for time_slot in time_slots
        ]
        return RoadTimeHeatmapOut(
            time_slots=time_slots,
            roads=roads,
            items=items,
        )
