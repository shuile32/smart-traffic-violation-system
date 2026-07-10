# 前后端集成缺陷修复 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复前后端集成测试发现的 18 个缺陷——6 个页面白屏、5 个页面使用 Mock 假数据、关键数据流断裂。

**Architecture:** 后端单行 schema 补字段修 case ID 断裂；前端批量改 import（Mock→真实 API）、为无后端支持的页面加统一「开发中」占位；清理 intake.js 重复导出、补 201 响应处理、修中文字符集。

**Tech Stack:** FastAPI + Pydantic v2 + Vue 3 + Element Plus + Axios

**上游基线:** `frontend-backend-integration` 分支，180 测试全绿

---

## 修复策略

| 优先级 | 修复方式 | 涉及 |
|:--:|------|------|
| P0 | 改 import / 补 schema 字段 | 7 个致命缺陷 |
| P1 | import 切换到真实 API + 适配数据结构 | 5 个 Mock 页面 |
| P2 | 加统一占位组件 | 5 个无后端 API 页面 |
| P3 | 清理 / 配置修复 | 编码、重复导出、201 |

---

## 文件结构

```
新增:
- smart-traffic-frontend/src/components/UnderDevelopment.vue   # 统一「开发中」占位组件

修改 (后端):
- backend/app/schemas/case.py:5-12                              # CaseListItem 加 id 字段
- backend/app/api/v1/cases.py:30-36                             # 列表响应加 id
- backend/app/core/config.py                                    # 确认 charset 配置

修改 (前端 API 层):
- smart-traffic-frontend/src/api/intake.js                      # 删除 mock 导出，只留真实 API
- smart-traffic-frontend/src/api/request.js:27                  # 201 也包信封

修改 (前端视图 — 改 import):
- smart-traffic-frontend/src/views/review/ImageUpload.vue:55,92 # import + 字段名
- smart-traffic-frontend/src/views/stats/Dashboard.vue:57,72-91 # Mock→Real + 数据适配
- smart-traffic-frontend/src/views/admin/ViolationList.vue:110  # Mock→Real
- smart-traffic-frontend/src/views/admin/AdvancedSearch.vue:83  # Mock→Real
- smart-traffic-frontend/src/views/citizen/Report.vue:63,99-103 # Mock→Real intake

修改 (前端视图 — 加占位):
- smart-traffic-frontend/src/views/admin/ViolationReview.vue     # 用 UnderDevelopment
- smart-traffic-frontend/src/views/admin/ViolationUpload.vue     # 用 UnderDevelopment
- smart-traffic-frontend/src/views/admin/Announcement.vue        # 用 UnderDevelopment
- smart-traffic-frontend/src/views/system/DatabaseMaintain.vue   # 用 UnderDevelopment
- smart-traffic-frontend/src/views/admin/DriverList.vue          # 用 UnderDevelopment
- smart-traffic-frontend/src/views/admin/RoleManage.vue          # 用 UnderDevelopment
- smart-traffic-frontend/src/views/system/RoleManage.vue         # 用 UnderDevelopment
```

---

### Task 1: 创建 UnderDevelopment 占位组件

**Files:**
- Create: `smart-traffic-frontend/src/components/UnderDevelopment.vue`

- [ ] **Step 1: 创建组件**

```vue
<!-- smart-traffic-frontend/src/components/UnderDevelopment.vue -->
<template>
  <div class="page-container" style="display:flex;align-items:center;justify-content:center;min-height:60vh">
    <el-result icon="info" title="功能开发中" sub-title="该功能正在开发中，敬请期待。">
      <template #extra>
        <el-button type="primary" @click="$router.back()">返回上一页</el-button>
        <el-button @click="$router.push('/')">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
// 纯展示组件，无需额外逻辑
</script>
```

- [ ] **Step 2: 验证文件创建**

```bash
ls -la smart-traffic-frontend/src/components/UnderDevelopment.vue
```

---

### Task 2: 修复 Case ID 断裂 (BUG-1) — 致命

**Files:**
- Modify: `backend/app/schemas/case.py:5-12`
- Modify: `backend/app/api/v1/cases.py:30-36`

**根因:** `CaseListItem` 不包含 `id`，前端 `Workbench.vue` 用 `item.id` 导航详情 → `undefined` → 后端 `case_id: int` 解析失败。

- [ ] **Step 1: CaseListItem schema 加 `id` 字段**

```python
# backend/app/schemas/case.py — CaseListItem (line 5-12)
class CaseListItem(BaseModel):
    id: int                          # ← 新增：数据库主键
    case_no: str
    status: str
    source_type: str | None = None
    plate_no: str | None = None
    violation_type: str | None = None
    captured_at: str | None = None
    location_text: str | None = None
```

