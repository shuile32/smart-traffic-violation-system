# 张浩-10 内部 AI 接口层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 upstream 新基线上实现 spec §6.2 的 4 个 `/internal/ai` 路由（yolo/detect、ocr/plate、rules/evaluate、review/text）+ ABC 接口 + stub 实现 + DI 工厂，强类型响应，鉴权到位，TDD。

**Architecture:** `app/ai/adapters/base.py`（ABC+dataclass）+ `stub.py`（4 stub）+ `providers.py`（按 `AI_PROVIDER` 选实现的 DI 工厂）+ `routes.py`（4 路由，Depends 注入 adapter）+ `app/schemas/ai.py`（Pydantic 响应）+ `main.py` 挂载。real AI 实现等唐高鹏，本任务只 stub。

**Tech Stack:** FastAPI、Pydantic v2、SQLAlchemy（仅鉴权依赖用）、pytest + TestClient（SQLite 内存，复用队友 conftest）。

**分支：** `zhanghao/internal-ai`（off upstream/main，基线 32 passed）。跑测试：`cd backend && python -m pytest ...`。

**已确认的队友基线事实（写代码直接用）：**
- 鉴权：`from app.core.deps import require_role`；`user: User = Depends(require_role("admin","reviewer"))`。无 token→401，角色不足→403。
- conftest fixtures（`tests/conftest.py`）：`client`/`db`/`seeded_roles`/`citizen_user`/`citizen_token`/`auth_headers`（citizen）。本计划 Task 3 补 reviewer fixtures。
- `app/core/config.py` 的 `Settings` 类，`settings` 实例。
- 强类型响应：`response_model=XxxOut`，跟 `app/schemas/auth.py` 风格。
- `app/main.py`：`app = FastAPI(...)` + `app.include_router(api_router)` + `/health`。

---

## Task 1: ABC 接口 + dataclass（`app/ai/adapters/base.py`）

**Files:**
- Create: `backend/app/ai/__init__.py`（空）
- Create: `backend/app/ai/adapters/__init__.py`（空）
- Create: `backend/app/ai/adapters/base.py`
- Create: `backend/tests/ai/__init__.py`（空）
- Test: `backend/tests/ai/test_base.py`

- [ ] **Step 1: 写测试 `tests/ai/test_base.py`**

```python
from app.ai.adapters.base import (
    AIReviewResultData,
    DetectionResult,
    RuleResult,
)


def test_detection_result_construction():
    r = DetectionResult(
        objects=[{"label": "car"}],
        vehicle_bbox=[1, 2, 3, 4],
        plate_bbox=None,
        annotated_image_path=None,
        model_version="stub",
    )
    assert r.objects == [{"label": "car"}]
    assert r.vehicle_bbox == [1, 2, 3, 4]


def test_rule_result_construction():
    r = RuleResult(
        candidate_violation_type="speed",
        rule_code="speed",
        rule_matched=True,
        evidence_level="complete",
        evidence_items=["超速"],
        missing_evidence=[],
        reason="ok",
    )
    assert r.rule_matched is True
    assert r.evidence_level == "complete"


def test_ai_review_result_data_construction():
    r = AIReviewResultData(
        conclusion="suggest_approve",
        ai_confidence=0.9,
        reason="ok",
        risk_points=[],
        missing_evidence=[],
        prompt_version="v1",
    )
    assert r.conclusion == "suggest_approve"
```

- [ ] **Step 2: 跑，确认 FAIL（模块不存在）**

Run: `cd backend && python -m pytest tests/ai/test_base.py -v`
Expected: FAIL — `ModuleNotFoundError: app.ai.adapters.base`

- [ ] **Step 3: 写 `app/ai/adapters/base.py`**

