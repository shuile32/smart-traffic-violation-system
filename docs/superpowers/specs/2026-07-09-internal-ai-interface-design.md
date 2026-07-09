# 张浩-10 内部 AI 接口层 · Design Spec

## 背景

团队第一阶段 spec（`docs/superpowers/specs/2026-07-08-交通违章平台-第一阶段开发方案-design.md`）§6.2 把内部 AI 路由列为 IN-scope：`POST /internal/ai/yolo/detect`、`/ocr/plate`、`/rules/evaluate`、`/review/text`。§6.3 推迟 `/internal/ai/review/vision`（多模态复核）。

分工（`docs/团队任务分工.md`）张浩-10 = 内部 AI 接口层；AI 实现本身（YOLOv8/OCR/规则引擎/LLM）归唐高鹏（唐高鹏-7/8/9/11）。故本任务边界 = **HTTP 路由 + ABC 接口 + stub 实现 + DI 工厂**，真实 AI 实现等唐高鹏交付后插入，不改路由。

upstream 现状（队友 M0-M2 地基）无 `app/ai/` 目录，需从零建。基线约定：强类型 Pydantic 响应、`app/services/` 服务层、`app/core/deps.py` 依赖注入、SQLite 内存测试、无 Celery。

## 范围

**IN（4 路由）：**
- `POST /internal/ai/yolo/detect` —— 上传图片，返回检测结果
- `POST /internal/ai/ocr/plate` —— 上传车牌裁剪图，返回车牌号
- `POST /internal/ai/rules/evaluate` —— JSON（detection + ocr + intake_event + rule），返回规则判定
- `POST /internal/ai/review/text` —— JSON（evidence），返回 LLM 初审意见

**OUT：**
- `/internal/ai/review/vision`（多模态复核，§6.3 推迟）
- real AI 实现（ultralytics/paddleocr/openai 不装不碰，等唐高鹏）
- DB 持久化（/internal/ai 是无状态探测接口，不写表）
- Celery（本任务无异步）

## 架构

```
backend/app/ai/
├── __init__.py
├── adapters/
│   ├── __init__.py
│   ├── base.py     # ABC + dataclass（从旧代码 app/ai/adapters/base.py 搬运复用）
│   └── stub.py     # StubYoloDetector / StubOcrEngine / StubRuleEvaluator / StubLLMProvider
├── providers.py    # DI 工厂：get_yolo_detector()/get_ocr_engine()/get_rule_evaluator()/get_llm_provider()
└── routes.py       # internal_router，4 路由，Depends 注入 adapter
backend/app/schemas/ai.py   # DetectionOut / OcrOut / RuleEvalOut / ReviewOut
backend/app/main.py         # 挂载 internal_router 到 /internal/ai
backend/app/core/config.py  # 新增 AI_PROVIDER: str = "stub"
```

遵循 spec §7 的 `app/ai/adapters/base.py` 路径（AI 是独立关注点，与队友 `app/services/` 业务服务区分）。

## 组件

### `app/ai/adapters/base.py`（复用旧设计）
ABC + dataclass：
- `DetectionResult`（objects/vehicle_bbox/plate_bbox/annotated_image_url/model_version）
- `RuleResult`（candidate_violation_type/rule_code/rule_matched/evidence_level/evidence_items/missing_evidence/reason）
- `AIReviewResultData`（conclusion/ai_confidence/reason/risk_points/missing_evidence/prompt_version）
- `YoloDetector.detect(image_path) -> DetectionResult`
- `OcrEngine.recognize_plate(plate_crop_path) -> str | None`
- `RuleEvaluator.evaluate(detection, ocr_result, intake_event, rule) -> RuleResult`
- `LLMProvider.review(evidence_payload) -> AIReviewResultData`

（`NotificationProvider` 不在本任务，留给杨翼-8 通知模块。）

### `app/ai/adapters/stub.py`
4 个 stub 实现，返回**写实固定数据**（让端到端管线可测）：
- `StubYoloDetector.detect` → 1 辆 car（confidence 0.92）+ vehicle_bbox + plate_bbox + model_version="stub-yolov8n"
- `StubOcrEngine.recognize_plate` → "京A12345"
- `StubRuleEvaluator.evaluate` → 按 rule 的 rule_type 走超速/专用车道简易判定，返回 rule_matched + evidence
- `StubLLMProvider.review` → conclusion="suggest_approve", ai_confidence=0.88

