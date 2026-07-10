# 🚦 智能交通违章平台 — 前后端功能测试报告

> 测试日期: 2026-07-10 | 测试范围: 所有 API 端点 + 前端视图代码审查

---

## 一、测试概览

| 指标 | 数值 |
|------|------|
| API 端点测试 | 50+ |
| 前端视图审查 | 24 个 Vue 文件 |
| 🔴 致命缺陷 | 7 个（功能完全不可用） |
| 🟠 严重缺陷 | 6 个（数据错误/使用 Mock） |
| 🟡 一般缺陷 | 5 个（兼容性/缺失功能） |

---

## 二、🔴 致命缺陷（功能完全不可用）

### BUG-1: 案件列表→详情 ID 类型不匹配

**根因**: 后端 `GET /cases` 返回 `{ case_no, status, ... }` 不包含 `id` 字段，但 `GET /cases/{case_id}` 要求 `case_id: int`。

| 层级 | 代码位置 | 行为 |
|------|---------|------|
| 后端 | `cases.py:41` | `case_id: int` — 只接受整数 DB ID |
| 后端 | `cases.py:31` | `CaseListItem` 返回 `case_no` 字符串，不含 `id` |
| 前端 | `Workbench.vue:33` | `:key="item.id"` — `id` 为 `undefined` |
| 前端 | `Workbench.vue:36` | `openDetail(item.id)` — 传递 `undefined` |
| 前端 | `Workbench.vue:162` | `router.push('/review/case/${id}')` → `/review/case/undefined` |
| 前端 | `CaseDetail.vue:266` | `getCaseDetail(route.params.id)` → 请求 `/cases/undefined` |

**结果**: 审核工作台可以看到案件列表，但点击任何案件卡片查看详情 → **必崩**。

**修复方向**:
- 方案 A: `CaseListItem` schema 增加 `id: int` 字段，前端用 `id` 请求详情
- 方案 B: 后端改用 `case_no` (string) 做路径参数，`/cases/{case_no}`

---

### BUG-2: ImageUpload.vue 导入不存在的函数

**位置**: `src/views/review/ImageUpload.vue:55`
```js
import { mockAdminUpload } from '@/api/intake'  // ❌ 不存在
```

`intake.js` 的真实 API 导出了 `adminUpload`（覆盖了 mock 同名导出），但没有 `mockAdminUpload`。

**结果**: 审核员点击「证据上传」页面 → 模块加载失败 → **白屏/报错**。

---

### BUG-3: ViolationReview.vue 导入不存在的函数

**位置**: `src/views/admin/ViolationReview.vue:115`
```js
import { getViolation, getAiResult, reviewViolation } from '@/api/violation'
// ❌ getViolation 不存在（mock 叫 getViolations，真实叫 fetchViolationDetail）
// ❌ getAiResult 不存在
// ❌ reviewViolation 不存在
```

**结果**: 管理员点击「违章审核处理」页面 → **白屏/报错**。

---

### BUG-4: ViolationUpload.vue 导入不存在的函数

**位置**: `src/views/admin/ViolationUpload.vue:74`
```js
import { createViolation, uploadImage } from '@/api/violation'
// ❌ 两个函数均不存在于 violation.js
```

**结果**: 管理员点击「违章证据上传」页面 → **白屏/报错**。

---

### BUG-5: Announcement.vue 导入不存在的函数

**位置**: `src/views/admin/Announcement.vue:44`
```js
import { getAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement } from '@/api/system'
// ❌ 四个函数均不存在于 system.js，后端也无对应 API
```

**结果**: 管理员点击「系统公告」页面 → **白屏/报错**。

---

### BUG-6: DatabaseMaintain.vue 导入不存在的函数

**位置**: `src/views/system/DatabaseMaintain.vue:41`
```js
import { backupDatabase } from '@/api/system'
// ❌ 不存在，后端无此 API
```

**结果**: 管理员点击「数据库维护」页面 → **白屏/报错**。

---

### BUG-7: DriverList.vue 调用不存在的后端 API

**位置**: `src/views/admin/DriverList.vue:99` → `src/api/driver.js`
```js
// driver.js 调用 /drivers, /drivers/:id, /drivers/:id/license 等
// 后端验证: GET /api/v1/drivers → 404 Not Found
```