```python
"""AI 组件抽象接口 — 可插拔，每组件一套实现，后期可换。

real 实现由唐高鹏交付（YOLOv8/OCR/规则引擎/LLM），张浩-10 提供 stub + 路由。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DetectionResult:
    objects: list[dict]  # [{label, confidence, bbox}, ...]
    vehicle_bbox: list[int] | None  # [x1, y1, x2, y2]
    plate_bbox: list[int] | None
    annotated_image_path: str | None
    model_version: str


@dataclass
class RuleResult:
    candidate_violation_type: str | None
    rule_code: str | None
    rule_matched: bool
    evidence_level: str  # complete / partial / insufficient
    evidence_items: list[str]
    missing_evidence: list[str]
    reason: str


@dataclass
class AIReviewResultData:
    conclusion: str  # suggest_approve / need_review / suggest_reject
    ai_confidence: float | None
    reason: str
    risk_points: list[str]
    missing_evidence: list[str]
    prompt_version: str


class YoloDetector(ABC):
    @abstractmethod
    def detect(self, image_path: str) -> DetectionResult: ...


class OcrEngine(ABC):
    @abstractmethod
    def recognize_plate(self, plate_crop_path: str) -> str | None: ...


class RuleEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        detection: DetectionResult,
        ocr_result: str | None,
        intake_event: dict,
        rule: dict,
    ) -> RuleResult: ...


class LLMProvider(ABC):
    @abstractmethod
    def review(self, evidence_payload: dict) -> AIReviewResultData: ...
```

- [ ] **Step 4: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/ai/test_base.py -v`
Expected: 3 passed。

- [ ] **Step 5: 提交**

```bash
git add backend/app/ai/__init__.py backend/app/ai/adapters/__init__.py backend/app/ai/adapters/base.py backend/tests/ai/__init__.py backend/tests/ai/test_base.py
git commit -m "feat(ai): ABC 接口 + dataclass（张浩-10 地基）"
```

---

## Task 2: 4 个 stub 实现 + 测试（TDD）

**Files:**
- Create: `backend/app/ai/adapters/stub.py`
- Test: `backend/tests/ai/test_stubs.py`

- [ ] **Step 1: 写测试 `tests/ai/test_stubs.py`**

```python
from app.ai.adapters.base import DetectionResult
from app.ai.adapters.stub import (
    StubLLMProvider,
    StubOcrEngine,
    StubRuleEvaluator,
    StubYoloDetector,
)


def test_stub_yolo_detect():
    r = StubYoloDetector().detect("/any.jpg")
    assert r.model_version == "stub-yolov8n"
    assert any(o["label"] == "car" for o in r.objects)
    assert r.vehicle_bbox is not None
    assert r.plate_bbox is not None


def test_stub_ocr_recognize_plate():
    assert StubOcrEngine().recognize_plate("/any.jpg") == "京A12345"


def _det():
    return DetectionResult(
        objects=[], vehicle_bbox=None, plate_bbox=None,
        annotated_image_path=None, model_version="",
    )


def test_stub_rule_speed_matched():
    r = StubRuleEvaluator().evaluate(
        detection=_det(),
        ocr_result="京A12345",
        intake_event={"speed": 120},
        rule={"rule_type": "speed", "speed_limit": 80, "rule_code": "speed"},
    )
    assert r.rule_matched is True
    assert r.evidence_level == "complete"
    assert r.candidate_violation_type == "speed"


def test_stub_rule_speed_not_matched():
    r = StubRuleEvaluator().evaluate(
        detection=_det(),
        ocr_result=None,
        intake_event={"speed": 50},
        rule={"rule_type": "speed", "speed_limit": 80, "rule_code": "speed"},
    )
    assert r.rule_matched is False


def test_stub_rule_unknown_type():
    r = StubRuleEvaluator().evaluate(
        detection=_det(),
        ocr_result=None,
        intake_event={},
        rule={"rule_type": "no_parking", "rule_code": "np"},
    )
    assert r.rule_matched is False
    assert r.evidence_level == "insufficient"


def test_stub_llm_review():
    r = StubLLMProvider().review({"any": "evidence"})
    assert r.conclusion == "suggest_approve"
    assert r.ai_confidence == 0.88
    assert r.prompt_version == "stub-v1"
```

- [ ] **Step 2: 跑，确认 FAIL（stub 模块不存在）**

Run: `cd backend && python -m pytest tests/ai/test_stubs.py -v`
Expected: FAIL — `ModuleNotFoundError: app.ai.adapters.stub`

- [ ] **Step 3: 写 `app/ai/adapters/stub.py`**

```python
"""Stub AI 实现 — 返回写实固定数据，供管线联调。

real 实现由唐高鹏交付后接入 providers.py 的工厂分支，不改路由。
"""
from app.ai.adapters.base import (
    AIReviewResultData,
    DetectionResult,
    LLMProvider,
    OcrEngine,
    RuleEvaluator,
    RuleResult,
    YoloDetector,
)