### `app/ai/providers.py`
工厂函数，按 `settings.AI_PROVIDER` 选实现：
```python
def get_yolo_detector() -> YoloDetector:
    if settings.AI_PROVIDER == "stub":
        return StubYoloDetector()
    # 唐高鹏交付后：elif settings.AI_PROVIDER == "real": return UltralyticsYoloDetector()
    raise NotImplementedError(...)
```
4 个 adapter 各一个工厂。路由用 `Depends(get_yolo_detector)` 等注入。

### `app/ai/routes.py`
`internal_router = APIRouter(prefix="/internal/ai", tags=["internal-ai"])`，4 路由：
- 全部 `Depends(require_role("admin", "reviewer"))` 鉴权
- yolo/detect、ocr/plate 收 `UploadFile`；rules/evaluate、review/text 收 JSON dict
- 调 adapter，返回强类型 Pydantic 响应

### `app/schemas/ai.py`
- `DetectionOut`：objects(list[dict]) + vehicle_bbox + plate_bbox + annotated_image_url + model_version
- `OcrOut`：plate_no (str | None)
- `RuleEvalOut`：rule_matched + evidence_level + evidence_items + reason
- `ReviewOut`：conclusion + ai_confidence + reason

### `app/main.py`
加 `app.include_router(internal_router)`（prefix 已在 router 上）。

## 数据流

`POST /internal/ai/yolo/detect`：图片 → 存临时文件 → `detector.detect(path)` → `DetectionOut`。
`POST /internal/ai/ocr/plate`：车牌图 → 存临时文件 → `engine.recognize_plate(path)` → `OcrOut`。
`POST /internal/ai/rules/evaluate`：JSON body → 构造 DetectionResult + dicts → `evaluator.evaluate(...)` → `RuleEvalOut`。
`POST /internal/ai/review/text`：JSON body → `provider.review(payload)` → `ReviewOut`。

## 鉴权

全部 `require_role("admin", "reviewer")`（复用 `app/core/deps.py`）。无 token → 401；角色不足 → 403。

## 错误处理

stub 不会失败（返回固定数据）。real 实现就绪后，adapter 内部异常由全局 HTTPException 处理器兜底（upstream main.py 暂无信封，走默认 `{"detail":...}`）。本任务不引入新错误处理约定。

## 测试策略（TDD）

`backend/tests/ai/`（新建）：
- `test_routes.py`：4 路由各测 happy path（默认 stub，断言固定输出字段）+ 鉴权（无 token 401 / citizen 403 / reviewer 200）。
- `test_stubs.py`：4 个 stub 单元测试，确认返回结构契约（DetectionResult/RuleResult/AIReviewResultData 字段齐全）。

复用 `tests/conftest.py` 的 `client`/`citizen_user`/`auth_headers` fixtures。stub 路由测试不需 DB（无状态），但 `client` fixture 依赖 `db`——沿用即可（建空表无开销）。

临时文件：yolo/ocr 路由存临时图，测试用 `tmp_path` + monkeypatch 或直接用 `UploadFile` 内存字节（stub 不真读文件内容，固定返回，故无需真存盘——stub 实现可忽略 image_path 参数）。

## 成功标准

- `cd backend && python -m pytest -q` 全绿（此分支基线 32 + 本任务新增约 8-10；张浩-9 在独立分支不在此基线）。
- 4 个 `/internal/ai/*` 路由可用，强类型响应，鉴权到位。
- `AI_PROVIDER=stub` 默认，端到端管线（intake→AI）可用固定输出跑通。
- 唐高鹏交付 real 实现后，只需在 `providers.py` 加 `elif` 分支，不改路由/测试。

## 不做

- real AI 实现（ultralytics/paddleocr/openai）。
- `/review/vision`。
- DB 持久化、Celery。
- 不动 intakes/services/auth 等队友代码。
- 不做 NotificationProvider（杨翼-8）。
