from datetime import datetime, timezone

from app.models.intake import Case, IntakeEvent
from app.models.violation import Violation
from app.services.statistics_service import StatisticsService

WIN = ("2000-01-01T00:00:00", "2099-01-01T00:00:00")  # 宽窗，覆盖所有种子


def _seed_case(db, *, status, created_at, case_no):
    ev = IntakeEvent(source_type="admin", image_hash="h" * 8)
    db.add(ev)
    db.flush()
    c = Case(case_no=case_no, intake_event_id=ev.id, status=status, created_at=created_at)
    db.add(c)
    db.commit()
    return c


def _seed_violation(
    db, *, case, violation_type, location_text, created_at, vio_no,
    occurred_at=None,
):
    v = Violation(
        violation_no=vio_no, case_id=case.id, plate_no="京A1", violation_type=violation_type,
        location_text=location_text, fine_amount=200, points=3, status="pending",
        occurred_at=occurred_at, created_at=created_at,
    )
    db.add(v)
    db.commit()
    return v


def test_overview_counts(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    _seed_case(db, status="approved", created_at=t, case_no="C1")
    _seed_case(db, status="rejected", created_at=t, case_no="C2")
    _seed_case(db, status="pending_human_review", created_at=t, case_no="C3")
    out = StatisticsService(db).overview(*WIN)
    assert out.total_cases == 3
    assert out.approve_rate == round(1 / 3 * 100, 1)
    assert out.reject_rate == round(1 / 3 * 100, 1)
    assert out.pending_count == 1


def test_by_location_orders_desc_and_limit(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口A", created_at=t, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口A", created_at=t, vio_no="V2")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口B", created_at=t, vio_no="V3")
    out = StatisticsService(db).by_location(*WIN, limit=10)
    assert out.items[0].name == "路口A"
    assert out.items[0].value == 2
    out_limit1 = StatisticsService(db).by_location(*WIN, limit=1)
    assert len(out_limit1.items) == 1


def test_by_type_percentage(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t, vio_no="V2")
    _seed_violation(db, case=c, violation_type="违停", location_text="A", created_at=t, vio_no="V3")
    out = StatisticsService(db).by_type(*WIN)
    assert len(out.items) == 2
    super_item = next(i for i in out.items if i.name == "超速")
    assert super_item.value == 2
    assert super_item.percentage == round(2 / 3 * 100, 1)


def test_by_time_daily_grouping(db):
    t1 = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 9, 11, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t1, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t1, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t1, vio_no="V2")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t2, vio_no="V3")
    out = StatisticsService(db).by_time(*WIN)
    assert len(out.items) == 2
    assert out.items[0].date == "2026-07-08"
    assert out.items[0].count == 2
    assert out.items[1].date == "2026-07-09"
    assert out.items[1].count == 1


def test_overview_time_window_excludes_outside(db):
    t1 = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc)
    _seed_case(db, status="approved", created_at=t1, case_no="C1")
    _seed_case(db, status="approved", created_at=t2, case_no="C2")
    out = StatisticsService(db).overview("2026-07-09T00:00:00", "2026-07-11T00:00:00")
    assert out.total_cases == 1


def test_by_type_time_window_excludes_outside(db):
    t1 = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t1, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t1, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t2, vio_no="V2")
    out = StatisticsService(db).by_type("2026-07-09T00:00:00", "2026-07-11T00:00:00")
    assert len(out.items) == 1
    assert out.items[0].value == 1


