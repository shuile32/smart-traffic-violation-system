# 后端 API 层测试 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为第一阶段后端 `app/api/v1/*` 及 `core/middleware`、`core/permissions` 补全集成测试，覆盖鉴权 401/403、权限 403、成功路径与主要错误路径，零 ML/Redis/SMTP 依赖，唯一外部依赖为本机 MySQL 测试库。

**Architecture:** 在 `backend/tests/conftest.py` 中：import app 前用环境变量把 `DATABASE_URL` 切到 MySQL 测试库、注入 5 个 fake task 模块到 `sys.modules` 隔绝 ML/Celery broker、用 `join_transaction_mode="create_savepoint"` 的 Session 实现每用例事务回滚隔离、monkeypatch `intakes.chain` 与 `intakes.MEDIA_DIR`。6 个测试文件按路由组织，每个用例自包含种子数据。

**Tech Stack:** pytest、FastAPI `TestClient`、SQLAlchemy 2.0、MySQL(pymysql)、`unittest.mock` 风格的 fake task。

**前置事实（已读源码确认，写代码时直接用）：**
- 鉴权返回码：无 Authorization 头 → **401**（`HTTPBearer(auto_error=True)` 在当前 FastAPI 版本返回 401 "Not authenticated"）；token 无效/过期 → **401**（`get_current_user`）；角色不足 → **403**（`RoleChecker`）。
- `intakes.py:23` `MEDIA_DIR` 为硬编码相对路径，不读 settings，必须 monkeypatch。
- `intakes._create_case` 用 `chain(...).apply_async()`（对 chain 对象调用），非 `task.delay`。
- `cases.request_recheck` 调 `detect_objects_task.delay(...)`，未 try/except 包裹。
- `cases.approve` 调 `send_notification_task.delay(...)`，有 try/except 包裹。
- 全局响应体：`{"code": int, "message": str, "data": ...}`。
- 路由前缀：`/api/v1`。

---

## Task 0: 准备 MySQL 测试库

**Files:** 无（DB 侧操作）

- [ ] **Step 1: 建库**

在 MySQL 中创建测试库（账号按你本机情况改 `TEST_DATABASE_URL`）：

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS traffic_violation_test DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

- [ ] **Step 2: 确认连接串可用**

如需自定义账号，跑测试前 `export TEST_DATABASE_URL="mysql+pymysql://USER:PASS@localhost:3306/traffic_violation_test"`。未设则 conftest 回退 `mysql+pymysql://root:123456@localhost:3306/traffic_violation_test`（已验证可连）。

---

## Task 1: conftest.py 基础设施

**Files:**
- Create: `backend/tests/conftest.py`
- Smoke test: `backend/tests/test_smoke.py`

- [ ] **Step 1: 写 conftest.py**

