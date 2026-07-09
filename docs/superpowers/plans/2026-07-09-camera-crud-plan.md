# 张浩-7 摄像头设备管理 CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本地 main（d175700 + 张浩-5/9/10 + seed，基线 111 passed）上实现摄像头设备 + API Key 的 CRUD（7 路由，软删），照杨翼 route→service→schemas 模式，admin 鉴权，TDD。

**Architecture:** `app/schemas/camera.py`（Pydantic）→ `app/services/camera_service.py`（CameraService，Key 生成用 secrets+sha256）→ `app/api/v1/cameras.py`（7 路由，`require_role("admin")`）→ `router.py` 挂载。软删（设备 disable/Key revoke 走 status），与张浩-9 的 status 鉴权衔接。

**Tech Stack:** FastAPI、SQLAlchemy 2.0、Pydantic v2、`secrets`+`hashlib`、pytest + TestClient（SQLite 内存）。

**分支：** `zhanghao/camera-crud`（off main，基线 111 passed）。跑测试：`cd backend && python -m pytest ...`。

**已确认事实：**
- `CameraDevice`（`app/models/intake.py`）：id/device_code(unique)/location_text/status(default "enabled")/created_at。
- `CameraApiKey`：id/camera_device_id(FK)/key_hash(String255 unique index)/status(default "active")/created_at。
- 张浩-9 的 `get_camera_device`（`app/core/deps.py`）按 `key_hash==sha256(raw) AND status=="active"` 查 + `dev.status=="enabled"` 放行。
- 鉴权：`from app.core.deps import require_role`；`_: User = Depends(require_role("admin"))`。无 token→401、非 admin→403。
- conftest fixtures：`client`/`db`/`seeded_roles`/`citizen_user`/`auth_headers`/`reviewer_user`/`reviewer_auth_headers`。**无 admin_user**（Task 2 加）。
- 杨翼 router.py 风格：`api_router.include_router(xxx.router)`，prefix 在 api_router（`/api/v1`），路由内写 `/admin/cameras/...`。

---

## Task 1: Schemas（`app/schemas/camera.py`）

**Files:**
- Create: `backend/app/schemas/camera.py`
- Test: `backend/tests/test_schemas_camera.py`

- [ ] **Step 1: 写测试 `tests/test_schemas_camera.py`**

```python
from datetime import datetime, timezone

from app.schemas.camera import (
    CameraDeviceCreateIn,
    CameraDeviceListResponse,
    CameraDeviceOut,
    CameraDeviceUpdateIn,
    CameraKeyCreateOut,
    CameraKeyListResponse,
    CameraKeyOut,
)


def test_camera_device_out_from_attributes():
    d = CameraDeviceOut.model_validate({
        "id": 1, "device_code": "C1", "location_text": "A",
        "status": "enabled", "created_at": datetime(2026, 7, 8, tzinfo=timezone.utc),
    })
    assert d.device_code == "C1"
    assert d.status == "enabled"


def test_camera_device_create_in_defaults():
    c = CameraDeviceCreateIn(device_code="C1")
    assert c.location_text is None


def test_camera_device_update_in_all_optional():
    u = CameraDeviceUpdateIn()
    assert u.location_text is None
    assert u.status is None


def test_camera_key_create_out():
    o = CameraKeyCreateOut(raw_key="abc", key=CameraKeyOut(
        id=1, camera_device_id=2, status="active",
        created_at=datetime(2026, 7, 8, tzinfo=timezone.utc)))
    assert o.raw_key == "abc"
    assert o.key.id == 1


def test_list_responses():
    lr = CameraDeviceListResponse(items=[], total=0, page=1, page_size=20)
    assert lr.total == 0
    kr = CameraKeyListResponse(items=[])
    assert kr.items == []
```

- [ ] **Step 2: 跑，确认 FAIL**

Run: `cd backend && python -m pytest tests/test_schemas_camera.py -v`
Expected: FAIL — `ModuleNotFoundError: app.schemas.camera`

- [ ] **Step 3: 写 `app/schemas/camera.py`**