class StubYoloDetector(YoloDetector):
    def detect(self, image_path: str) -> DetectionResult:
        return DetectionResult(
            objects=[{"label": "car", "confidence": 0.92, "bbox": [100, 200, 300, 350]}],
            vehicle_bbox=[100, 200, 300, 350],
            plate_bbox=[120, 230, 200, 270],
            annotated_image_path=image_path,
            model_version="stub-yolov8n",
        )


class StubOcrEngine(OcrEngine):
    def recognize_plate(self, plate_crop_path: str) -> str | None:
        return "京A12345"


class StubRuleEvaluator(RuleEvaluator):
    def evaluate(self, detection, ocr_result, intake_event, rule) -> RuleResult:
        rule_type = rule.get("rule_type")
        if rule_type == "speed":
            speed = intake_event.get("speed")
            limit = rule.get("speed_limit")
            matched = speed is not None and limit is not None and speed > limit
            return RuleResult(
                candidate_violation_type="speed" if matched else None,
                rule_code=rule.get("rule_code", "speed"),
                rule_matched=matched,
                evidence_level="complete" if matched else "insufficient",
                evidence_items=[f"车速{speed}，限速{limit}"] if matched else [],
                missing_evidence=[] if matched else ["车速或限速缺失"],
                reason="超速判定" if matched else "速度数据不足",
            )
        if rule_type == "special_lane":
            return RuleResult(
                candidate_violation_type="special_lane",
                rule_code=rule.get("rule_code", "special_lane"),
                rule_matched=True,
                evidence_level="complete",
                evidence_items=["检测到车辆", "车辆位于专用车道ROI内"],
                missing_evidence=[],
                reason="占用专用车道（stub 简化：默认匹配）",
            )
        return RuleResult(
            candidate_violation_type=None,
            rule_code=rule.get("rule_code"),
            rule_matched=False,
            evidence_level="insufficient",
            evidence_items=[],
            missing_evidence=[f"未知 rule_type: {rule_type}"],
            reason="未知规则",
        )


class StubLLMProvider(LLMProvider):
    def review(self, evidence_payload: dict) -> AIReviewResultData:
        return AIReviewResultData(
            conclusion="suggest_approve",
            ai_confidence=0.88,
            reason="stub: 证据链完整，建议通过",
            risk_points=[],
            missing_evidence=[],
            prompt_version="stub-v1",
        )
```

- [ ] **Step 4: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/ai/test_stubs.py -v`
Expected: 6 passed。

- [ ] **Step 5: 提交**

```bash
git add backend/app/ai/adapters/stub.py backend/tests/ai/test_stubs.py
git commit -m "feat(ai): 4 个 stub 实现 + 测试"
```

---

## Task 3: config + schemas + providers + reviewer fixtures

**Files:**
- Modify: `backend/app/core/config.py`（加 `AI_PROVIDER`）
- Create: `backend/app/schemas/ai.py`
- Create: `backend/app/ai/providers.py`
- Modify: `backend/tests/conftest.py`（加 reviewer fixtures）

- [ ] **Step 1: 改 `app/core/config.py`，在 `ALLOWED_IMAGE_TYPES` 行后加一行**

在 `ALLOWED_IMAGE_TYPES: tuple[str, ...] = (...)` 之后加：
```python
    AI_PROVIDER: str = "stub"  # stub | real（real 等 唐 高鹏 交付）
```

- [ ] **Step 2: 写 `app/schemas/ai.py`**

```python
from pydantic import BaseModel


class DetectionOut(BaseModel):
    objects: list[dict]
    vehicle_bbox: list[int] | None
    plate_bbox: list[int] | None
    annotated_image_url: str | None
    model_version: str


class OcrOut(BaseModel):
    plate_no: str | None


class RuleEvalOut(BaseModel):
    rule_matched: bool
    evidence_level: str
    evidence_items: list[str]
    reason: str


class ReviewOut(BaseModel):
    conclusion: str
    ai_confidence: float | None
    reason: str
```