```python
"""API 层测试基础设施。

设计要点：
1. 在 import app 之前用环境变量把 DATABASE_URL 切到 MySQL 测试库。
2. 注入 5 个 fake task 模块到 sys.modules，隔绝 ultralytics/paddleocr/Redis。
3. Session 用 join_transaction_mode="create_savepoint"，每用例事务回滚隔离。
4. monkeypatch intakes.chain 与运行期 intakes.MEDIA_DIR。
"""
import os
import sys
import types
import tempfile

# ── 在导入 app 之前配置环境 ─────────────────────────────
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "mysql+pymysql://root:123456@localhost:3306/traffic_violation_test",  # 本地开发凭据，CI 用 env 覆盖
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("DEBUG", "false")          # 关闭 SQL echo 噪声
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "30")
_media_tmp = tempfile.mkdtemp(prefix="tv_media_")
os.environ.setdefault("MEDIA_STORAGE_DIR", _media_tmp)

# ── 注入 fake task 模块，避免拉起 ultralytics/paddleocr/Redis ──
CELERY_CALLS: list = []


class _FakeTask:
    """假 Celery task：记录调用但不执行，不连 broker。"""

    def __init__(self, name: str):
        self.name = name

    def s(self, *a, **k):
        CELERY_CALLS.append(("s", self.name, a, k))
        return {"task": self.name, "args": a, "kwargs": k}

    def si(self, *a, **k):
        return self.s(*a, **k)

    def delay(self, *a, **k):
        CELERY_CALLS.append(("delay", self.name, a, k))
        return None

    def apply_async(self, *a, **k):
        CELERY_CALLS.append(("apply_async", self.name, a, k))
        return None


_FAKE_TASK_MODULES = {
    "app.tasks.detect_objects_task": ("detect_objects_task",),
    "app.tasks.ocr_plate_task": ("ocr_plate_task",),
    "app.tasks.evaluate_rule_task": ("evaluate_rule_task",),
    "app.tasks.ai_review_task": ("ai_review_task",),
    "app.tasks.send_notification_task": ("send_notification_task",),
}
for _mod_name, _names in _FAKE_TASK_MODULES.items():
    if _mod_name not in sys.modules:
        _fake = types.ModuleType(_mod_name)
        for _n in _names:
            setattr(_fake, _n, _FakeTask(_n))
        sys.modules[_mod_name] = _fake

# ── 现在才导入 app ──────────────────────────────────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401  注册所有模型到 Base.metadata
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app

engine = create_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)


class _FakeWorkflow:
    def apply_async(self, *a, **k):
        CELERY_CALLS.append(("chain.apply_async", a, k))
        return None


def _fake_chain(*sigs):
    CELERY_CALLS.append(("chain", sigs))
    return _FakeWorkflow()


# 替换 intakes 模块里的 chain（其 _create_case 用 chain(...).apply_async()）
import app.api.v1.intakes as _intakes_mod  # noqa: E402
_intakes_mod.chain = _fake_chain


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _reset_celery():
    CELERY_CALLS.clear()
    yield


@pytest.fixture
def celery_calls():
    return CELERY_CALLS


@pytest.fixture
def db_session():
    connection = engine.connect()
    trans = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    yield session
    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed_roles(db_session):
    from app.models.role import Role

    for name in ("citizen", "reviewer", "admin", "camera"):
        db_session.add(Role(name=name, description=name))
    db_session.commit()
    return {r.name: r.id for r in db_session.query(Role).all()}


@pytest.fixture
def make_user(db_session, seed_roles):
    from app.models.user import User

    counter = {"n": 0}

    def _make(role: str = "citizen", status: int = 1):
        counter["n"] += 1
        u = User(
            username=f"u{counter['n']}",
            password_hash=hash_password("123456"),
            role_id=seed_roles[role],
            status=status,
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        return u

    return _make


@pytest.fixture
def auth_header():
    def _make(role: str = "citizen", user_id: int = 1):
        token = create_access_token(user_id, role)
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def seed_camera(db_session):
    import hashlib
    from app.models.camera_device import CameraDevice
    from app.models.camera_api_key import CameraApiKey

    dev = CameraDevice(device_name="cam1", device_code="DEV001", location_text="路口A")
    db_session.add(dev)
    db_session.commit()
    db_session.refresh(dev)
    raw_key = "test-camera-key-123"
    db_session.add(CameraApiKey(
        camera_device_id=dev.id,
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        key_prefix=raw_key[:8],
        status="active",
    ))
    db_session.commit()
    return {"device": dev, "raw_key": raw_key}
```

- [ ] **Step 2: 写 smoke 测试验证基础设施**

```python
# backend/tests/test_smoke.py
"""验证 conftest 基础设施可用。"""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_db_session_writable(db_session):
    from app.models.role import Role

    db_session.add(Role(name="smoke_role"))
    db_session.commit()
    assert db_session.query(Role).filter_by(name="smoke_role").count() == 1


def test_celery_fake_records(celery_calls):
    # conftest 已注入 fake；直接调用确认记录链路
    from app.tasks.detect_objects_task import detect_objects_task

    detect_objects_task.delay(1, "/x.jpg")
    assert any(c[0] == "delay" for c in celery_calls)
```

- [ ] **Step 3: 跑 smoke**

Run: `cd backend && python -m pytest tests/test_smoke.py -v`
Expected: 3 passed。

若报 `Can't connect to MySQL server`：确认 Task 0 的库已建、`TEST_DATABASE_URL` 正确。
若报 savepoint 相关错：把 `db_session` 的 `join_transaction_mode="create_savepoint"` 行注释掉，改用文末「Fallback 隔离方案」。

- [ ] **Step 4: 提交**

```bash
git add backend/tests/conftest.py backend/tests/test_smoke.py
git commit -m "test: API 层测试基础设施 conftest + smoke"
```

> **Fallback 隔离方案**（仅当 savepoint 模式出问题时替换 `db_session` fixture）：
> ```python
> @pytest.fixture
> def db_session():
>     from sqlalchemy.orm import sessionmaker
>     SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
>     session = SessionLocal()
>     yield session
>     for t in reversed(Base.metadata.sorted_tables):
>         session.execute(t.delete())
>     session.commit()
>     session.close()
> ```
> 该方案靠每用例末尾按 FK 逆序清空所有表实现隔离，不依赖 savepoint，更稳但稍慢。