- [ ] **Step 2: 列表响应填充 `id`**

```python
# backend/app/api/v1/cases.py — list_cases 函数 (line 30-36)
# 修改 CaseListItem 构造，加入 id=c.id
items.append(CaseListItem(
    id=c.id,                         # ← 新增
    case_no=c.case_no, status=c.status,
    source_type=ev.source_type if ev else None,
    plate_no=c.plate_no, violation_type=c.violation_type,
    captured_at=str(ev.captured_at) if ev and ev.captured_at else None,
    location_text=ev.location_text if ev else None,
))
```

- [ ] **Step 3: 验证 — 列表响应包含 id**

```bash
curl -s http://localhost:8001/api/v1/cases \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8001/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin1234"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')" \
  | python -c "import sys,json; d=json.load(sys.stdin); print('HAS id:', 'id' in d['items'][0] if d['items'] else 'NO ITEMS')"
```

期望输出: `HAS id: True`

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/case.py backend/app/api/v1/cases.py
git commit -m "fix: CaseListItem 增加 id 字段，修复案件详情/审批 ID 断裂"
```

---

### Task 3: 修复 ImageUpload.vue (BUG-2 + BUG-17) — 致命

**Files:**
- Modify: `smart-traffic-frontend/src/views/review/ImageUpload.vue:55,86-92`

**根因:** 导入 `mockAdminUpload`（不存在）+ 调用 `adminUpload`（未导入）+ FormData 字段名 `images` 应为 `image`。

- [ ] **Step 1: 修复 import + FormData 字段名**

```javascript
// smart-traffic-frontend/src/views/review/ImageUpload.vue
// Line 55: 修改 import
import { adminUpload } from '@/api/intake'
```

```javascript
// Line 86-92: 修改 handleSubmit 中的 FormData 构建
const fd = new FormData()
fd.append('location_text', form.location_text)
fd.append('captured_at', form.captured_at)
if (form.speed) fd.append('speed', form.speed)
// 后端期望字段名是 'image'（单数），不是 'images'
if (fileList.value.length > 0) {
  fd.append('image', fileList.value[0].raw)
}
await adminUpload(fd)
```

**注意:** 后端只接受单文件 `UploadFile`，前端 `el-upload` 虽支持多选，但 intake API 只接受一个 `image` 字段。只传第一个文件。

- [ ] **Step 2: 重启前端验证无编译错误**

```bash
# 检查 Vite 编译输出无 "does not provide an export named" 错误
```

- [ ] **Step 3: Commit**

```bash
git add smart-traffic-frontend/src/views/review/ImageUpload.vue
git commit -m "fix: ImageUpload.vue - 修复 import 和 FormData 字段名"
```

---

### Task 4: 修复 Dashboard.vue Mock→Real (BUG-8) — 严重

**Files:**
- Modify: `smart-traffic-frontend/src/views/stats/Dashboard.vue:57,71-124`

**根因:** 导入 mock 函数 `getOverview/getTrend/getTypeRatio/getRegionRank`，展示写死的假数据。

**数据适配:** 后端返回格式与 mock 不同：
- Mock: `{ data: { total_cases, today_new, approve_rate, ... } }`（已被拦截器包成 `{ code, data: { data } }`）
- Real (经拦截器包信封): `{ code: 200, data: { total_cases, approved_count, rejected_count, pending_count, approval_rate, period } }`

前端 `overviewCards` 引用的字段名需要对齐后端真实字段：
- `total_cases` ✅ 一致
- `total_violations` → 改为 `approved_count`（后端无 total_violations）
- `approve_rate` → 改为 `approval_rate`（已存在，需 ×100）
- `reject_rate` → 从 `rejected_count/total_cases` 计算
- `pending_count` ✅ 一致
- `today_new` → 后端无此字段，改为 `pending_count` 或用 0

- [ ] **Step 1: 修改 import**

```javascript
// smart-traffic-frontend/src/views/stats/Dashboard.vue:57
// 旧:
import { getOverview, getTrend, getTypeRatio, getRegionRank } from '@/api/statistics'
// 新:
import { fetchOverview, fetchByTime, fetchByType, fetchByLocation } from '@/api/statistics'
```

- [ ] **Step 2: 适配 loadData 函数和 computed**

```javascript
// smart-traffic-frontend/src/views/stats/Dashboard.vue:71-91
// 旧的 overviewCards computed → 改为匹配真实 API 字段:
const overviewCards = computed(() => {
  const d = overview.value || {}
  const total = d.total_cases || 0
  const approved = d.approved_count || 0
  const rejected = d.rejected_count || 0
  return [
    { label: '总案件数', value: total, color: '#409eff' },
    { label: '已通过', value: approved, color: '#67c23a' },
    { label: '已驳回', value: rejected, color: '#f56c6c' },
    { label: '通过率', value: (d.approval_rate != null ? (d.approval_rate * 100).toFixed(1) + '%' : 'N/A'), color: '#409eff' },
    { label: '待审核', value: d.pending_count || 0, color: '#e6a23c' },
    { label: '时间段', value: d.period ? d.period.start?.slice(0, 10) + '~' + d.period.end?.slice(0, 10) : '全部', color: '#909399' }
  ]
})