**结果**: 管理员点击「驾驶员管理」页面 → API 404 → **功能不可用**。

---

## 三、🟠 严重缺陷（使用 Mock 数据，非真实 API）

### BUG-8: Dashboard.vue 使用 Mock 统计数据

**位置**: `src/views/stats/Dashboard.vue:57`
```js
import { getOverview, getTrend, getTypeRatio, getRegionRank } from '@/api/statistics'
// ↑ 这四个是 Mock 函数，返回 mock.js 里的假数据
// 真实 API: fetchOverview, fetchByLocation, fetchByType, fetchByTime
```

**结果**: 数据大屏展示的是写死的假数据，看不到真实统计。

---

### BUG-9: ViolationList.vue (admin) 使用 Mock

**位置**: `src/views/admin/ViolationList.vue:110`
```js
import { getViolations, deleteViolation, exportExcel } from '@/api/violation'
// ↑ Mock 函数，且 deleteViolation/exportExcel 是假实现
// 真实 API: fetchViolations（仅查询列表）
```

**结果**: 管理员看到的违章列表是假数据。

---

### BUG-10: AdvancedSearch.vue 使用 Mock

**位置**: `src/views/admin/AdvancedSearch.vue:83`
```js
import { getViolations } from '@/api/violation'
// ↑ Mock 函数
```

---

### BUG-11: Report.vue (citizen) 使用 Mock 提交举报

**位置**: `src/views/citizen/Report.vue:63`
```js
import { submitReport } from '@/api/violation'
// ↑ Mock 函数，返回假数据
// 应该使用: intake.js 的 citizenReport 真实 API
```

**结果**: 市民提交随手拍举报 → 走了 Mock → **没有真正提交到后端**。

---

### BUG-12: RoleManage.vue (两处) 使用 Mock

**位置**: 
- `src/views/admin/RoleManage.vue:69` → `import { getRoles, createRole, updateRole, deleteRole }` 
- `src/views/system/RoleManage.vue:39` → `import { getRoles, updateRolePermissions }`

**问题**: 后端没有 `/admin/roles` CRUD API（roles 通过 seed_data 固定），system.js 也无真实角色 API。

---

### BUG-13: 登记接口返回 201 而非 200

**后端**: `POST /api/v1/auth/register` → **201 Created**
**前端拦截器** (`request.js:27`): 检查 `!('code' in raw)` 包信封 → 201 响应也会走到这个逻辑，理论上能处理。

但前端 `auth.js` 的 `register` 函数调用后，stores/user.js 中的 `login` action 会尝试读取 `res.data.access_token`，需要确认 201 响应下的数据结构是否一致。已验证：201 响应结构与 200 一致（`{access_token, token_type, user}`），但不排除时序问题。

---

## 四、🟡 一般缺陷

### BUG-14: 中文编码乱码

API 响应中的中文字段出现乱码：
```json
{"message": "ͼƬ�ѽ��գ��ȴ�����"}  
// 期望: "图片已接收，等待处理"
{"location_text": "娴嬭瘯璺彛1鍙"}  
// 期望: "测试路口1号"
```

**影响范围**: 所有中文内容的 API 响应。可能是 MySQL charset 或连接字符串编码问题。

---

### BUG-15: intake.js 同名导出覆盖

`intake.js` 中 mock 和真实 API 使用**完全相同的函数名**：
```js
export const adminUpload = async ... // Mock (line 29)
export const adminUpload = (fd) => ... // 真实 (line 54) ← 覆盖了 mock
```

因为真实 API 在后面，所以最终导出的是真实版本。但 `ImageUpload.vue` 试图导入 `mockAdminUpload`（不存在），虽然实际调用了 `adminUpload`。

---

### BUG-16: 后端缺失 API 端点

前端页面引用了后端不存在的 API：

| 前端页面 | 调用的 API | 后端状态 |
|---------|-----------|---------|
| DriverList.vue | `/api/v1/drivers/*` | ❌ 404 |
| RoleManage.vue | `/admin/roles` CRUD | ❌ 不存在 |
| Announcement.vue | 公告 CRUD | ❌ 不存在 |
| DatabaseMaintain.vue | 数据库备份 | ❌ 不存在 |
| SmsTemplate.vue | 短信模板 CRUD | ❌ 不存在 (notification_templates 有模型无 CRUD API) |