---

## Task 2: test_auth_api.py

**Files:**
- Create: `backend/tests/test_auth_api.py`

- [ ] **Step 1: 写测试文件**

```python
"""auth 路由测试：login / me / permissions menus。"""


def test_login_success(client, make_user):
    u = make_user(role="citizen")
    resp = client.post("/api/v1/auth/login",
                       json={"username": u.username, "password": "123456"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["access_token"]
    assert body["data"]["user"]["username"] == u.username


def test_login_wrong_password(client, make_user):
    u = make_user(role="citizen")
    resp = client.post("/api/v1/auth/login",
                       json={"username": u.username, "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


def test_login_unknown_user(client):
    resp = client.post("/api/v1/auth/login",
                       json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


def test_login_disabled_account(client, make_user):
    u = make_user(role="citizen", status=0)
    resp = client.post("/api/v1/auth/login",
                       json={"username": u.username, "password": "123456"})
    assert resp.status_code == 403


def test_me_without_token_returns_403(client):
    # HTTPBearer 默认 auto_error=True → 403
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 403


def test_me_with_invalid_token_returns_401(client):
    resp = client.get("/api/v1/auth/me",
                      headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_me_with_token(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/auth/me", headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == u.username


def test_menus_admin_has_system_management(client, auth_header):
    resp = client.get("/api/v1/auth/permissions/menus",
                      headers=auth_header("admin", 1))
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()["data"]["menus"]]
    assert "系统管理" in names


def test_menus_citizen_no_system_management(client, auth_header):
    resp = client.get("/api/v1/auth/permissions/menus",
                      headers=auth_header("citizen", 1))
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()["data"]["menus"]]
    assert "系统管理" not in names
```

- [ ] **Step 2: 跑**

Run: `cd backend && python -m pytest tests/test_auth_api.py -v`
Expected: 9 passed。

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_auth_api.py
git commit -m "test: auth 路由覆盖 login/me/menus"
```

---

## Task 3: test_intakes_api.py

**Files:**
- Create: `backend/tests/test_intakes_api.py`

- [ ] **Step 1: 写测试文件**

```python
"""intakes 路由测试：citizen-reports / camera-captures / admin-uploads。"""


def _jpg():
    # 最小 JPEG 字节流
    return ("test.jpg",
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9",
            "image/jpeg")


def test_citizen_report_no_token_returns_401(client):
    resp = client.post("/api/v1/intakes/citizen-reports",
                       files={"image": _jpg()},
                       data={"location_text": "A", "captured_at": "2026-07-08T10:00:00"})
    assert resp.status_code == 401