- [ ] **Step 3: 写 `app/ai/providers.py`**

```python
"""AI adapter DI 工厂。按 settings.AI_PROVIDER 选实现。

唐高鹏交付 real 实现后，在各工厂加 elif 分支返回 real 类，不改路由。
"""
from app.ai.adapters.base import (
    LLMProvider,
    OcrEngine,
    RuleEvaluator,
    YoloDetector,
)
from app.ai.adapters.stub import (
    StubLLMProvider,
    StubOcrEngine,
    StubRuleEvaluator,
    StubYoloDetector,
)
from app.core.config import settings


def _provider_not_supported() -> Exception:
    return NotImplementedError(f"AI_PROVIDER={settings.AI_PROVIDER} 暂未支持")


def get_yolo_detector() -> YoloDetector:
    if settings.AI_PROVIDER == "stub":
        return StubYoloDetector()
    raise _provider_not_supported()


def get_ocr_engine() -> OcrEngine:
    if settings.AI_PROVIDER == "stub":
        return StubOcrEngine()
    raise _provider_not_supported()


def get_rule_evaluator() -> RuleEvaluator:
    if settings.AI_PROVIDER == "stub":
        return StubRuleEvaluator()
    raise _provider_not_supported()


def get_llm_provider() -> LLMProvider:
    if settings.AI_PROVIDER == "stub":
        return StubLLMProvider()
    raise _provider_not_supported()
```

- [ ] **Step 4: 改 `tests/conftest.py`，在 `auth_headers` fixture 之后追加 reviewer 三件套**

在 `def auth_headers(...)` 函数之后追加：
```python
@pytest.fixture()
def reviewer_user(db: Session, seeded_roles) -> User:
    user = User(
        username="reviewer1",
        password_hash=hash_password("pass1234"),
        email="reviewer@example.com",
        role_id=seeded_roles["reviewer"].id,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def reviewer_token(reviewer_user: User) -> str:
    return create_access_token(subject=str(reviewer_user.id), role="reviewer")


@pytest.fixture()
def reviewer_auth_headers(reviewer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {reviewer_token}"}
```

- [ ] **Step 5: 跑既有测试确认无回归**

Run: `cd backend && python -m pytest -q`
Expected: 32 passed（本任务只加配置/类型/fixture，无新测试，数量不变）。

- [ ] **Step 6: 提交**

```bash
git add backend/app/core/config.py backend/app/schemas/ai.py backend/app/ai/providers.py backend/tests/conftest.py
git commit -m "feat(ai): config AI_PROVIDER + schemas + DI 工厂 + reviewer fixtures"
```

---

## Task 4: 路由 yolo/detect + ocr/plate + main 挂载（TDD）

**Files:**
- Create: `backend/app/ai/routes.py`
- Modify: `backend/app/main.py`（挂载 internal_router）
- Test: `backend/tests/ai/test_routes.py`

- [ ] **Step 1: 写测试 `tests/ai/test_routes.py`（yolo + ocr 部分）**

```python
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_yolo_detect_requires_auth(client):
    resp = client.post(
        "/internal/ai/yolo/detect",
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 401


def test_yolo_detect_citizen_forbidden(client, citizen_user, auth_headers):
    resp = client.post(
        "/internal/ai/yolo/detect",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 403


def test_yolo_detect_success(client, reviewer_user, reviewer_auth_headers):
    resp = client.post(
        "/internal/ai/yolo/detect",
        headers=reviewer_auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_version"] == "stub-yolov8n"
    assert any(o["label"] == "car" for o in data["objects"])
    assert data["vehicle_bbox"] is not None


def test_ocr_plate_success(client, reviewer_user, reviewer_auth_headers):
    resp = client.post(
        "/internal/ai/ocr/plate",
        headers=reviewer_auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["plate_no"] == "京A12345"


def test_ocr_plate_requires_auth(client):
    resp = client.post(
        "/internal/ai/ocr/plate",
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 401
```

- [ ] **Step 2: 跑，确认 FAIL（路由未挂载，404）**

Run: `cd backend && python -m pytest tests/ai/test_routes.py -v`
Expected: FAIL — 路由 404 或模块不存在。

- [ ] **Step 3: 写 `app/ai/routes.py`（先 yolo + ocr 两路由）**

