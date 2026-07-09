# 张浩-5 统计分析 API · Design Spec

## 背景

团队第一阶段 spec（`docs/superpowers/specs/2026-07-08-交通违章平台-第一阶段开发方案-design.md`）§6.1 把 statistics 列为 IN-scope：`GET /api/v1/statistics/overview`、`/by-location`、`/by-time`、`/by-type`（只返回聚合数据，无前端图表）。分工张浩-5。

upstream 现状（`d175700`）：杨翼 M3 已建 `Violation` 模型（`app/models/violation.py`：violation_type/location_text/created_at/occurred_at/status/fine_amount/points）+ `Case` 模型（`app/models/intake.py`：status/created_at）+ violations 路由/service/schemas。violations 表已就绪，张浩-5 不再阻塞。

本任务在 `zhanghao/statistics` 分支（off main d175700）上实现 4 个统计路由，照杨翼的 route→service→schemas 模式，强类型 Pydantic 响应、`require_role("reviewer","admin")` 鉴权、SQLite 内存测试。

## 范围

**IN（4 路由）：**
- `GET /api/v1/statistics/overview` — 案件管线概览（查 Case）
- `GET /api/v1/statistics/by-location` — 违章地点分布（查 Violation）
- `GET /api/v1/statistics/by-type` — 违章类型分布（查 Violation）
- `GET /api/v1/statistics/by-time` — 违章时间趋势（查 Violation，按日）

**OUT：** 前端图表（§6.1 只聚合数据）；by-week/by-month 粒度（YAGNI，先 daily）；不动杨翼的 violations/cases 代码。

## 架构

```
backend/app/api/v1/statistics.py        # 4 路由，require_role，调 StatisticsService
backend/app/services/statistics_service.py  # StatisticsService，4 个聚合方法
backend/app/schemas/statistics.py       # OverviewOut/ByLocationOut/ByTypeOut/ByTimeOut
backend/app/api/v1/router.py            # 挂载 statistics.router
backend/tests/api/test_statistics_api.py
backend/tests/services/test_statistics_service.py
```

## 路由与指标

### overview（查 Case）
- 时间窗：`Case.created_at.between(st, et)`
- `total_cases` = Case 在窗内总数
- `approved_count` = Case status=="approved" 在窗内
- `rejected_count` = Case status=="rejected" 在窗内
- `pending_count` = Case status=="pending_human_review"（当前队列，**不过滤时间窗**）
- `approval_rate` = approved/total*100（total=0 时 0.0），保留 1 位
- `period` = {start, end}（ISO 字符串）

### by-location（查 Violation）
- 时间窗：`Violation.created_at.between(st, et)`
- `group by Violation.location_text`，`count(id)`，倒序，`limit`（默认 10，1~50）
- items: [{location_text, count}]

### by-type（查 Violation）
- 时间窗同上
- `total` = 窗内 Violation 总数
- `group by violation_type`，count + `percentage` = count/total*100（total=0 时 0.0）
- items: [{violation_type, count, percentage}]

### by-time（查 Violation）
- 时间窗同上
- `group by date(cast created_at as Date)`，count，按 date 正序
- items: [{date, count}]（date 为 "YYYY-MM-DD" 字符串）

## 时间过滤

- query 参数 `start_time`/`end_time`：ISO 字符串（如 `2026-01-01T00:00:00`）
- 缺省：`start_time` 无 → `datetime(2000,1,1, tzinfo=UTC)`；`end_time` 无 → `datetime.now(timezone.utc)`
- 用 `datetime.fromisoformat` 解析，timezone-aware（Violation.created_at/Case.created_at 都是 tz-aware）

## Schemas（`app/schemas/statistics.py`）

```python
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

## Service（`app/services/statistics_service.py`）

`class StatisticsService: def __init__(self, db)`，4 方法：
- `overview(st, et) -> OverviewOut`
- `by_location(st, et, limit) -> ByLocationOut`
- `by_type(st, et) -> ByTypeOut`
- `by_time(st, et) -> ByTimeOut`

聚合用 `sqlalchemy.func.count` + `group_by`；by-time 用 `cast(Violation.created_at, Date)`（SQLite 兼容）。方法直接返回 Pydantic Out 对象（service 构造，route 透传）。

## 鉴权

4 路由全部 `Depends(require_role("reviewer", "admin"))`。无 token→401、citizen→403、reviewer/admin→200。

## 测试（TDD）

### `tests/services/test_statistics_service.py`
种 3 条 Case（approved/rejected/pending）+ 3 条 Violation（不同 location/type/created_at），断言：
- overview 计数 + approval_rate 正确
- by-location 倒序、limit 生效
- by-type count + percentage 正确
- by-time 按日分组 + 正序

### `tests/api/test_statistics_api.py`
4 路由各测：无 token→401、citizen→403、reviewer→200 + 响应结构断言（字段齐全）。

复用 conftest 的 `client`/`reviewer_auth_headers`/`citizen_user`/`auth_headers`/`db`/`seeded_roles`。种 Case/Violation 用 helper（参考杨翼 test_review_flow_integration 的种数据方式）。

## 成功标准

- `cd backend && python -m pytest -q` 全绿（基线 62 + 本任务新增约 12-15）。
- 4 个 `/api/v1/statistics/*` 路由可用，强类型响应，鉴权到位。
- 不动杨翼的 violations/cases/auth/intakes 代码（`git diff main -- app/api/v1/violations.py app/services/violation_service.py` 等应为空）。

## 不做

- 前端图表、by-week/by-month 粒度。
- 不改 Violation/Case 模型。
- 不引入 Celery/Redis。