def test_citizen_report_success(client, make_user, auth_header, monkeypatch, tmp_path,
                               db_session, celery_calls):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    u = make_user(role="citizen")
    resp = client.post("/api/v1/intakes/citizen-reports",
                       files={"image": _jpg()},
                       data={"location_text": "路口A",
                             "captured_at": "2026-07-08T10:00:00",
                             "description": "违停"},
                       headers=auth_header("citizen", u.id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "uploaded"
    assert data["case_no"].startswith("CASE")
    from app.models.case import Case
    assert db_session.query(Case).count() == 1
    assert any(c[0] == "chain" for c in celery_calls)


def test_camera_capture_no_key_returns_401(client):
    resp = client.post("/api/v1/intakes/camera-captures",
                       files={"image": _jpg()},
                       data={"camera_id": "DEV001", "captured_at": "2026-07-08T10:00:00"})
    assert resp.status_code == 401


def test_camera_capture_invalid_key_returns_401(client, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    resp = client.post("/api/v1/intakes/camera-captures",
                       files={"image": _jpg()},
                       data={"camera_id": "DEV001", "captured_at": "2026-07-08T10:00:00"},
                       headers={"X-Camera-Key": "wrong"})
    assert resp.status_code == 401


def test_camera_capture_success(client, seed_camera, monkeypatch, tmp_path, celery_calls):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    resp = client.post("/api/v1/intakes/camera-captures",
                       files={"image": _jpg()},
                       data={"camera_id": "DEV001",
                             "captured_at": "2026-07-08T10:00:00",
                             "speed": "88.5"},
                       headers={"X-Camera-Key": seed_camera["raw_key"]})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "uploaded"
    assert any(c[0] == "chain" for c in celery_calls)


def test_admin_upload_citizen_forbidden(client, make_user, auth_header, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    u = make_user(role="citizen")
    resp = client.post("/api/v1/intakes/admin-uploads",
                       files={"image": _jpg()},
                       data={"captured_at": "2026-07-08T10:00:00"},
                       headers=auth_header("citizen", u.id))
    assert resp.status_code == 403


def test_admin_upload_reviewer_success(client, make_user, auth_header, monkeypatch,
                                      tmp_path, celery_calls):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    u = make_user(role="reviewer")
    resp = client.post("/api/v1/intakes/admin-uploads",
                       files={"image": _jpg()},
                       data={"captured_at": "2026-07-08T10:00:00", "location_text": "B"},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert any(c[0] == "chain" for c in celery_calls)
```

- [ ] **Step 2: 跑**

Run: `cd backend && python -m pytest tests/test_intakes_api.py -v`
Expected: 7 passed。

若某用例报文件写入相关错，确认 `monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))` 在请求前已调用。

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_intakes_api.py
git commit -m "test: intakes 路由覆盖 citizen/camera/admin 上传与鉴权"
```

---

## Task 4: test_cases_api.py

**Files:**
- Create: `backend/tests/test_cases_api.py`

- [ ] **Step 1: 写测试文件**

```python
"""cases 路由测试：list / get / approve / reject / request-recheck。"""
from datetime import datetime, timezone

from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.media_asset import MediaAsset


def _seed_case(db_session, status="pending_human_review", case_no="CASE001"):
    intake = IntakeEvent(
        source_type="admin", source_id=1,
        captured_at=datetime(2026, 7, 8, 10, 0, 0),
        image_hash="h" * 64, status="uploaded",
    )
    db_session.add(intake)
    db_session.flush()
    media = MediaAsset(
        intake_event_id=intake.id, asset_type="original",
        url="/media/x.jpg", mime_type="image/jpeg", size=10,
    )
    db_session.add(media)
    db_session.flush()
    case = Case(case_no=case_no, intake_event_id=intake.id, status=status)
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def test_list_cases_no_token_returns_401(client):
    assert client.get("/api/v1/cases").status_code == 401


def test_list_cases_citizen_forbidden(client, make_user, auth_header):
    u = make_user(role="citizen")
    resp = client.get("/api/v1/cases", headers=auth_header("citizen", u.id))
    assert resp.status_code == 403


def test_list_cases_reviewer_ok(client, make_user, auth_header, db_session):
    _seed_case(db_session)
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/cases", headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 1


def test_list_cases_filter_by_status(client, make_user, auth_header, db_session):
    _seed_case(db_session, status="approved", case_no="CASE001")
    _seed_case(db_session, status="pending_human_review", case_no="CASE002")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/cases?status=approved",
                      headers=auth_header("reviewer", u.id))
    assert resp.json()["data"]["total"] == 1


def test_get_case_404(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/cases/9999", headers=auth_header("reviewer", u.id))
    assert resp.status_code == 404


def test_approve_wrong_state_returns_400(client, make_user, auth_header, db_session):
    c = _seed_case(db_session, status="uploaded")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/approve",
                       json={"plate_no": "京A12345", "violation_type": "违停"},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 400


def test_approve_success_creates_violation_and_audit(client, make_user, auth_header,
                                                    db_session, celery_calls):
    c = _seed_case(db_session, status="pending_human_review")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/approve",
                       json={"plate_no": "京A12345", "violation_type": "违停",
                             "fine_amount": 200, "points": 3},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    from app.models.violation import Violation
    from app.models.audit_log import AuditLog
    assert db_session.query(Violation).count() == 1
    assert db_session.query(AuditLog).filter_by(action="case:approve").count() == 1
    db_session.refresh(c)
    assert c.status == "archived"


def test_reject_success(client, make_user, auth_header, db_session):
    c = _seed_case(db_session, status="pending_human_review")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/reject",
                       json={"reject_reason": "证据不足"},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    db_session.refresh(c)
    assert c.status == "rejected"


def test_request_recheck_success(client, make_user, auth_header, db_session, celery_calls):
    c = _seed_case(db_session, status="pending_human_review")
    u = make_user(role="reviewer")
    resp = client.post(f"/api/v1/cases/{c.id}/request-recheck",
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    db_session.refresh(c)
    assert c.status == "detecting"
    assert any(call[0] == "delay" for call in celery_calls)
```

- [ ] **Step 2: 跑**

Run: `cd backend && python -m pytest tests/test_cases_api.py -v`
Expected: 9 passed。

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_cases_api.py
git commit -m "test: cases 路由覆盖 list/get/approve/reject/recheck"
```

---

## Task 5: test_violations_api.py

**Files:**
- Create: `backend/tests/test_violations_api.py`

- [ ] **Step 1: 写测试文件**

```python
"""violations 路由测试：list / get / owner 违章查询的越权校验。"""
from datetime import datetime

from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.violation import Violation


def _seed_violation(db_session, plate="京A12345", vtype="违停", owner_id=None):
    intake = IntakeEvent(
        source_type="admin", source_id=1,
        captured_at=datetime(2026, 7, 8, 10, 0, 0),
        image_hash="h" * 64, status="uploaded",
    )
    db_session.add(intake)
    db_session.flush()
    case = Case(case_no=f"CASE{plate}", intake_event_id=intake.id, status="approved")
    db_session.add(case)
    db_session.flush()
    v = Violation(
        violation_no=f"VIO{plate}", case_id=case.id,
        plate_no=plate, violation_type=vtype,
        occurred_at=datetime(2026, 7, 8, 10, 0, 0),
        owner_id=owner_id, fine_amount=200, points=3, status="pending",
    )
    db_session.add(v)
    db_session.commit()
    return v


def test_list_violations_filter_by_type(client, make_user, auth_header, db_session):
    _seed_violation(db_session, plate="京A111", vtype="违停")
    _seed_violation(db_session, plate="京B222", vtype="超速")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/violations?violation_type=超速",
                      headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 1


def test_list_violations_filter_by_plate(client, make_user, auth_header, db_session):
    _seed_violation(db_session, plate="京A111")
    _seed_violation(db_session, plate="京B222")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/violations?plate_no=京A",
                      headers=auth_header("reviewer", u.id))
    assert resp.json()["data"]["total"] == 1


def test_get_violation_404(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/violations/9999",
                      headers=auth_header("reviewer", u.id))
    assert resp.status_code == 404


def test_owner_violations_self_ok(client, make_user, auth_header, db_session):
    u = make_user(role="citizen")
    _seed_violation(db_session, owner_id=u.id)
    resp = client.get(f"/api/v1/violations/owners/{u.id}/violations",
                      headers=auth_header("citizen", u.id))
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 1


def test_owner_violations_other_forbidden(client, make_user, auth_header):
    u = make_user(role="citizen")
    other = make_user(role="citizen")
    resp = client.get(f"/api/v1/violations/owners/{other.id}/violations",
                      headers=auth_header("citizen", u.id))
    assert resp.status_code == 403


def test_owner_violations_admin_can_view_other(client, make_user, auth_header, db_session):
    other = make_user(role="citizen")
    _seed_violation(db_session, owner_id=other.id)
    admin = make_user(role="admin")
    resp = client.get(f"/api/v1/violations/owners/{other.id}/violations",
                      headers=auth_header("admin", admin.id))
    assert resp.status_code == 200
```

- [ ] **Step 2: 跑**

Run: `cd backend && python -m pytest tests/test_violations_api.py -v`
Expected: 6 passed。

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_violations_api.py
git commit -m "test: violations 路由覆盖 list/get 与 owner 越权校验"
```

---

## Task 6: test_statistics_api.py

**Files:**
- Create: `backend/tests/test_statistics_api.py`

- [ ] **Step 1: 写测试文件**

```python
"""statistics 路由测试：overview / by-location / by-type / by-time。"""
from datetime import datetime

from app.models.case import Case
from app.models.intake_event import IntakeEvent
from app.models.violation import Violation

WIN = {"start_time": "2026-01-01T00:00:00", "end_time": "2026-12-31T23:59:59"}


def _seed(db_session, case_status="approved", vtype="违停", location="路口A",
          created=datetime(2026, 7, 8, 10, 0, 0)):
    intake = IntakeEvent(
        source_type="admin", source_id=1,
        captured_at=datetime(2026, 7, 8, 10, 0, 0),
        image_hash="h" * 64, status="uploaded",
    )
    db_session.add(intake)
    db_session.flush()
    case = Case(case_no=f"C{vtype}{location}", intake_event_id=intake.id,
                status=case_status, created_at=created)
    db_session.add(case)
    db_session.flush()
    v = Violation(
        violation_no=f"V{vtype}{location}", case_id=case.id,
        plate_no="京A1", violation_type=vtype,
        occurred_at=datetime(2026, 7, 8, 10, 0, 0),
        location_text=location, fine_amount=200, points=3,
        status="pending", created_at=created,
    )
    db_session.add(v)
    db_session.commit()
    return v


def test_overview_no_token_returns_401(client):
    assert client.get("/api/v1/statistics/overview", params=WIN).status_code == 401


def test_overview_counts(client, make_user, auth_header, db_session):
    _seed(db_session, case_status="approved")
    _seed(db_session, case_status="rejected", location="路口B")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200
    d = resp.json()["data"]
    assert d["total_cases"] == 2
    assert d["approved_count"] == 1
    assert d["rejected_count"] == 1


def test_by_location_orders_by_count_desc(client, make_user, auth_header, db_session):
    _seed(db_session, location="路口A")
    _seed(db_session, location="路口A", vtype="超速")
    _seed(db_session, location="路口B")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/by-location",
                      headers=auth_header("reviewer", u.id), params=WIN)
    items = resp.json()["data"]["items"]
    assert items[0]["location_text"] == "路口A"
    assert items[0]["count"] == 2


def test_by_type_returns_all_types(client, make_user, auth_header, db_session):
    _seed(db_session, vtype="违停")
    _seed(db_session, vtype="超速", location="路口B")
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/by-type",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200
    assert len(resp.json()["data"]["items"]) == 2


def test_by_time_returns_daily_bucket(client, make_user, auth_header, db_session):
    _seed(db_session, created=datetime(2026, 7, 8, 10, 0, 0))
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/by-time",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) >= 1
    assert any(i["count"] == 1 for i in items)
```

- [ ] **Step 2: 跑**

Run: `cd backend && python -m pytest tests/test_statistics_api.py -v`
Expected: 5 passed。

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_statistics_api.py
git commit -m "test: statistics 路由覆盖 overview/by-location/by-type/by-time"
```

---

## Task 7: test_rbac_api.py

**Files:**
- Create: `backend/tests/test_rbac_api.py`

- [ ] **Step 1: 写测试文件**

```python
"""RBAC 测试：经真实端点验证 RoleChecker 对各角色的 200/403 决策。"""

WIN = {"start_time": "2026-01-01T00:00:00", "end_time": "2026-12-31T23:59:59"}


def test_admin_can_access_reviewer_endpoint(client, make_user, auth_header):
    u = make_user(role="admin")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("admin", u.id), params=WIN)
    assert resp.status_code == 200


def test_reviewer_can_access(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200


def test_citizen_blocked_from_reviewer_endpoint(client, make_user, auth_header):
    u = make_user(role="citizen")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("citizen", u.id), params=WIN)
    assert resp.status_code == 403


def test_camera_role_blocked(client, make_user, auth_header):
    u = make_user(role="camera")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("camera", u.id), params=WIN)
    assert resp.status_code == 403


