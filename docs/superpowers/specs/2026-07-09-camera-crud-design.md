# 张浩-7 摄像头设备管理 CRUD · Design Spec

## 背景

分工张浩-7 = 摄像头设备管理 CRUD（设备增删改查 + API Key 生成/吊销）。属第二阶段（spec §6.1 外，运维后台），但模型已就绪，可做。

本地 main（`d175700` + 张浩-5/9/10 + seed polish，111 passed）上：
- `CameraDevice`（`app/models/intake.py`）：id/device_code(unique)/location_text/status(default "enabled")/created_at。
- `CameraApiKey`：id/camera_device_id(FK)/key_hash(String255 unique index)/status(default "active")/created_at。
- 张浩-9 已把摄像头鉴权（`deps.get_camera_device`）改成 sha256 索引查找，按 `status=="active"` + `dev.status=="enabled"` 放行。本任务的 Key 生成要与之衔接：产 raw key + 存 `sha256(raw)`，撤销/停用走 status 软删。

照杨翼 route→service→schemas 模式，强类型 Pydantic 响应、`require_role("admin")`、SQLite 内存测试。

## 范围

**IN：**
- 设备：创建 / 列表（分页）/ 详情 / 改（location_text、status enable/disable）
- Key：生成（raw 返回一次）/ 列表（元数据）/ 撤销（status=revoked）

**OUT：**
- 硬删（设备/Key 都软删，保留审计轨迹、无 FK 问题）
- key_prefix/expires_at/revoked_at（模型没有，YAGNI，不加字段）
- 改 CameraDevice/CameraApiKey 模型
- 级联删
- 不动杨翼代码（只 `router.py` 加挂载）

## 架构

```
backend/app/api/v1/cameras.py        # 路由，require_role("admin")，调 CameraService
backend/app/services/camera_service.py  # CameraService
backend/app/schemas/camera.py        # Pydantic schemas
backend/app/api/v1/router.py         # 挂载 cameras.router
backend/tests/api/test_cameras_api.py
backend/tests/services/test_camera_service.py
```

## 路由（前缀 `/api/v1/admin/cameras`，全部 `require_role("admin")`）

| 方法 | 路径 | 说明 | 响应 |
|------|------|------|------|
| POST | `/admin/cameras` | 建设备（device_code + location_text?） | `CameraDeviceOut`（201）|
| GET | `/admin/cameras` | 列表（page≥1, page_size 1~100） | `CameraDeviceListResponse` |
| GET | `/admin/cameras/{id}` | 详情 | `CameraDeviceOut`（404 不存在）|
| PATCH | `/admin/cameras/{id}` | 改 location_text / status | `CameraDeviceOut` |
| POST | `/admin/cameras/{id}/keys` | 生成 Key | `CameraKeyCreateOut`（raw 一次）|
| GET | `/admin/cameras/{id}/keys` | 列该设备 Key（元数据） | `CameraKeyListResponse` |
| POST | `/admin/cameras/{id}/keys/{key_id}/revoke` | 撤销 Key | `CameraKeyOut` |

**无 DELETE**——设备 disable、Key revoke 都走 status。

## Schemas（`app/schemas/camera.py`）

```python
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
    raw_key: str        # 只在生成时返回一次
    key: CameraKeyOut

class CameraKeyListResponse(BaseModel):
    items: list[CameraKeyOut]
```

## Service（`app/services/camera_service.py`）

`class CameraService: def __init__(self, db)`：
- `create_device(device_code, location_text) -> CameraDevice`：device_code 重复 → raise HTTPException(409)
- `list_devices(page, page_size) -> dict`：{items, total, page, page_size}
- `get_device(device_id) -> CameraDevice`：None → 404
- `update_device(device_id, location_text, status) -> CameraDevice`：None → 404
- `create_key(device_id) -> tuple[str, CameraApiKey]`：产 `raw = secrets.token_urlsafe(32)`，存 `key_hash = sha256(raw).hexdigest()`；设备不存在 → 404
- `list_keys(device_id) -> list[CameraApiKey]`：设备不存在 → 404
- `revoke_key(device_id, key_id) -> CameraApiKey`：设 status="revoked"；不存在或不属于该设备 → 404

## 鉴权

全部 `Depends(require_role("admin"))`。无 token→401、非 admin→403、admin→200。

## 错误处理

- 重复 device_code → 409 "设备编号已存在"
- 设备/Key 不存在 → 404
- 设备不存在时操作 Key → 404（先校验设备）
- status 非法值（非 enabled/disabled）→ 422（Pydantic 不强校验 enum，service 层校验返 400/422；本任务用 400）

## 测试（TDD）

### `tests/services/test_camera_service.py`
- create_device 成功 + 重复 409
- list_devices 分页
- update_device 成功 + 不存在 404
- create_key：raw 返回、key_hash 是 sha256(raw)、设备不存在 404
- revoke_key：status→revoked、不存在 404
- 撤销后的 Key 在张浩-9 的 `get_camera_device` 鉴权里失效（status!=active → 401）

### `tests/api/test_cameras_api.py`
- 设备 CRUD：create/list/get(404)/patch(404) + 鉴权（无 token 401 / reviewer 403 / admin 200）
- Key：generate（raw 返回一次，响应含 raw_key + key 元数据）/ list（无 raw、无 key_hash）/ revoke
- 鉴权：所有路由 admin 200、非 admin 403

复用 conftest 的 `client`/`db`/`seeded_roles`/`reviewer_auth_headers`/`citizen_user`/`auth_headers`。conftest 没有 admin_user——在 conftest 仿 `reviewer_user` 加 `admin_user`/`admin_token`/`admin_auth_headers` 三件套（admin 角色 id 取自 seeded_roles["admin"]）。

## 成功标准

- `cd backend && python -m pytest -q` 全绿（基线 111 + 本任务新增约 15-18）。
- 7 个路由可用，强类型响应，admin 鉴权到位。
- 撤销的 Key / 停用的设备在 `get_camera_device`（张浩-9）里鉴权失效（端到端一致）。
- 不动杨翼代码（`git diff main -- app/api/v1/violations.py app/services/violation_service.py ...` 为空；只 router.py 加挂载）。

## 不做

- 硬删、级联、key_prefix/expires_at、模型改动、杨翼代码。