```python
"""内部 AI 接口路由 — 无状态探测，对接 AI adapter。"""
import os
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile

from app.ai.adapters.base import DetectionResult
from app.ai.providers import (
    get_llm_provider,
    get_ocr_engine,
    get_rule_evaluator,
    get_yolo_detector,
)
from app.core.deps import require_role
from app.models.user import User
from app.schemas.ai import DetectionOut, OcrOut

internal_router = APIRouter(prefix="/internal/ai", tags=["internal-ai"])


def _save_upload(image: UploadFile) -> str:
    suffix = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(image.file.read())
    tmp.close()
    return tmp.name


@internal_router.post("/yolo/detect", response_model=DetectionOut)
def yolo_detect(
    image: UploadFile = File(...),
    detector=Depends(get_yolo_detector),
    _: User = Depends(require_role("admin", "reviewer")),
) -> DetectionOut:
    path = _save_upload(image)
    try:
        r = detector.detect(path)
    finally:
        os.unlink(path)
    return DetectionOut(
        objects=r.objects,
        vehicle_bbox=r.vehicle_bbox,
        plate_bbox=r.plate_bbox,
        annotated_image_url=r.annotated_image_path,
        model_version=r.model_version,
    )


@internal_router.post("/ocr/plate", response_model=OcrOut)
def ocr_plate(
    image: UploadFile = File(...),
    engine=Depends(get_ocr_engine),
    _: User = Depends(require_role("admin", "reviewer")),
) -> OcrOut:
    path = _save_upload(image)
    try:
        plate = engine.recognize_plate(path)
    finally:
        os.unlink(path)
    return OcrOut(plate_no=plate)
```

- [ ] **Step 4: 改 `app/main.py`，挂载 internal_router**

把 `app/main.py` 改为：
```python
from fastapi import FastAPI

from app.ai.routes import internal_router
from app.api.v1.router import api_router

app = FastAPI(title="交通违章智能管理平台 API")
app.include_router(api_router)
app.include_router(internal_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/ai/test_routes.py -v`
Expected: 5 passed。

- [ ] **Step 6: 提交**

```bash
git add backend/app/ai/routes.py backend/app/main.py backend/tests/ai/test_routes.py
git commit -m "feat(ai): /internal/ai yolo/detect + ocr/plate 路由"
```

---

## Task 5: 路由 rules/evaluate + review/text（TDD）

**Files:**
- Modify: `backend/app/ai/routes.py`（追加 2 路由）
- Modify: `backend/tests/ai/test_routes.py`（追加测试）
- Modify: `backend/app/schemas/ai.py`（无改动，已含 RuleEvalOut/ReviewOut；只确认 import）

- [ ] **Step 1: 在 `tests/ai/test_routes.py` 末尾追加测试**

```python
def test_rules_evaluate_speed_matched(client, reviewer_user, reviewer_auth_headers):
    body = {
        "detection": {"objects": [], "vehicle_bbox": None, "plate_bbox": None, "annotated_image_url": None, "model_version": ""},
        "ocr_result": "京A12345",
        "intake_event": {"speed": 120},
        "rule": {"rule_type": "speed", "speed_limit": 80, "rule_code": "speed"},
    }
    resp = client.post("/internal/ai/rules/evaluate", headers=reviewer_auth_headers, json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["rule_matched"] is True
    assert data["evidence_level"] == "complete"


def test_rules_evaluate_requires_auth(client):
    resp = client.post("/internal/ai/rules/evaluate", json={})
    assert resp.status_code == 401


def test_review_text_success(client, reviewer_user, reviewer_auth_headers):
    resp = client.post(
        "/internal/ai/review/text",
        headers=reviewer_auth_headers,
        json={"evidence": "any"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["conclusion"] == "suggest_approve"
    assert data["ai_confidence"] == 0.88


def test_review_text_citizen_forbidden(client, citizen_user, auth_headers):
    resp = client.post("/internal/ai/review/text", headers=auth_headers, json={})
    assert resp.status_code == 403
```

- [ ] **Step 2: 跑，确认 FAIL（路由未实现，404）**

Run: `cd backend && python -m pytest tests/ai/test_routes.py -v`
Expected: 新 4 条 FAIL（404），已有 5 条 PASS。

