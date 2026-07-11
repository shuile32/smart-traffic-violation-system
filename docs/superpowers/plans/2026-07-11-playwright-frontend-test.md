# Playwright MCP 前端全量自动化测试计划

> **For agentic workers:** 本计划使用 Playwright MCP (`mcp__playwright__*` 工具) 执行。步骤使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 用 Playwright MCP 对智能交通违章管理平台前端做全量页面覆盖测试——截图每个页面、抓取控制台报错、测试关键增删改查流程。

**Architecture:** 启动 Vite dev server (port 5173)，Playwright MCP 导航至各页面。前端无需后端即可渲染 UI（API 调用会失败但页面结构正常），重点验证页面渲染、交互反馈、控制台报错。增删改查流程测试依赖后端是否运行——若 8000 端口无响应则跳过 CRUD 流程、记录阻断原因。

**Tech Stack:** Playwright MCP (browser_navigate/click/type/snapshot/screenshot/console_messages)、Vite dev server、Vue 3 + Element Plus

**前置条件：**
- Playwright MCP 已连接（重启 Claude Code 后生效）
- Node.js v22 可用
- `smart-traffic-frontend/` 目录下 `npm install` 已完成

---

### Task 1: 启动开发服务器

**Files:**
- 无新建/修改文件

- [ ] **Step 1: 启动 Vite dev server（后台运行）**

```bash
cd C:/Users/demonlover/Desktop/smart-traffic-violation-system/smart-traffic-frontend && npm run dev
```

Run in background (`run_in_background: true`)，等待 5 秒后验证。

- [ ] **Step 2: 确认 dev server 已启动**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
```

Expected: `200`（返回 HTML 页面）

- [ ] **Step 3: 确认后端状态（决定 CRUD 测试是否可行）**

```
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/
```

记录结果：若返回非 200，则跳过 Task 8（CRUD 流程测试）。

---

### Task 2: 登录页测试

**Goal:** 验证登录页渲染、表单验证、提交行为

- [ ] **Step 1: 导航到登录页并截图**

```
browser_navigate: http://localhost:5173/login
```

Expected: 自动跳转到登录页，显示用户名/密码输入框和登录按钮。

- [ ] **Step 2: 截图登录页**

```
browser_take_screenshot: filename=01-login-page.png, fullPage=true
```

- [ ] **Step 3: 测试空表单提交验证**

```
browser_click: 登录按钮（不填任何内容）
browser_snapshot: 检查是否显示"请输入用户名"等校验提示
```

Expected: Element Plus 表单校验提示出现。

- [ ] **Step 4: 测试错误凭据提交**

```
browser_type: 用户名输入框 → "wronguser"
browser_type: 密码输入框 → "wrongpass"
browser_click: 登录按钮
browser_wait_for: time=2 秒
browser_snapshot: 检查错误提示（如"用户名或密码错误"或网络错误）
```

- [ ] **Step 5: 截图登录错误状态**

```
browser_take_screenshot: filename=02-login-error.png
```

- [ ] **Step 6: 抓取登录页控制台报错**

```
browser_console_messages: level=error
```

记录所有 error 级别日志。

- [ ] **Step 7: Commit 截图和日志**

```bash
# 将截图和日志文件整理记录
```

---

### Task 3: 管理员面板页面全覆盖

**Goal:** 逐页截图 admin 下所有非 UnderDevelopment 页面，检查控制台报错

**前置:**
- 先尝试用测试账号登录（若后端不可用则跳过登录直接在地址栏导航，观察未登录态页面表现）

- [ ] **Step 1: 尝试登录管理员**

```bash
# 如果后端可用（Task 1 Step 3 返回 200），用接口直接登录获取 token：
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

若成功，用 `browser_evaluate` 注入 token 到 localStorage；若失败，跳过登录直接导航。

- [ ] **Step 2: 用户管理页 `/admin/users`**

```
browser_navigate: http://localhost:5173/admin/users
browser_wait_for: time=2
browser_take_screenshot: filename=03-admin-users.png, fullPage=true
browser_console_messages: level=error
browser_snapshot: 记录页面元素结构
```

- [ ] **Step 3: 角色管理页 `/admin/roles`**

```
browser_navigate: http://localhost:5173/admin/roles
browser_take_screenshot: filename=04-admin-roles.png, fullPage=true
```

Expected: 显示"功能开发中"（UnderDevelopment 组件）。