def test_road_time_heatmap_uses_slot_boundaries_and_fills_zeroes(db):
    day = datetime(2026, 7, 8, tzinfo=timezone.utc)
    case = _seed_case(db, status="approved", created_at=day, case_no="C1")
    hours = [0, 2, 4, 6, 7, 9, 11, 13, 17, 19, 21, 23]
    for index, hour in enumerate(hours, start=1):
        occurred_at = day.replace(hour=hour, minute=59 if hour == 23 else 0)
        _seed_violation(
            db, case=case, violation_type="超速", location_text="路段A",
            occurred_at=occurred_at, created_at=day, vio_no=f"H{index}",
        )

    out = StatisticsService(db).road_time_heatmap(*WIN)

    assert out.time_slots == [
        "0-2", "2-4", "4-6", "6-7", "7-9", "9-11",
        "11-13", "13-17", "17-19", "19-21", "21-24",
    ]
    assert out.roads == ["路段A"]
    assert [item.time_slot for item in out.items] == out.time_slots
    assert [item.count for item in out.items] == [1] * 10 + [2]


def test_road_time_heatmap_orders_roads_and_items(db):
    day = datetime(2026, 7, 8, tzinfo=timezone.utc)
    case = _seed_case(db, status="approved", created_at=day, case_no="C1")
    for vio_no, road, hour in [("V1", "路段B", 8), ("V2", "路段A", 18), ("V3", "路段A", 18)]:
        _seed_violation(
            db, case=case, violation_type="超速", location_text=road,
            occurred_at=day.replace(hour=hour), created_at=day, vio_no=vio_no,
        )

    out = StatisticsService(db).road_time_heatmap(*WIN)

    assert out.roads == ["路段A", "路段B"]
    assert len(out.items) == 22
    assert [item.road for item in out.items[:11]] == ["路段A"] * 11
    counts = {(item.road, item.time_slot): item.count for item in out.items}
    assert counts[("路段A", "17-19")] == 2
    assert counts[("路段B", "7-9")] == 1
    assert counts[("路段A", "0-2")] == 0


def test_road_time_heatmap_filters_window_and_invalid_dimensions(db):
    day = datetime(2026, 7, 8, tzinfo=timezone.utc)
    case = _seed_case(db, status="approved", created_at=day, case_no="C1")
    rows = [
        ("V1", "路段A", day.replace(hour=8)),
        ("V2", "路段A", day.replace(day=9, hour=8)),
        ("V3", "路段A", None),
        ("V4", None, day.replace(hour=8)),
        ("V5", "", day.replace(hour=8)),
        ("V6", "   ", day.replace(hour=8)),
    ]
    for vio_no, road, occurred_at in rows:
        _seed_violation(
            db, case=case, violation_type="超速", location_text=road,
            occurred_at=occurred_at, created_at=day, vio_no=vio_no,
        )

    out = StatisticsService(db).road_time_heatmap(
        "2026-07-08T00:00:00", "2026-07-08T23:59:59",
    )

    assert out.roads == ["路段A"]
    assert sum(item.count for item in out.items) == 2
    assert next(item for item in out.items if item.time_slot == "7-9").count == 2

    empty = StatisticsService(db).road_time_heatmap(
        "2030-01-01T00:00:00", "2030-01-02T00:00:00",
    )
    assert empty.roads == []
    assert empty.items == []
    assert len(empty.time_slots) == 11


def test_road_time_heatmap_filters_created_at_and_buckets_occurred_at(db):
    inside = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    outside = datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    case = _seed_case(db, status="approved", created_at=inside, case_no="C-CREATED")
    _seed_violation(
        db, case=case, violation_type="超速", location_text="创建期内道路",
        created_at=inside, occurred_at=outside.replace(hour=18), vio_no="CREATED-IN",
    )
    _seed_violation(
        db, case=case, violation_type="超速", location_text="发生期内道路",
        created_at=outside, occurred_at=inside.replace(hour=8), vio_no="OCCURRED-IN",
    )

    out = StatisticsService(db).road_time_heatmap(
        "2026-07-08T00:00:00", "2026-07-08T23:59:59",
    )

    assert out.roads == ["创建期内道路"]
    assert sum(item.count for item in out.items) == 1
    assert next(item for item in out.items if item.time_slot == "17-19").count == 1