def test_admin_can_access_cases_list(client, make_user, auth_header):
    u = make_user(role="admin")
    resp = client.get("/api/v1/cases", headers=auth_header("admin", u.id))
    assert resp.status_code == 200
```

- [ ] **Step 2: 跑**

Run: `cd backend && python -m pytest tests/test_rbac_api.py -v`
Expected: 5 passed。

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_rbac_api.py
git commit -m "test: RBAC 经真实端点验证各角色 200/403"
```

---

## Task 8: 全量回归

- [ ] **Step 1: 跑全部测试**

Run: `cd backend && python -m pytest -v`
Expected: 全绿（既有 20 + 新增约 40 = 约 60 用例）。

- [ ] **Step 2: 若有用例失败**

按 TDD red→green 处理：若测试揭示的是真实 API bug，修 `app/` 下对应代码并在此 commit；若是测试本身写错，改测试。每个修复单独 commit，信息 `fix: <说明>`。

- [ ] **Step 3: 收尾提交（若有零散改动）**

```bash
git add -A
git commit -m "test: API 层测试全量回归通过"
```

---

## 自检清单（实现完成后逐项确认）

- [ ] `python -m pytest` 全绿，无跳过。
- [ ] 测试未连真实 Redis / LLM / SMTP / 模型权重（靠 `sys.modules` fake task 注入）。
- [ ] 唯一外部依赖为本机 MySQL `traffic_violation_test` 库。
- [ ] `backend/media` 未被测试文件污染（`intakes.MEDIA_DIR` monkeypatch 到 tmp）。
- [ ] 覆盖矩阵：auth(9) + intakes(7) + cases(9) + violations(6) + statistics(5) + rbac(5) + smoke(3) = 44 新增用例。