- [ ] **Step 4: 摄像头管理 `/admin/cameras`**

```
browser_navigate: http://localhost:5173/admin/cameras
browser_take_screenshot: filename=05-admin-cameras.png, fullPage=true
browser_snapshot: 记录表格列和操作按钮
browser_console_messages: level=error
```

- [ ] **Step 5: 规则配置 `/admin/rules`**

```
browser_navigate: http://localhost:5173/admin/rules
browser_take_screenshot: filename=06-admin-rules.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 6: 短信模板 `/admin/sms-templates`**

```
browser_navigate: http://localhost:5173/admin/sms-templates
browser_take_screenshot: filename=07-admin-sms.png, fullPage=true
```

Expected: UnderDevelopment。

- [ ] **Step 7: 操作日志 `/admin/logs`**

```
browser_navigate: http://localhost:5173/admin/logs
browser_take_screenshot: filename=08-admin-logs.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 8: 公告管理 `/admin/announcements`**

```
browser_navigate: http://localhost:5173/admin/announcements
browser_take_screenshot: filename=09-admin-announcements.png
```

Expected: UnderDevelopment。

- [ ] **Step 9: 违章列表 `/admin/violations`**

```
browser_navigate: http://localhost:5173/admin/violations
browser_take_screenshot: filename=10-admin-violations.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 10: 车辆管理 `/admin/vehicles`**

```
browser_navigate: http://localhost:5173/admin/vehicles
browser_take_screenshot: filename=11-admin-vehicles.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 11: 驾驶员管理 `/admin/drivers`**

```
browser_navigate: http://localhost:5173/admin/drivers
browser_take_screenshot: filename=12-admin-drivers.png
```

Expected: UnderDevelopment。

- [ ] **Step 12: 高级搜索 `/admin/search`**

```
browser_navigate: http://localhost:5173/admin/search
browser_take_screenshot: filename=13-admin-search.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 13: 系统日志 `/admin/system-logs`**

```
browser_navigate: http://localhost:5173/admin/system-logs
browser_take_screenshot: filename=14-admin-system-logs.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 14: 数据库维护 `/admin/database`**

```
browser_navigate: http://localhost:5173/admin/database
browser_take_screenshot: filename=15-admin-database.png
```

Expected: UnderDevelopment。

- [ ] **Step 15: 管理员统计 `/admin/stats`**

```
browser_navigate: http://localhost:5173/admin/stats
browser_wait_for: time=3
browser_take_screenshot: filename=16-admin-stats.png, fullPage=true
browser_snapshot: 检查 KPI 卡片和 ECharts 图表是否存在
browser_console_messages: level=error
```

---

### Task 4: 审核工台页面覆盖

- [ ] **Step 1: 审核工台 `/review/workbench`**

```
browser_navigate: http://localhost:5173/review/workbench
browser_wait_for: time=2
browser_take_screenshot: filename=17-review-workbench.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 2: 审核违章列表 `/review/violations`**

```
browser_navigate: http://localhost:5173/review/violations
browser_take_screenshot: filename=18-review-violations.png, fullPage=true
browser_snapshot
```

- [ ] **Step 3: 证据上传 `/review/upload`**

```
browser_navigate: http://localhost:5173/review/upload
browser_take_screenshot: filename=19-review-upload.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

---

### Task 5: 统计仪表盘页面覆盖

- [ ] **Step 1: 统计仪表盘 `/stats`**

```
browser_navigate: http://localhost:5173/stats
browser_wait_for: time=3
browser_take_screenshot: filename=20-stats-dashboard.png, fullPage=true
browser_snapshot: 检查 6 个 KPI 卡片 + 趋势折线图 + 类型饼图 + 区域柱状图
browser_console_messages: level=error
```

- [ ] **Step 2: 分析报告 `/stats/report`**

```
browser_navigate: http://localhost:5173/stats/report
browser_take_screenshot: filename=21-stats-report.png, fullPage=true
browser_snapshot
```

Expected: 显示 "AI 分析模块暂未接入"。

---

### Task 6: 公民门户页面覆盖

- [ ] **Step 1: 公民首页 `/citizen/home`**

```
browser_navigate: http://localhost:5173/citizen/home
browser_wait_for: time=2
browser_take_screenshot: filename=22-citizen-home.png, fullPage=true
browser_snapshot
browser_console_messages: level=error
```

- [ ] **Step 2: 随手拍举报 `/citizen/report`**

