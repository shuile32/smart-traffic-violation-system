from app.schemas import statistics as statistics_schemas
from app.schemas.statistics import (
    ByLocationItem,
    ByLocationOut,
    ByTimeItem,
    ByTimeOut,
    ByTypeItem,
    ByTypeOut,
    OverviewOut,
)


def test_overview_out_construction():
    o = OverviewOut(
        total_cases=3, total_violations=1, approve_rate=33.3,
        reject_rate=33.3, pending_count=1,
    )
    assert o.total_cases == 3
    assert o.approve_rate == 33.3


def test_by_location_out():
    o = ByLocationOut(items=[ByLocationItem(name="路口A", value=2)])
    assert o.items[0].value == 2


def test_by_type_out():
    o = ByTypeOut(items=[ByTypeItem(name="超速", value=2, percentage=66.7)])
    assert o.items[0].percentage == 66.7


def test_by_time_out():
    o = ByTimeOut(items=[ByTimeItem(date="2026-07-08", count=2)])
    assert o.items[0].date == "2026-07-08"


def test_road_time_heatmap_out():
    item = statistics_schemas.RoadTimeHeatmapItem(
        road="路段A", time_slot="0-2", count=0,
    )
    out = statistics_schemas.RoadTimeHeatmapOut(
        time_slots=["0-2", "2-4"],
        roads=["路段A"],
        items=[item],
    )

    assert out.time_slots == ["0-2", "2-4"]
    assert out.roads == ["路段A"]
    assert out.items[0].count == 0
