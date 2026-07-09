# 张浩-5 统计分析 API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 upstream d175700 基线上实现 spec §6.1 的 4 个 `/api/v1/statistics/*` 路由（overview/by-location/by-type/by-time），照杨翼 route→service→schemas 模式，强类型 Pydantic 响应、`require_role("reviewer","admin")` 鉴权、TDD。

**Architecture:** `app/schemas/statistics.py`（Pydantic Out）→ `app/services/statistics_service.py`（StatisticsService 聚合查询）→ `app/api/v1/statistics.py`（4 路由，调 service）→ `router.py` 挂载。overview 查 Case，其余查 Violation。

**Tech Stack:** FastAPI、SQLAlchemy 2.0（func.count/group_by/cast Date）、Pydantic v2、pytest + TestClient（SQLite 内存，复用 conftest）。

**分支：** `zhanghao/statistics`（off main `d175700`，基线 62 passed）。跑测试：`cd backend && python -m pytest ...`。

**已确认事实（写代码直接用）：**
- 鉴权：`from app.core.deps import require_role`；`_: User = Depends(require_role("reviewer","admin"))`。无 token→401、citizen→403。
- conftest fixtures：`client`/`db`/`seeded_roles`/`citizen_user`/`auth_headers`(citizen)/`reviewer_user`/`reviewer_auth_headers`。
- `Violation`（`app/models/violation.py`）：violation_no/case_id/plate_no/violation_type/location_text/fine_amount/points/status/created_at（tz-aware）。
- `Case`（`app/models/intake.py`）：case_no/intake_event_id/status/created_at（tz-aware）。`IntakeEvent`：source_type/image_hash 必填，captured_at 可空。
- 杨翼 router.py 风格：`api_router.include_router(xxx.router)`，路由用 `APIRouter(tags=[...])`，prefix 在 api_router 上（`/api/v1`），路由内 path 写 `/statistics/...`。

---

## Task 1: Schemas（`app/schemas/statistics.py`）

**Files:**
- Create: `backend/app/schemas/statistics.py`
- Test: `backend/tests/test_schemas_statistics.py`

- [ ] **Step 1: 写测试 `tests/test_schemas_statistics.py`**

```python
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


def test_overview_out_construction():
    o = OverviewOut(
        total_cases=3, approved_count=1, rejected_count=1, pending_count=1,
        approval_rate=33.3, period=PeriodOut(start="s", end="e"),
    )
    assert o.total_cases == 3
    assert o.period.start == "s"


def test_by_location_out():
    o = ByLocationOut(items=[ByLocationItem(location_text="路口A", count=2)])
    assert o.items[0].count == 2


def test_by_type_out():
    o = ByTypeOut(items=[ByTypeItem(violation_type="超速", count=2, percentage=66.7)])
    assert o.items[0].percentage == 66.7


def test_by_time_out():
    o = ByTimeOut(items=[ByTimeItem(date="2026-07-08", count=2)])
    assert o.items[0].date == "2026-07-08"
```

- [ ] **Step 2: 跑，确认 FAIL**

Run: `cd backend && python -m pytest tests/test_schemas_statistics.py -v`
Expected: FAIL — `ModuleNotFoundError: app.schemas.statistics`

- [ ] **Step 3: 写 `app/schemas/statistics.py`**

```python
from pydantic import BaseModel


class PeriodOut(BaseModel):
    start: str | None
    end: str | None


class OverviewOut(BaseModel):
    total_cases: int
    approved_count: int
    rejected_count: int
    pending_count: int
    approval_rate: float
    period: PeriodOut


class ByLocationItem(BaseModel):
    location_text: str | None
    count: int


class ByLocationOut(BaseModel):
    items: list[ByLocationItem]


class ByTypeItem(BaseModel):
    violation_type: str
    count: int
    percentage: float


class ByTypeOut(BaseModel):
    items: list[ByTypeItem]


class ByTimeItem(BaseModel):
    date: str
    count: int


class ByTimeOut(BaseModel):
    items: list[ByTimeItem]
```

- [ ] **Step 4: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/test_schemas_statistics.py -v`
Expected: 4 passed。

- [ ] **Step 5: 提交**

```bash
git add backend/app/schemas/statistics.py backend/tests/test_schemas_statistics.py
git commit -m "feat(statistics): Pydantic 响应 schema"
```

---

## Task 2: StatisticsService + service 测试（TDD）

**Files:**
- Create: `backend/app/services/statistics_service.py`
- Test: `backend/tests/services/test_statistics_service.py`

- [ ] **Step 1: 写测试 `tests/services/test_statistics_service.py`**

```python
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