- [ ] **Step 3: 在 `app/ai/routes.py` 追加 2 路由 + 补 import**

在文件顶部 import 区把 `RuleEvalOut, ReviewOut` 加进 `app.schemas.ai` 的 import：
```python
from app.schemas.ai import DetectionOut, OcrOut, ReviewOut, RuleEvalOut
```
在文件末尾追加：
```python
@internal_router.post("/rules/evaluate", response_model=RuleEvalOut)
def rules_evaluate(
    body: dict,
    evaluator=Depends(get_rule_evaluator),
    _: User = Depends(require_role("admin", "reviewer")),
) -> RuleEvalOut:
    detection_data = body.get("detection", {})
    detection = DetectionResult(
        objects=detection_data.get("objects", []),
        vehicle_bbox=detection_data.get("vehicle_bbox"),
        plate_bbox=detection_data.get("plate_bbox"),
        annotated_image_path=detection_data.get("annotated_image_url"),
        model_version=detection_data.get("model_version", ""),
    )
    r = evaluator.evaluate(
        detection=detection,
        ocr_result=body.get("ocr_result"),
        intake_event=body.get("intake_event", {}),
        rule=body.get("rule", {}),
    )
    return RuleEvalOut(
        rule_matched=r.rule_matched,
        evidence_level=r.evidence_level,
        evidence_items=r.evidence_items,
        reason=r.reason,
    )


@internal_router.post("/review/text", response_model=ReviewOut)
def review_text(
    body: dict,
    provider=Depends(get_llm_provider),
    _: User = Depends(require_role("admin", "reviewer")),
) -> ReviewOut:
    r = provider.review(body)
    return ReviewOut(
        conclusion=r.conclusion,
        ai_confidence=r.ai_confidence,
        reason=r.reason,
    )
```

- [ ] **Step 4: 跑，确认 PASS**

Run: `cd backend && python -m pytest tests/ai/test_routes.py -v`
Expected: 9 passed（5 + 4）。

- [ ] **Step 5: 提交**

```bash
git add backend/app/ai/routes.py backend/tests/ai/test_routes.py
git commit -m "feat(ai): /internal/ai rules/evaluate + review/text 路由"
```

---

## Task 6: 全量回归 + 自检

- [ ] **Step 1: 全量跑**

Run: `cd backend && python -m pytest -v`
Expected: 全绿。数量 = 32（基线）+ 3（test_base）+ 6（test_stubs）+ 9（test_routes）= 50 passed。

- [ ] **Step 2: 自检清单**

- [ ] 4 个 `/internal/ai/*` 路由可用，强类型响应（`response_model`）。
- [ ] 全部路由 `require_role("admin","reviewer")` 鉴权；无 token→401、citizen→403、reviewer→200。
- [ ] `AI_PROVIDER=stub` 默认；`providers.py` 工厂按 env 选实现。
- [ ] 未装 ultralytics/paddleocr/openai（stub 不依赖）。
- [ ] 未动 intakes/services/auth 等队友代码（`git diff upstream/main -- backend/app/api backend/app/services backend/app/core` 应只含 `config.py` 的 `AI_PROVIDER` 一行）。

- [ ] **Step 3: 若有零散改动，收尾提交**

```bash
git add -A
git commit -m "test(ai): 全量回归通过"
```
（若无改动则跳过。）

---

## 自检（计划层面）

- **Spec 覆盖**：§6.2 的 4 路由（Task 4-5）✅；§7 ABC 接口（Task 1）✅；stub 实现（Task 2）✅；DI 工厂（Task 3）✅；强类型响应（Task 3 schemas）✅；鉴权（Task 4-5 require_role）✅；测试（Task 1/2/4/5）✅。§6.3 /review/vision 明确不做 ✅。
- **占位符**：无 TBD/TODO，每步有完整代码。
- **类型一致**：`DetectionResult`/`RuleResult`/`AIReviewResultData` 字段在 base（Task1）、stub（Task2）、routes（Task4-5）一致；`DetectionOut` 等在 schemas（Task3）与 routes（Task4-5）一致；fixture 名 `reviewer_auth_headers`（Task3 定义，Task4-5 使用）一致。