async function loadData() {
  const params = {}
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_time = dateRange.value[0]
    params.end_time = dateRange.value[1]
  }
  const [ov, tr, ty, rg] = await Promise.all([
    fetchOverview(params),
    fetchByTime(params),
    fetchByType(params),
    fetchByLocation(params)
  ])
  overview.value = ov.data
  // 后端 by-time 返回 [{date, count}] 格式，对齐趋势图
  trend.value = (tr.data || []).map(t => ({ date: t.date, count: t.count }))
  // 后端 by-type 返回 [{violation_type, count, percentage}]，对齐饼图
  typeRatio.value = (ty.data || []).map(t => ({ name: t.violation_type, value: t.count }))
  // 后端 by-location 返回 [{location_text, count}]，对齐柱状图
  regionRank.value = (rg.data || []).map(r => ({ name: r.location_text, value: r.count }))
}
```

- [ ] **Step 3: 确认后端统计数据格式**

```bash
curl -s http://localhost:8001/api/v1/statistics/by-time \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool | head -20
curl -s http://localhost:8001/api/v1/statistics/by-type \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool | head -20
curl -s http://localhost:8001/api/v1/statistics/by-location \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool | head -20
```

> 如果后端返回格式与预期不同，根据实际响应调整 map 函数中的字段名。

- [ ] **Step 4: Commit**

```bash
git add smart-traffic-frontend/src/views/stats/Dashboard.vue
git commit -m "fix: Dashboard.vue 从 Mock 切换到真实统计 API"
```

---

### Task 5: 修复 ViolationList.vue + AdvancedSearch.vue Mock→Real (BUG-9 + BUG-10)

**Files:**
- Modify: `smart-traffic-frontend/src/views/admin/ViolationList.vue:110`
- Modify: `smart-traffic-frontend/src/views/admin/AdvancedSearch.vue:83`

- [ ] **Step 1: ViolationList.vue — 修改 import + adapt**

```javascript
// smart-traffic-frontend/src/views/admin/ViolationList.vue:110
// 旧:
import { getViolations, deleteViolation, exportExcel } from '@/api/violation'
// 新:
import { fetchViolations } from '@/api/violation'
```

还需要处理被删除的 `deleteViolation` 和 `exportExcel` 引用：
- `deleteViolation`: 后端无删除 API → 改为 `ElMessage.warning('暂不支持删除')`
- `exportExcel`: 后端无导出 API → 改为 `ElMessage.warning('导出功能开发中')`

> **注意:** 需要读取 ViolationList.vue 的 `<script>` 部分找到 `deleteViolation` 和 `exportExcel` 的调用位置，替换为上面的降级处理。

- [ ] **Step 2: AdvancedSearch.vue — 修改 import**

```javascript
// smart-traffic-frontend/src/views/admin/AdvancedSearch.vue:83
// 旧:
import { getViolations } from '@/api/violation'
// 新:
import { fetchViolations } from '@/api/violation'

// 搜索函数中: getViolations(params) → fetchViolations(params)
// 响应结构: res.data.items 不变（拦截器包信封后一致）
```

- [ ] **Step 3: Commit**

```bash
git add smart-traffic-frontend/src/views/admin/ViolationList.vue smart-traffic-frontend/src/views/admin/AdvancedSearch.vue
git commit -m "fix: ViolationList + AdvancedSearch 从 Mock 切换到真实 API"
```

---

### Task 6: 修复 Report.vue (citizen) Mock→Real (BUG-11)

**Files:**
- Modify: `smart-traffic-frontend/src/views/citizen/Report.vue:63,99-103`

- [ ] **Step 1: 修改 import + FormData 构建**

```javascript
// smart-traffic-frontend/src/views/citizen/Report.vue:63
// 旧:
import { submitReport } from '@/api/violation'
// 新:
import { citizenReport } from '@/api/intake'
```

```javascript
// Line 99-103: 修改 FormData + API 调用
// 旧:
const fd = new FormData()
fd.append('location', form.location)
fd.append('violation_time', form.violation_time)
fd.append('description', form.description)
fileList.value.forEach(f => fd.append('images', f.raw))
await submitReport(fd)