def _seed_violation(db, *, case, violation_type, location_text, created_at, vio_no):
    v = Violation(
        violation_no=vio_no, case_id=case.id, plate_no="京A1", violation_type=violation_type,
        location_text=location_text, fine_amount=200, points=3, status="pending",
        created_at=created_at,
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
    assert out.approved_count == 1
    assert out.rejected_count == 1
    assert out.pending_count == 1
    assert out.approval_rate == round(1 / 3 * 100, 1)


def test_by_location_orders_desc_and_limit(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口A", created_at=t, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口A", created_at=t, vio_no="V2")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口B", created_at=t, vio_no="V3")
    out = StatisticsService(db).by_location(*WIN, limit=10)
    assert out.items[0].location_text == "路口A"
    assert out.items[0].count == 2
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
    super_item = next(i for i in out.items if i.violation_type == "超速")
    assert super_item.count == 2
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
```

- [ ] **Step 2: 跑，确认 FAIL**

Run: `cd backend && python -m pytest tests/services/test_statistics_service.py -v`
Expected: FAIL — `ModuleNotFoundError: app.services.statistics_service`

- [ ] **Step 3: 写 `app/services/statistics_service.py`**

```python
# app/services/statistics_service.py
from datetime import datetime, timezone

from sqlalchemy import Date, cast, func
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
        date_col = cast(Violation.created_at, Date)
        rows = (
            self.db.query(date_col, func.count(Violation.id))
            .filter(Violation.created_at.between(st, et))
            .group_by(date_col)
            .order_by(date_col)
            .all()
        )
        return ByTimeOut(items=[ByTimeItem(date=str(r[0]), count=r[1]) for r in rows])
```

- [ ] **Step 4: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/services/test_statistics_service.py -v`
Expected: 4 passed。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/statistics_service.py backend/tests/services/test_statistics_service.py
git commit -m "feat(statistics): StatisticsService 聚合查询 + 测试"
```

---

## Task 3: 路由 + router 挂载 + API 测试（TDD）

**Files:**
- Create: `backend/app/api/v1/statistics.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/api/test_statistics_api.py`

- [ ] **Step 1: 写测试 `tests/api/test_statistics_api.py`**

```python
from datetime import datetime, timezone

from app.models.intake import Case, IntakeEvent
from app.models.violation import Violation


def _seed(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    ev = IntakeEvent(source_type="admin", image_hash="h" * 8)
    db.add(ev)
    db.flush()
    for no, st in [("C1", "approved"), ("C2", "rejected"), ("C3", "pending_human_review")]:
        db.add(Case(case_no=no, intake_event_id=ev.id, status=st, created_at=t))
    db.flush()
    c1 = db.query(Case).filter_by(case_no="C1").first()
    db.add(Violation(
        violation_no="V1", case_id=c1.id, plate_no="京A", violation_type="超速",
        location_text="路口A", fine_amount=200, points=3, status="pending", created_at=t,
    ))
    db.commit()


def test_overview_requires_auth(client):
    assert client.get("/api/v1/statistics/overview").status_code == 401


def test_overview_citizen_forbidden(client, citizen_user, auth_headers):
    assert client.get("/api/v1/statistics/overview", headers=auth_headers).status_code == 403


def test_overview_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/overview", headers=reviewer_auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_cases"] == 3
    assert data["approved_count"] == 1
    assert "period" in data


def test_by_location_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/by-location", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json()["items"], list)


def test_by_type_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/by-type", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


def test_by_time_success(client, reviewer_user, reviewer_auth_headers, db):
    _seed(db)
    r = client.get("/api/v1/statistics/by-time", headers=reviewer_auth_headers)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


def test_by_location_requires_auth(client):
    assert client.get("/api/v1/statistics/by-location").status_code == 401
```

- [ ] **Step 2: 跑，确认 FAIL（路由未挂载，404）**

Run: `cd backend && python -m pytest tests/api/test_statistics_api.py -v`
Expected: FAIL（404）。

- [ ] **Step 3: 写 `app/api/v1/statistics.py`**

```python
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
```

- [ ] **Step 4: 改 `app/api/v1/router.py`，挂载 statistics.router**

先 Read 该文件。把 `from app.api.v1 import auth, cases, intakes, violations` 改为：
```python
from app.api.v1 import auth, cases, intakes, statistics, violations
```
在 `api_router.include_router(violations.router)` 之后追加：
```python
api_router.include_router(statistics.router)
```

- [ ] **Step 5: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/api/test_statistics_api.py -v`
Expected: 7 passed。

- [ ] **Step 6: 提交**

```bash
git add backend/app/api/v1/statistics.py backend/app/api/v1/router.py backend/tests/api/test_statistics_api.py
git commit -m "feat(statistics): /api/v1/statistics 4 路由 + 挂载"
```

---

## Task 4: 全量回归 + 自检

- [ ] **Step 1: 全量跑**

Run: `cd backend && python -m pytest -v`
Expected: 全绿。数量 = 62（基线）+ 4（schemas）+ 4（service）+ 7（api）= 77 passed。

- [ ] **Step 2: 自检清单**

- [ ] 4 个 `/api/v1/statistics/*` 路由可用，强类型响应（`response_model`）。
- [ ] 全部 `require_role("reviewer","admin")`；无 token→401、citizen→403、reviewer→200。
- [ ] overview 查 Case（total/approved/rejected/pending/approval_rate/period），其余查 Violation。
- [ ] 未动杨翼代码：`git diff main -- backend/app/api/v1/violations.py backend/app/api/v1/cases.py backend/app/services/violation_service.py backend/app/services/case_service.py backend/app/services/review_service.py` 应为空。

- [ ] **Step 3: 若有零散改动，收尾提交**

```bash
git add -A
git commit -m "test(statistics): 全量回归通过"
```
（若无改动则跳过。）

---

## 自检（计划层面）

- **Spec 覆盖**：§6.1 的 4 路由（Task 3）✅；overview 查 Case（Task 2/3）✅；by-location/by-type/by-time 查 Violation（Task 2/3）✅；强类型 Pydantic 响应（Task 1 schemas）✅；service 层（Task 2）✅；鉴权 require_role（Task 3）✅；测试（Task 1/2/3）✅。不做前端图表/by-week-month（§不做）✅。
- **占位符**：无 TBD/TODO，每步有完整代码。
- **类型一致**：`OverviewOut`/`ByLocationOut`/`ByTypeOut`/`ByTimeOut` 字段在 schemas（Task1）、service（Task2）、routes（Task3）一致；`StatisticsService.overview/by_location/by_type/by_time` 签名在 service（Task2）与 routes（Task3）调用一致；conftest fixture 名 `reviewer_auth_headers`/`citizen_user`/`auth_headers`/`db`/`client` 与杨翼 conftest 一致。