```
browser_navigate: http://localhost:5173/citizen/report
browser_take_screenshot: filename=23-citizen-report.png, fullPage=true
browser_snapshot: 检查图片上传区、表单字段
```

- [ ] **Step 3: 我的举报 `/citizen/my-reports`**

```
browser_navigate: http://localhost:5173/citizen/my-reports
browser_take_screenshot: filename=24-citizen-my-reports.png, fullPage=true
browser_snapshot
```

- [ ] **Step 4: 车辆绑定 `/citizen/vehicles`**

```
browser_navigate: http://localhost:5173/citizen/vehicles
browser_take_screenshot: filename=25-citizen-vehicles.png, fullPage=true
browser_snapshot
```

- [ ] **Step 5: 我的违章 `/citizen/my-violations`**

```
browser_navigate: http://localhost:5173/citizen/my-violations
browser_take_screenshot: filename=26-citizen-my-violations.png, fullPage=true
browser_snapshot
```

---

### Task 7: 全局控制台报错汇总

- [ ] **Step 1: 用 browser_run_code_unsafe 注入全局错误监听**

```javascript
// 在每个页面注入 window.__playwrightErrors = []
// 然后监听 window.onerror 和 console.error
```

- [ ] **Step 2: 产出每页报错清单**

对 Tasks 2-6 收集的所有 `browser_console_messages: level=error` 做汇总，按页面分类。

- [ ] **Step 3: 产出报错报告**

写入 `docs/superpowers/plans/playwright-test-results/console-errors.md`，列出：
- 页面路径
- 报错内容
- 严重程度（阻断/警告/可忽略）
- 修复建议

---

### Task 8: 增删改查流程测试（条件执行）

**前置条件：** 仅当 Task 1 Step 3 确认后端 8000 端口可达时执行。若不可达，跳过整个 Task 8 并记录原因。

- [ ] **Step 1: 用户管理 CRUD 流程**

```
# Create: 点击"新增用户"→ 填表 → 提交 → 刷新列表验证新行出现
# Read:   列表加载用户数据，分页切换
# Update: 点击编辑 → 修改角色 → 保存 → 验证变更
# Delete: 切换状态开关（启用/禁用），验证状态更新
```

```
browser_navigate: http://localhost:5173/admin/users
browser_click: "新增用户" 按钮
browser_type: 用户名 → "testuser_playwright"
browser_type: 真实姓名 → "测试用户"
browser_type: 手机号 → "13900000001"
browser_select_option: 角色 → admin
browser_click: 确认/提交按钮
browser_wait_for: time=2
browser_snapshot: 验证新增行出现
browser_take_screenshot: filename=27-crud-user-create.png
```

- [ ] **Step 2: 车辆管理 CRUD 流程**

```
browser_navigate: http://localhost:5173/admin/vehicles
# Create vehicle: 点新增 → 填车牌/车主/类型/颜色 → 提交
# Read: 列表加载 + 搜索车牌
# Update: 编辑修改
# Delete: 无删除按钮则跳过
```

- [ ] **Step 3: 规则配置 CRUD 流程**

```
browser_navigate: http://localhost:5173/admin/rules
# Create rule → toggle active/inactive
```

---

### Task 9: 产出测试报告

- [ ] **Step 1: 整理所有截图**

截图命名约定：`{序号}-{模块}-{页面}.png`，存到 `docs/superpowers/plans/playwright-test-results/screenshots/`

- [ ] **Step 2: 编写测试报告**

输出 `docs/superpowers/plans/playwright-test-results/test-report.md`，包含：
- 测试概况（页面数、通过/失败/跳过）
- 每页测试结果（截图链接、控制台报错数、渲染状态）
- CRUD 流程测试结果（若有）
- 控制台报错汇总
- 改进建议

---

### Task 10: 清理

- [ ] **Step 1: 停止 dev server**

```bash
# 杀掉 Vite 进程
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *vite*" 2>nul || true
```

- [ ] **Step 2: 提交测试产物**

```bash
git add docs/superpowers/plans/playwright-test-results/
git commit -m "test: Playwright MCP 前端全量测试报告"
```

---

> **执行方式：** 本计划适合用 Playwright MCP 逐步执行。每个 Step 调用对应的 MCP 工具（`mcp__playwright__*`），截图和 console 日志保存到本地。Tasks 1-7（页面覆盖 + 错误收集）必须全部执行；Task 8（CRUD 流程）条件执行；Task 9 产出最终报告。
