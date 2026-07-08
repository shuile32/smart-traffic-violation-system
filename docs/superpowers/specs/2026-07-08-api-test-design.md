# 后端 API 层测试设计 · 2026-07-08

## 目标

为第一阶段后端 `app/api/v1/*`（auth / intakes / cases / violations / statistics）及 `app/core/middleware.py`、`app/core/permissions.py` 补全集成测试，使用 FastAPI `TestClient`，覆盖鉴权（401）、权限（403）、成功路径与主要错误路径（404 / 状态守卫 / 参数校验）。

## 当前障碍

- `app/core/database.py` 默认连 MySQL，`get_db` 为模块级 `SessionLocal`。
- `app/api/v1/intakes.py` 上传后投递 Celery chain：`detect_objects_task → ocr_plate_task → evaluate_rule_task → ai_review_task`。真跑会 `import ultralytics / paddleocr` 并加载模型权重，eager 同步执行会超慢或失败。
- `app/api/v1/cases.py` 的 `request-recheck` 调 `detect_objects_task.delay()`，且未 try/except 包裹。
- `app/core/config.py` 的 `settings` 为 `lru_cache` 模块级单例。

## 关键决策

### DB：真实 MySQL 测试库

- 读环境变量 `TEST_DATABASE_URL`，未设则回退 `mysql+pymysql://root:@localhost:3306/traffic_violation_test`。
- 测试前置：调用方需在本机 MySQL 建好 `traffic_violation_test` 库并赋权。
- conftest 建独立 engine，`Base.metadata.create_all` 建表；每个测试用 session 级事务隔离（rollback / drop），保证用例间干净。

### Celery：monkeypatch 记录而非 eager

**偏离用户最初选择的"eager"，原因**：eager 会同步执行 ML task 链，加载 YOLO/PaddleOCR 权重，测试将超时或报错。API 层测试应验证端点是否正确建库、返回正确响应、是否投递任务，而非 ML 管道本身。

- autouse fixture monkeypatch 以下对象的 `.delay()` 与 `.apply_async()`，改为追加到 `celery_calls` 列表，不执行：
  - `app.tasks.detect_objects_task.detect_objects_task`
  - `app.tasks.ocr_plate_task.ocr_plate_task`
  - `app.tasks.evaluate_rule_task.evaluate_rule_task`
  - `app.tasks.ai_review_task.ai_review_task`
  - `app.tasks.send_notification_task.send_notification_task`
- 测试可断言 `celery_calls` 中是否包含期望投递。

### 其他隔离

- 媒体目录：`MEDIA_STORAGE_DIR` 指到 `tmp_path`，不污染仓库。
- Redis、LLM、SMTP：测试不连，全部 monkeypatch。
- 复用 `main.py` 全局异常 handler，断言按统一响应体 `{code, message, data}` 校验。

## 测试基础设施（`backend/tests/conftest.py`）

- `engine` / `TestingSessionLocal`：由 `TEST_DATABASE_URL` 构建。
- `db_session` fixture：yield session，测试后 rollback + 清表。
- `client` fixture：`TestClient(app)`，`app.dependency_overrides[get_db]` 指向测试 session。
- `patch_celery` autouse fixture：上述 monkeypatch + `celery_calls` 列表。
- `tmp_media_dir` autouse fixture：重定向 `settings.MEDIA_STORAGE_DIR`。
- `auth_header(role, user_id)`：用 `create_access_token` 造 JWT，返回 `{"Authorization": "Bearer ..."}`。
- 种子 fixtures：建 `Role`(admin/reviewer/citizen) + `User`、`CameraDevice` + `CameraApiKey`（密码 `hash_password("123456")`）。

## 测试文件与覆盖矩阵（约 32-38 用例）

| 文件 | 覆盖点 |
|------|--------|
| `test_auth_api.py` | login 成功 / 密码错(401) / 账号禁用(403)；`/me` 鉴权(401) / 成功；`/permissions/menus` |
| `test_intakes_api.py` | citizen-reports：未登录 401 / 成功；camera-captures：缺 X-Camera-Key(401) / 无效 key(401) / 成功；admin-uploads：citizen 403 / reviewer 成功；断言任务链被投递 |
| `test_cases_api.py` | list：未登录 403 / 过滤 / 分页；get：404；approve：状态守卫(400) / 成功建违章 + 审计；reject；request-recheck |
| `test_violations_api.py` | list 过滤；get 404；owner 违章：市民查自己 OK / 查他人 403 |
| `test_statistics_api.py` | overview / by-location / by-type / by-time：鉴权 + 基本正确性 |
| `test_rbac_api.py` | RoleChecker 各角色组合经真实端点验证（admin / reviewer / citizen 拿到 200 / 403） |

## 不覆盖范围（边界）

- ML task 内部逻辑（YOLO / OCR / LLM 真实推理）——后续阶段。
- Alembic 迁移正确性。
- 前端。

## 成功标准

- `cd backend && python -m pytest` 全绿，无外部 Redis / LLM / SMTP / 模型权重依赖。
- 唯一外部依赖：本机 MySQL `traffic_violation_test` 库。
- 覆盖 5 个路由 + 中间件 + 权限的鉴权 / 权限 / 成功 / 主要错误路径。