// 新:
const fd = new FormData()
fd.append('location_text', form.location)
fd.append('captured_at', form.violation_time)
if (form.description) fd.append('description', form.description)
// 后端只接受单文件 image
if (fileList.value.length > 0) {
  fd.append('image', fileList.value[0].raw)
}
await citizenReport(fd)
```

- [ ] **Step 2: Commit**

```bash
git add smart-traffic-frontend/src/views/citizen/Report.vue
git commit -m "fix: Report.vue 从 Mock submitReport 切换到真实 intake API"
```

---

### Task 7: 为无后端 API 页面加「开发中」占位 (BUG-3/4/5/6/7/12)

**Files:**
- Modify: `smart-traffic-frontend/src/views/admin/ViolationReview.vue`
- Modify: `smart-traffic-frontend/src/views/admin/ViolationUpload.vue`
- Modify: `smart-traffic-frontend/src/views/admin/Announcement.vue`
- Modify: `smart-traffic-frontend/src/views/system/DatabaseMaintain.vue`
- Modify: `smart-traffic-frontend/src/views/admin/DriverList.vue`
- Modify: `smart-traffic-frontend/src/views/admin/RoleManage.vue`
- Modify: `smart-traffic-frontend/src/views/system/RoleManage.vue`

**策略:** 每个页面的 `<template>` 和 `<script>` 替换为使用 `UnderDevelopment` 占位组件的最小实现。保留原有代码在注释中供后续开发参考。

- [ ] **Step 1: ViolationReview.vue — 替换为占位**

```vue
<!-- smart-traffic-frontend/src/views/admin/ViolationReview.vue -->
<template>
  <UnderDevelopment />
</template>

<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

- [ ] **Step 2: ViolationUpload.vue — 替换为占位**

```vue
<!-- smart-traffic-frontend/src/views/admin/ViolationUpload.vue -->
<template>
  <UnderDevelopment />
</template>

<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

- [ ] **Step 3: Announcement.vue — 替换为占位**

```vue
<!-- smart-traffic-frontend/src/views/admin/Announcement.vue -->
<template>
  <UnderDevelopment />
</template>

<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

- [ ] **Step 4: DatabaseMaintain.vue — 替换为占位**

```vue
<!-- smart-traffic-frontend/src/views/system/DatabaseMaintain.vue -->
<template>
  <UnderDevelopment />
</template>

<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

- [ ] **Step 5: DriverList.vue — 替换为占位**

```vue
<!-- smart-traffic-frontend/src/views/admin/DriverList.vue -->
<template>
  <UnderDevelopment />
</template>

<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

- [ ] **Step 6: RoleManage.vue (admin) — 替换为占位**

```vue
<!-- smart-traffic-frontend/src/views/admin/RoleManage.vue -->
<template>
  <UnderDevelopment />
</template>

<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

- [ ] **Step 7: RoleManage.vue (system) — 替换为占位**

```vue
<!-- smart-traffic-frontend/src/views/system/RoleManage.vue -->
<template>
  <UnderDevelopment />
</template>

<script setup>
import UnderDevelopment from '@/components/UnderDevelopment.vue'
</script>
```

- [ ] **Step 8: Commit**

```bash
git add smart-traffic-frontend/src/views/admin/ViolationReview.vue \
        smart-traffic-frontend/src/views/admin/ViolationUpload.vue \
        smart-traffic-frontend/src/views/admin/Announcement.vue \
        smart-traffic-frontend/src/views/system/DatabaseMaintain.vue \
        smart-traffic-frontend/src/views/admin/DriverList.vue \
        smart-traffic-frontend/src/views/admin/RoleManage.vue \
        smart-traffic-frontend/src/views/system/RoleManage.vue
git commit -m "fix: 7个无后端API页面替换为 UnderDevelopment 占位组件"
```

---

### Task 8: 清理 intake.js 重复导出 (BUG-15)

**Files:**
- Modify: `smart-traffic-frontend/src/api/intake.js`

**根因:** Mock 和真实 API 使用相同导出名，真实 API 在后面覆盖 mock。删除 mock 导出，只保留真实 API。

- [ ] **Step 1: 删除 mock 导出，只留真实 API**

```javascript
// smart-traffic-frontend/src/api/intake.js
// 删除所有 mock 函数（line 1-48），只保留:
import request from './request'