---

### BUG-17: ImageUpload.vue 表单字段名不匹配

`ImageUpload.vue` 中上传图片的 FormData 字段名是 `images`（复数）：
```js
fileList.value.forEach(f => fd.append('images', f.raw))
```

但后端 `intakes.py` 期望 `image`（单数）：
```python
async def citizen_report(image: UploadFile = File(...), ...)
```

**结果**: 审核员上传图片会因字段名不匹配而失败。

---

### BUG-18: 审批请求发送多余字段

`CaseDetail.vue:278` 发送审批请求时包含 `action` 字段：
```js
await approveCase(route.params.id, { ...reviewForm, action: 'approve' })
```

`reviewForm` 对象中存在 `action` 属性（`reviewForm.action = 'approve'`），但后端 `ApproveRequest` schema 不包含此字段。虽然 FastAPI 默认会忽略多余字段，但不够干净。

---

## 五、功能正常的部分 ✅

以下功能经测试确认可用：

| 模块 | 状态 | 说明 |
|------|:--:|------|
| 登录/注册 | ✅ | JWT 签发正确，角色识别准确 |
| Token 刷新/校验 | ✅ | `/auth/me` 正确返回用户信息 |
| 修改资料/密码 | ✅ | profile 和 password 端点正常 |
| 权限菜单 | ✅ | 按角色返回不同菜单项 |
| 图片摄入（市民） | ✅ | 文件上传、哈希去重均正常 |
| 图片摄入（管理员） | ✅ | 正常 |
| 图片摄入（摄像头） | ✅ | X-Camera-Key 鉴权正常 |
| 重复上传检测 | ✅ | 相同图片返回 409 |
| 非法文件拦截 | ✅ | 非图片 MIME 返回 400 |
| 案件列表查询 | ✅ | 分页、状态过滤正常 |
| 案件详情（int ID） | ✅ | 返回完整信息 |
| 案件审批通过 | ✅ | 创建违章+通知+奖励 |
| 案件驳回 | ✅ | 正确更新状态 |
| 案件重检请求 | ✅ | 返回 stub 202 |
| 违章列表/详情 | ✅ | reviewer/admin 正常 |
| 车主违章查询 | ✅ | 市民仅看自己的 |
| 统计 API（4 端点） | ✅ | 聚合查询正常 |
| 摄像头 CRUD | ✅ | 7 路由 + Key 生成/吊销 |
| API Key 吊销后失效 | ✅ | 吊销 Key 再调用 intake → 401 |
| 用户管理 CRUD | ✅ | 软禁用正常 |
| 车辆管理 CRU | ✅ | 车牌去重、模糊搜索 |
| 违章规则 CRUD | ✅ | 正常 |
| AI YOLO/OCR/规则/初审 | ✅ | 4 端点正常返回 stub 数据 |
| AI 权限控制 | ✅ | Citizen 访问 AI → 403 |
| RBAC 整体 | ✅ | 角色隔离严格 |
| 审计日志查询 | ✅ | 正常 |
| 奖励记录查询 | ✅ | 正常 |
| LLM 报告生成 | ✅ | Stub 正常 |

---

## 六、修复优先级

### P0 — 立即修复（功能阻断）

| 序号 | 问题 | 修复工作量 |
|:--:|------|:--:|
| 1 | Case list 缺少 `id` 字段 → 详情/审批/驳回全链路断裂 | 小（2 行） |
| 2-7 | 6 个页面导入不存在的函数 → 白屏 | 中（需补 API 或降级处理） |

### P1 — 本周修复（数据真实性）

| 序号 | 问题 | 修复工作量 |
|:--:|------|:--:|
| 8-12 | 5 个页面使用 Mock 而非真实 API | 小（改 import） |
| 13 | 登记 201 处理确认 | 小 |
| 14 | 中文编码乱码 | 中（排查 MySQL charset） |
| 17 | ImageUpload 字段名 images→image | 小 |

### P2 — 后续迭代

| 序号 | 问题 | 说明 |
|:--:|------|------|
| 16 | 缺失后端 API | 角色管理/公告/驾驶员/短信模板需新建 API |
| 18 | 审批 body 多余字段 | 代码清理 |
| 15 | intake.js 导出清理 | 去掉 mock 层或分离文件 |