```python
from datetime import datetime

from pydantic import BaseModel


class CameraDeviceOut(BaseModel):
    id: int
    device_code: str
    location_text: str | None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class CameraDeviceCreateIn(BaseModel):
    device_code: str
    location_text: str | None = None


class CameraDeviceUpdateIn(BaseModel):
    location_text: str | None = None
    status: str | None = None  # enabled / disabled


class CameraDeviceListResponse(BaseModel):
    items: list[CameraDeviceOut]
    total: int
    page: int
    page_size: int


class CameraKeyOut(BaseModel):
    id: int
    camera_device_id: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
    # 不含 key_hash / raw


class CameraKeyCreateOut(BaseModel):
    raw_key: str  # 只在生成时返回一次
    key: CameraKeyOut


class CameraKeyListResponse(BaseModel):
    items: list[CameraKeyOut]
```

- [ ] **Step 4: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/test_schemas_camera.py -v`
Expected: 5 passed。

- [ ] **Step 5: 提交**

```bash
git add backend/app/schemas/camera.py backend/tests/test_schemas_camera.py
git commit -m "feat(camera): Pydantic schemas"
```

---

## Task 2: conftest 加 admin fixtures

**Files:**
- Modify: `backend/tests/conftest.py`（在 `reviewer_auth_headers` 之后追加 admin 三件套）

- [ ] **Step 1: Read conftest.py 找到 `reviewer_auth_headers` fixture 结尾，在其后追加**

```python
@pytest.fixture()
def admin_user(db: Session, seeded_roles) -> User:
    user = User(
        username="admin1",
        password_hash=hash_password("pass1234"),
        email="admin@example.com",
        role_id=seeded_roles["admin"].id,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def admin_token(admin_user: User) -> str:
    return create_access_token(subject=str(admin_user.id), role="admin")


@pytest.fixture()
def admin_auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
```

- [ ] **Step 2: 跑全量确认无回归**

Run: `cd backend && python -m pytest -q`
Expected: 111 passed（只加 fixture，无新测试）。

- [ ] **Step 3: 提交**

```bash
git add backend/tests/conftest.py
git commit -m "test(camera): conftest 加 admin_user/admin_auth_headers fixtures"
```

---

## Task 3: CameraService + service 测试（TDD）

**Files:**
- Create: `backend/app/services/camera_service.py`
- Test: `backend/tests/services/test_camera_service.py`

- [ ] **Step 1: 写测试 `tests/services/test_camera_service.py`**

```python
import hashlib

import pytest

from app.models.intake import CameraApiKey
from app.services.camera_service import CameraService


def test_create_device(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text="路口A")
    assert dev.id is not None
    assert dev.device_code == "CAM01"
    assert dev.status == "enabled"


def test_create_device_duplicate_409(db):
    CameraService(db).create_device(device_code="CAM01", location_text=None)
    with pytest.raises(Exception) as exc:
        CameraService(db).create_device(device_code="CAM01", location_text=None)
    assert exc.value.status_code == 409


def test_list_devices_pagination(db):
    for i in range(5):
        CameraService(db).create_device(device_code=f"CAM0{i}", location_text=None)
    res = CameraService(db).list_devices(page=1, page_size=2)
    assert res["total"] == 5
    assert len(res["items"]) == 2


def test_get_device_404(db):
    with pytest.raises(Exception) as exc:
        CameraService(db).get_device(9999)
    assert exc.value.status_code == 404


def test_update_device(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text="A")
    updated = CameraService(db).update_device(dev.id, location_text="B", status="disabled")
    assert updated.location_text == "B"
    assert updated.status == "disabled"


def test_update_device_invalid_status_400(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    with pytest.raises(Exception) as exc:
        CameraService(db).update_device(dev.id, location_text=None, status="bogus")
    assert exc.value.status_code == 400


def test_create_key_returns_raw_and_sha256_hash(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    raw, key = CameraService(db).create_key(dev.id)
    assert len(raw) > 0
    assert key.key_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert key.status == "active"


def test_create_key_device_not_found_404(db):
    with pytest.raises(Exception) as exc:
        CameraService(db).create_key(9999)
    assert exc.value.status_code == 404


def test_revoke_key(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    _, key = CameraService(db).create_key(dev.id)
    revoked = CameraService(db).revoke_key(dev.id, key.id)
    assert revoked.status == "revoked"


def test_revoke_key_not_found_404(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    with pytest.raises(Exception) as exc:
        CameraService(db).revoke_key(dev.id, 9999)
    assert exc.value.status_code == 404


def test_revoked_key_not_in_active_query(db):
    """撤销后的 Key 在张浩-9 的 active 查询里查不到（鉴权会 401）。"""
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    raw, key = CameraService(db).create_key(dev.id)
    CameraService(db).revoke_key(dev.id, key.id)
    found = (
        db.query(CameraApiKey)
        .filter(
            CameraApiKey.key_hash == hashlib.sha256(raw.encode()).hexdigest(),
            CameraApiKey.status == "active",
        )
        .first()
    )
    assert found is None
```

- [ ] **Step 2: 跑，确认 FAIL**

Run: `cd backend && python -m pytest tests/services/test_camera_service.py -v`
Expected: FAIL — `ModuleNotFoundError: app.services.camera_service`

- [ ] **Step 3: 写 `app/services/camera_service.py`**

```python
# app/services/camera_service.py
import hashlib
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.intake import CameraApiKey, CameraDevice

VALID_DEVICE_STATUS = {"enabled", "disabled"}


class CameraService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_device(self, *, device_code: str, location_text: str | None) -> CameraDevice:
        if self.db.query(CameraDevice).filter_by(device_code=device_code).first():
            raise HTTPException(status_code=409, detail="设备编号已存在")
        dev = CameraDevice(device_code=device_code, location_text=location_text)
        self.db.add(dev)
        self.db.commit()
        self.db.refresh(dev)
        return dev

    def list_devices(self, *, page: int, page_size: int) -> dict:
        total = self.db.query(CameraDevice).count()
        items = (
            self.db.query(CameraDevice)
            .order_by(CameraDevice.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_device(self, device_id: int) -> CameraDevice:
        dev = self.db.get(CameraDevice, device_id)
        if dev is None:
            raise HTTPException(status_code=404, detail="设备不存在")
        return dev

    def update_device(self, device_id: int, *, location_text: str | None, status: str | None) -> CameraDevice:
        dev = self.get_device(device_id)
        if status is not None and status not in VALID_DEVICE_STATUS:
            raise HTTPException(status_code=400, detail="status 必须是 enabled 或 disabled")
        if location_text is not None:
            dev.location_text = location_text
        if status is not None:
            dev.status = status
        self.db.commit()
        self.db.refresh(dev)
        return dev

    def create_key(self, device_id: int) -> tuple[str, CameraApiKey]:
        dev = self.get_device(device_id)  # 404 if not exist
        raw = secrets.token_urlsafe(32)
        key = CameraApiKey(
            camera_device_id=dev.id,
            key_hash=hashlib.sha256(raw.encode()).hexdigest(),
        )
        self.db.add(key)
        self.db.commit()
        self.db.refresh(key)
        return raw, key

    def list_keys(self, device_id: int) -> list[CameraApiKey]:
        self.get_device(device_id)  # 404 if device not exist
        return (
            self.db.query(CameraApiKey)
            .filter(CameraApiKey.camera_device_id == device_id)
            .order_by(CameraApiKey.id.desc())
            .all()
        )

    def revoke_key(self, device_id: int, key_id: int) -> CameraApiKey:
        self.get_device(device_id)
        key = (
            self.db.query(CameraApiKey)
            .filter(CameraApiKey.id == key_id, CameraApiKey.camera_device_id == device_id)
            .first()
        )
        if key is None:
            raise HTTPException(status_code=404, detail="Key 不存在")
        key.status = "revoked"
        self.db.commit()
        self.db.refresh(key)
        return key
```

- [ ] **Step 4: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/services/test_camera_service.py -v`
Expected: 11 passed。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/camera_service.py backend/tests/services/test_camera_service.py
git commit -m "feat(camera): CameraService 设备/Key CRUD + 测试"
```

---

## Task 4: 路由 + router 挂载 + API 测试（TDD）

**Files:**
- Create: `backend/app/api/v1/cameras.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/api/test_cameras_api.py`

- [ ] **Step 1: 写测试 `tests/api/test_cameras_api.py`**

```python
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_create_device_requires_auth(client):
    assert client.post("/api/v1/admin/cameras", json={"device_code": "C1"}).status_code == 401


def test_create_device_reviewer_forbidden(client, reviewer_user, reviewer_auth_headers):
    r = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=reviewer_auth_headers)
    assert r.status_code == 403


def test_create_device_success(client, admin_user, admin_auth_headers):
    r = client.post("/api/v1/admin/cameras",
                    json={"device_code": "CAM01", "location_text": "路口A"}, headers=admin_auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["device_code"] == "CAM01"
    assert data["status"] == "enabled"


def test_list_devices(client, admin_user, admin_auth_headers):
    client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers)
    client.post("/api/v1/admin/cameras", json={"device_code": "C2"}, headers=admin_auth_headers)
    r = client.get("/api/v1/admin/cameras", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_get_device_404(client, admin_user, admin_auth_headers):
    assert client.get("/api/v1/admin/cameras/9999", headers=admin_auth_headers).status_code == 404


def test_patch_device(client, admin_user, admin_auth_headers):
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    r = client.patch(f"/api/v1/admin/cameras/{dev_id}", json={"status": "disabled"}, headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "disabled"


def test_generate_key_returns_raw_once(client, admin_user, admin_auth_headers):
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    r = client.post(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["raw_key"]
    assert data["key"]["status"] == "active"
    # raw_key 不出现在 list 里
    lst = client.get(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers).json()["items"]
    assert "raw_key" not in lst[0]
    assert "key_hash" not in lst[0]


def test_revoke_key(client, admin_user, admin_auth_headers):
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    key_id = client.post(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers).json()["key"]["id"]
    r = client.post(f"/api/v1/admin/cameras/{dev_id}/keys/{key_id}/revoke", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "revoked"


def test_revoked_key_fails_intake_auth(client, admin_user, admin_auth_headers, tmp_path, monkeypatch):
    """端到端：撤销 Key 后 /intakes/camera-captures 鉴权 401（张浩-7 + 张浩-9 衔接）。"""
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    gen = client.post(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers).json()
    raw, key_id = gen["raw_key"], gen["key"]["id"]
    # 撤销前能抓拍
    r1 = client.post("/api/v1/intakes/camera-captures", headers={"X-Camera-Key": raw},
                     files={"image": ("a.jpg", JPEG, "image/jpeg")}, data={"location_text": "A"})
    assert r1.status_code == 200
    # 撤销后 401
    client.post(f"/api/v1/admin/cameras/{dev_id}/keys/{key_id}/revoke", headers=admin_auth_headers)
    r2 = client.post("/api/v1/intakes/camera-captures", headers={"X-Camera-Key": raw},
                     files={"image": ("a.jpg", JPEG, "image/jpeg")}, data={"location_text": "A"})
    assert r2.status_code == 401
```

- [ ] **Step 2: 跑，确认 FAIL（路由未挂载，404）**

Run: `cd backend && python -m pytest tests/api/test_cameras_api.py -v`
Expected: FAIL（404）。

- [ ] **Step 3: 写 `app/api/v1/cameras.py`**

```python
# app/api/v1/cameras.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.camera import (
    CameraDeviceCreateIn,
    CameraDeviceListResponse,
    CameraDeviceOut,
    CameraDeviceUpdateIn,
    CameraKeyCreateOut,
    CameraKeyListResponse,
    CameraKeyOut,
)
from app.services.camera_service import CameraService

router = APIRouter(prefix="/admin/cameras", tags=["cameras"])


@router.post("", response_model=CameraDeviceOut, status_code=201)
def create_device(body: CameraDeviceCreateIn,
                  db: Session = Depends(get_db),
                  _: User = Depends(require_role("admin"))) -> CameraDeviceOut:
    dev = CameraService(db).create_device(device_code=body.device_code, location_text=body.location_text)
    return CameraDeviceOut.model_validate(dev)


@router.get("", response_model=CameraDeviceListResponse)
def list_devices(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 db: Session = Depends(get_db),
                 _: User = Depends(require_role("admin"))) -> CameraDeviceListResponse:
    res = CameraService(db).list_devices(page=page, page_size=page_size)
    return CameraDeviceListResponse(
        items=[CameraDeviceOut.model_validate(d) for d in res["items"]],
        total=res["total"], page=res["page"], page_size=res["page_size"],
    )


@router.get("/{device_id}", response_model=CameraDeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> CameraDeviceOut:
    return CameraDeviceOut.model_validate(CameraService(db).get_device(device_id))


@router.patch("/{device_id}", response_model=CameraDeviceOut)
def update_device(device_id: int, body: CameraDeviceUpdateIn,
                  db: Session = Depends(get_db),
                  _: User = Depends(require_role("admin"))) -> CameraDeviceOut:
    dev = CameraService(db).update_device(device_id, location_text=body.location_text, status=body.status)
    return CameraDeviceOut.model_validate(dev)


@router.post("/{device_id}/keys", response_model=CameraKeyCreateOut, status_code=201)
def create_key(device_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> CameraKeyCreateOut:
    raw, key = CameraService(db).create_key(device_id)
    return CameraKeyCreateOut(raw_key=raw, key=CameraKeyOut.model_validate(key))


@router.get("/{device_id}/keys", response_model=CameraKeyListResponse)
def list_keys(device_id: int, db: Session = Depends(get_db),
              _: User = Depends(require_role("admin"))) -> CameraKeyListResponse:
    keys = CameraService(db).list_keys(device_id)
    return CameraKeyListResponse(items=[CameraKeyOut.model_validate(k) for k in keys])


@router.post("/{device_id}/keys/{key_id}/revoke", response_model=CameraKeyOut)
def revoke_key(device_id: int, key_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> CameraKeyOut:
    key = CameraService(db).revoke_key(device_id, key_id)
    return CameraKeyOut.model_validate(key)
```

- [ ] **Step 4: 改 `app/api/v1/router.py`，挂载 cameras.router**

先 Read 该文件。把 `from app.api.v1 import auth, cases, intakes, statistics, violations` 改为：
```python
from app.api.v1 import auth, cameras, cases, intakes, statistics, violations
```
在 `api_router.include_router(statistics.router)` 之后追加：
```python
api_router.include_router(cameras.router)
```

- [ ] **Step 5: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/api/test_cameras_api.py -v`
Expected: 9 passed。

- [ ] **Step 6: 提交**

```bash
git add backend/app/api/v1/cameras.py backend/app/api/v1/router.py backend/tests/api/test_cameras_api.py
git commit -m "feat(camera): /api/v1/admin/cameras 7 路由 + 挂载"
```

---

## Task 5: 全量回归 + 自检

- [ ] **Step 1: 全量跑**

Run: `cd backend && python -m pytest -v`
Expected: 全绿。数量 = 111（基线）+ 5（schemas）+ 11（service）+ 9（api）= 136 passed。

- [ ] **Step 2: 自检清单**

- [ ] 7 个 `/api/v1/admin/cameras/*` 路由可用，强类型响应。
- [ ] 全部 `require_role("admin")`；无 token→401、reviewer/citizen→403、admin→200。
- [ ] 软删：设备 disable（status=disabled）、Key revoke（status=revoked），无硬删。
- [ ] Key 生成：raw 返回一次，key_hash=sha256(raw)，list 不含 raw/key_hash。
- [ ] 撤销的 Key 在 `/intakes/camera-captures` 鉴权 401（张浩-7 + 张浩-9 衔接）。
- [ ] 未动杨翼代码：`git diff main -- backend/app/api/v1/violations.py backend/app/api/v1/cases.py backend/app/api/v1/intakes.py backend/app/services/violation_service.py backend/app/services/case_service.py backend/app/services/intake_service.py backend/app/core/deps.py` 应为空（只 router.py 加挂载）。

- [ ] **Step 3: 若有零散改动，收尾提交**

```bash
git add -A
git commit -m "test(camera): 全量回归通过"
```
（若无改动则跳过。）

---

## 自检（计划层面）

- **Spec 覆盖**：7 路由（Task 4）✅；schemas（Task 1）✅；service + Key 生成 secrets+sha256（Task 3）✅；admin fixtures（Task 2）✅；鉴权 require_role("admin")（Task 4）✅；软删（Task 3 status）✅；撤销→鉴权失效端到端（Task 4 test_revoked_key_fails_intake_auth）✅。不做硬删/key_prefix/模型改动（§不做）✅。
- **占位符**：无 TBD/TODO，每步有完整代码。
- **类型一致**：`CameraDeviceOut`/`CameraKeyOut`/`CameraKeyCreateOut` 等字段在 schemas（Task1）、service（Task3）、routes（Task4）一致；`CameraService.create_device/list_devices/get_device/update_device/create_key/list_keys/revoke_key` 签名在 service（Task3）与 routes（Task4）调用一致；conftest fixture 名 `admin_user`/`admin_auth_headers`（Task2 定义，Task4 使用）一致。