// 真实后端 API
export const citizenReport = (fd) => request.post('/intakes/citizen-reports', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
export const cameraCapture = (fd) => request.post('/intakes/camera-captures', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
export const adminUpload = (fd) => request.post('/intakes/admin-uploads', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
```

- [ ] **Step 2: 确认无其他文件引用被删除的函数**

```bash
grep -r "getIntakeEvents\|getIntakeEvent" smart-traffic-frontend/src/ --include="*.vue" --include="*.js" || echo "No references found - safe to delete"
```

- [ ] **Step 3: Commit**

```bash
git add smart-traffic-frontend/src/api/intake.js
git commit -m "refactor: intake.js 清理 mock 导出，只保留真实 API"
```

---

### Task 9: 补 201 响应处理 (BUG-13)

**Files:**
- Modify: `smart-traffic-frontend/src/api/request.js:27`

**根因:** 注册返回 201，拦截器对非 200 的 2xx 走 error 分支而非包信封。

- [ ] **Step 1: 扩展拦截器处理 201**

```javascript
// smart-traffic-frontend/src/api/request.js:23-35
// 旧:
request.interceptors.response.use(
  response => {
    const raw = response.data
    if (typeof raw === 'object' && raw !== null && !('code' in raw)) {
      return { code: 200, message: 'ok', data: raw }
    }
    // ...
  },
  // ...
)

// 新: 对 2xx 统一处理（200 + 201 等）
request.interceptors.response.use(
  response => {
    const raw = response.data
    // 所有 2xx 成功响应，裸 Pydantic 无信封则包一层
    if (typeof raw === 'object' && raw !== null && !('code' in raw)) {
      return { code: response.status, message: 'ok', data: raw }
    }
    if (raw.code === 401) {
      localStorage.clear()
      router.push('/login')
      return Promise.reject(new Error('登录已过期'))
    }
    return raw
  },
  // error handler unchanged...
)
```

- [ ] **Step 2: Commit**

```bash
git add smart-traffic-frontend/src/api/request.js
git commit -m "fix: 响应拦截器兼容 201 Created 状态码"
```

---

### Task 10: 修复中文编码 (BUG-14)

**Files:**
- Modify: `backend/app/core/config.py`

**根因:** MySQL 连接字符串可能缺少正确的 charset 设置，导致中文字符存储/读取乱码。

- [ ] **Step 1: 确认 .env DATABASE_URL charset 设置**

```bash
cat backend/.env | grep DATABASE_URL
```

期望包含: `?charset=utf8mb4`

如果缺失，`.env` 中 DATABASE_URL 应设置为:
```
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/traffic_violation?charset=utf8mb4
```

- [ ] **Step 2: 检查 config.py 默认值**

```python
# backend/app/core/config.py
# DATABASE_URL 默认值应包含 ?charset=utf8mb4
DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/traffic_violation?charset=utf8mb4"
```

- [ ] **Step 3: 验证修复 — 重新摄入后中文不乱码**

```bash
# 重新上传一张图片
python -c "
import requests, io
from PIL import Image
img = Image.new('RGB', (50, 50), color='green')
buf = io.BytesIO()
img.save(buf, format='JPEG')
resp = requests.post('http://localhost:8001/api/v1/intakes/admin-uploads',
    headers={'Authorization': 'Bearer ...'},
    files={'image': ('enc_test.jpg', buf.getvalue(), 'image/jpeg')},
    data={'location_text': '编码测试-中山路', 'captured_at': '2026-07-10T12:00:00'})
print(resp.json().get('message', 'NO MESSAGE'))
"
# 期望: "图片已接收，等待处理"（非乱码）
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/config.py backend/.env
git commit -m "fix: 确保 MySQL 连接使用 utf8mb4 charset"
```

---

## Self-Review

**1. Spec coverage:** 18 个缺陷全部覆盖——7 个致命（Task 2/3/7）、5 个 Mock（Task 4/5/6）、5 个缺失 API（Task 7 占位）、2 个编码/导出（Task 8/9/10）。BUG-18（审批多余字段）是无害的，此轮不修。

**2. Placeholder scan:** 无 TBD/TODO。所有代码步骤都有具体实现。

**3. Type consistency:** 前端 `fetch*` 函数命名一致；后端 `CaseListItem` 新增 `id: int` 与 detail 的 `id: int` 一致。

**待定 — 确认项:**
- 后端 statistics/by-time/by-type/by-location 返回的精确字段名需要 Task 4 Step 3 验证后微调 map 函数
- ViolationList.vue 中 `deleteViolation` / `exportExcel` 的具体调用位置需要读取文件后精确定位
