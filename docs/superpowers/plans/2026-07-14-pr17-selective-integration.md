# PR #17 Selective Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Selectively rebuild the approved PR #17 profile, layout, business-page, routing, and statistics features on the current tested `main`, then fast-forward the verified result into local `main`.

**Architecture:** Start a clean `codex/pr17-selective-integration` worktree from `main`; do not merge or cherry-pick PR #17. Preserve the current JavaScript auth/contracts and backend announcement APIs, extract only reusable behavior into small testable JavaScript helpers, and keep the backend as the single source of truth.

**Tech Stack:** Vue 3, Vue Router, Pinia, Element Plus, ECharts 5, Axios, SheetJS `xlsx`, Node test runner, FastAPI, SQLAlchemy 2, Pydantic 2, pytest, uv.

## Global Constraints

- Do not merge or cherry-pick PR #17.
- Preserve the current email registration, password-reset, announcement bell, `auth.js`, and `contracts.js` behavior.
- Do not add `contracts.ts` or migrate this scope to TypeScript.
- Do not persist announcements or rules in `localStorage`.
- Announcements have no draft/publish status; saving makes them visible immediately.
- Do not implement batch approve; batch reject must submit `{ reject_reason }`.
- Use `uv run --cache-dir .uv-cache --extra dev` for all backend tests.
- Every behavior change follows red-green-refactor and ends with an independently testable commit.

## Execution Prerequisite

Use `superpowers:using-git-worktrees` to create `.worktrees/pr17-selective-integration` from the current `main` on branch `codex/pr17-selective-integration`. Verify `.worktrees/` is ignored. Run these baselines inside the new worktree before editing:

```powershell
npm test
uv run --cache-dir .uv-cache --extra dev pytest -q --basetemp .pytest-tmp
```

Expected baseline: frontend 55 tests pass; backend 340 tests pass. Add `.pytest-tmp/` to `backend/.gitignore` in Task 1 so later test artifacts never dirty the worktree.

---

### Task 1: Profile API Contract and Profile Page

**Files:**
- Modify: `backend/.gitignore`
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/tests/api/test_auth.py`
- Modify: `smart-traffic-frontend/src/views/Profile.vue`
- Modify: `smart-traffic-frontend/src/stores/user.js`
- Create: `smart-traffic-frontend/public/images/admin.jpg`
- Create: `smart-traffic-frontend/public/images/reviewer.jpg`
- Create: `smart-traffic-frontend/public/images/citizen.jpg`
- Create: `smart-traffic-frontend/tests/selective-integration.test.js`
- Modify: `smart-traffic-frontend/package.json`

**Interfaces:**
- Consumes: existing `getUserInfo()`, `updateProfile(data)`, `changePassword(data)`, and `useUserStore()`.
- Produces: `UserOut.phone: str | None`, `UserOut.email: str`; a profile page that updates `userStore.userInfo` and logs out after password change.

- [ ] **Step 1: Write failing backend profile tests**

Extend `test_me_returns_user` and `test_update_profile` with exact contact assertions:

```python
def test_me_returns_user(client, citizen_user, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": citizen_user.id,
        "username": "citizen1",
        "role_code": "citizen",
        "phone": citizen_user.phone,
        "email": "citizen@example.com",
    }


def test_update_profile(client, citizen_user, auth_headers):
    response = client.put(
        "/api/v1/auth/profile",
        headers=auth_headers,
        json={"phone": "1390000", "email": " Updated@Example.COM "},
    )
    assert response.status_code == 200
    assert response.json()["phone"] == "1390000"
    assert response.json()["email"] == "updated@example.com"
```

- [ ] **Step 2: Verify the backend tests fail for missing fields**

Run:

```powershell
uv run --cache-dir .uv-cache --extra dev pytest -q --basetemp .pytest-tmp tests/api/test_auth.py::test_me_returns_user tests/api/test_auth.py::test_update_profile
```

Expected: both tests fail because `phone` and `email` are absent from `UserOut`.

- [ ] **Step 3: Implement the backend profile contract**

Add fields to `UserOut`:

```python
class UserOut(BaseModel):
    id: int
    username: str
    role_code: str
    phone: str | None = None
    email: str

    model_config = {"from_attributes": True}
```

In `auth.py`, add and use one mapper for login, registration, `/me`, and profile update:

```python
def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        role_code=user.role.code,
        phone=user.phone,
        email=user.email,
    )
```

Replace every manually constructed `UserOut(...)` with `_user_out(user)`. Add `.pytest-tmp/` to `backend/.gitignore`.

- [ ] **Step 4: Verify backend profile tests pass**

Run the Step 2 command. Expected: 2 passed.

- [ ] **Step 5: Write failing frontend profile source tests**

Create `tests/selective-integration.test.js`:

```javascript
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const source = path => readFile(new URL(path, import.meta.url), 'utf8')

test('profile edits backend contact fields and uses role avatars', async () => {
  const profile = await source('../src/views/Profile.vue')
  assert.match(profile, /form\.email/)
  assert.match(profile, /form\.phone/)
  assert.match(profile, /updateProfile\(\{ phone: form\.phone, email: form\.email \}\)/)
  assert.match(profile, /\/images\/admin\.jpg/)
  assert.match(profile, /\/images\/reviewer\.jpg/)
  assert.match(profile, /\/images\/citizen\.jpg/)
  assert.match(profile, /userStore\.logout\(\)/)
  assert.match(profile, /router\.push\('\/login'\)/)
})
```

Run:

```powershell
node --test tests/selective-integration.test.js
```

Expected: fail because the current profile has no email field or role avatars.

- [ ] **Step 6: Implement the profile page and avatar assets**

Copy the three binary avatar files from `.worktrees/pr-17/smart-traffic-frontend/public/images/` into the same paths in the integration worktree. Rebuild `Profile.vue` with:

```javascript
const form = reactive({ username: '', phone: '', email: '' })
const avatarUrl = computed(() => ({
  admin: '/images/admin.jpg',
  reviewer: '/images/reviewer.jpg',
  citizen: '/images/citizen.jpg'
}[userStore.role] || ''))

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const response = await updateProfile({ phone: form.phone, email: form.email })
    userStore.setUserInfo(response.data)
    Object.assign(form, response.data)
    ElMessage.success('保存成功')
  } finally {
    submitting.value = false
  }
}

async function handleChangePwd() {
  if (!pwdForm.oldPassword || !pwdForm.newPassword) return ElMessage.warning('请填写完整')
  if (pwdForm.newPassword !== pwdForm.rePassword) return ElMessage.warning('两次密码不一致')
  await changePassword({ old_password: pwdForm.oldPassword, new_password: pwdForm.newPassword })
  userStore.logout()
  router.push('/login')
}
```

Add `setUserInfo(info)` to `user.js`; it updates the ref and `localStorage.userInfo`. Return it from the store. The template must show the avatar, username, role tag, phone input, email input, save button, and password dialog. Keep card radii at 8px and use existing CSS variables for light/dark colors.

Update the frontend test script to include the new test file:

```json
"test": "node --test tests/contracts.test.js tests/email-auth-flow.test.js tests/selective-integration.test.js"
```

- [ ] **Step 7: Verify Task 1**

Run:

```powershell
npm test
uv run --cache-dir .uv-cache --extra dev pytest -q --basetemp .pytest-tmp tests/api/test_auth.py
```

Expected: all frontend tests and auth API tests pass.

- [ ] **Step 8: Commit Task 1**

```powershell
git add backend/.gitignore backend/app/schemas/auth.py backend/app/api/v1/auth.py backend/tests/api/test_auth.py smart-traffic-frontend/src/views/Profile.vue smart-traffic-frontend/src/stores/user.js smart-traffic-frontend/public/images/admin.jpg smart-traffic-frontend/public/images/reviewer.jpg smart-traffic-frontend/public/images/citizen.jpg smart-traffic-frontend/tests/selective-integration.test.js smart-traffic-frontend/package.json
git commit -m "feat: rebuild user profile"
```

### Task 2: Shared Header, Layout Shell, Error Boundary, Cache, and Route Cleanup

**Files:**
- Create: `smart-traffic-frontend/src/components/HeaderActions.vue`
- Create: `smart-traffic-frontend/src/components/BackToTop.vue`
- Modify: `smart-traffic-frontend/src/layouts/AdminLayout.vue`
- Modify: `smart-traffic-frontend/src/layouts/ReviewLayout.vue`
- Modify: `smart-traffic-frontend/src/layouts/CitizenLayout.vue`
- Modify: `smart-traffic-frontend/src/App.vue`
- Modify: `smart-traffic-frontend/src/router/index.js`
- Modify: `smart-traffic-frontend/src/views/review/CaseDetail.vue`
- Delete: `smart-traffic-frontend/src/views/admin/DriverList.vue`
- Delete: `smart-traffic-frontend/src/views/system/DatabaseMaintain.vue`
- Test: `smart-traffic-frontend/tests/selective-integration.test.js`

**Interfaces:**
- Consumes: `AnnouncementBell`, theme store, user store, route metadata.
- Produces: `HeaderActions` props `profilePath`, `roleLabel`, `defaultName`; `BackToTop` prop `target`; route metadata `keepAlive`.

- [ ] **Step 1: Write failing layout and routing tests**

Append tests that assert:

```javascript
test('all layouts use the shared header and route-aware cache shell', async () => {
  const header = await source('../src/components/HeaderActions.vue')
  assert.match(header, /<AnnouncementBell \/>/)
  for (const name of ['AdminLayout', 'ReviewLayout', 'CitizenLayout']) {
    const layout = await source(`../src/layouts/${name}.vue`)
    assert.match(layout, /<HeaderActions/)
    assert.match(layout, /<BackToTop/)
    assert.match(layout, /route\.meta\.keepAlive/)
    assert.doesNotMatch(layout, /cachedViews|:include=/)
  }
})

test('admin placeholders are removed and case detail is shared', async () => {
  const router = await source('../src/router/index.js')
  assert.doesNotMatch(router, /admin\/drivers|admin\/database|DriverList|DatabaseMaintain/)
  assert.match(router, /path: 'violations\/:id'[\s\S]*views\/review\/CaseDetail\.vue/)
  assert.match(router, /keepAlive: true/)
})

test('app provides a global render error boundary', async () => {
  const app = await source('../src/App.vue')
  assert.match(app, /onErrorCaptured/)
  assert.match(app, /window\.location\.reload\(\)/)
})
```

Run the selective test file. Expected: fail because the components and metadata do not exist.

- [ ] **Step 2: Implement `HeaderActions.vue` and `BackToTop.vue`**

`HeaderActions.vue` must render `AnnouncementBell`, an icon-only theme toggle with tooltip, optional role tag, and a user dropdown. Its command handler uses `router.push(props.profilePath)` and confirms before `userStore.logout()` plus `/login` navigation.

`BackToTop.vue` must watch `props.target`, attach one passive `scroll` listener, show after `scrollTop > 400`, call `target.scrollTo({ top: 0, behavior: 'smooth' })`, and detach before target changes or component unmounts.

- [ ] **Step 3: Rebuild the three layouts around the shared shell**

Each layout must use this cache structure:

```vue
<router-view v-slot="{ Component, route: viewRoute }">
  <Transition name="page-fade" mode="out-in">
    <KeepAlive>
      <component
        :is="Component"
        v-if="viewRoute.meta.keepAlive"
        :key="viewRoute.name"
      />
    </KeepAlive>
  </Transition>
  <Transition name="page-fade" mode="out-in">
    <component
      :is="Component"
      v-if="!viewRoute.meta.keepAlive"
      :key="viewRoute.fullPath"
    />
  </Transition>
</router-view>
```

Use `HeaderActions` in all three layouts and preserve `AnnouncementBell` only inside that component. Use `BackToTop :target="mainElement"`, where `mainElement` unwraps the Element Plus main ref via `$el`. Admin menu groups are violation management, vehicle, users, cameras, configuration, and logs. Reviewer menu remains flat.

- [ ] **Step 4: Add the error boundary and route changes**

`App.vue` tracks `hasError` and `errorMessage`, calls `onErrorCaptured`, and renders a refresh command when set. In router metadata, mark list/dashboard routes as cached and profile/detail/editor routes as uncached. Delete the driver/database routes and files. Point admin violation detail to `@/views/review/CaseDetail.vue`.

In `CaseDetail.vue`, add:

```javascript
const userStore = useUserStore()
const listPath = computed(() =>
  userStore.role === 'admin' ? '/admin/violations' : '/review/workbench'
)
```

Replace hard-coded post-review navigation with `router.push(listPath.value)`.

- [ ] **Step 5: Verify and commit Task 2**

Run `npm test` and `npm run build`. Expected: pass. Then commit:

```powershell
git add smart-traffic-frontend/src/components/HeaderActions.vue smart-traffic-frontend/src/components/BackToTop.vue smart-traffic-frontend/src/layouts smart-traffic-frontend/src/App.vue smart-traffic-frontend/src/router/index.js smart-traffic-frontend/src/views/review/CaseDetail.vue smart-traffic-frontend/src/views/admin/DriverList.vue smart-traffic-frontend/src/views/system/DatabaseMaintain.vue smart-traffic-frontend/tests/selective-integration.test.js
git commit -m "feat: unify application layouts"
```

### Task 3: Dashboard Dark-Mode Chart Theme

**Files:**
- Create: `smart-traffic-frontend/src/utils/chartTheme.js`
- Modify: `smart-traffic-frontend/src/views/stats/Dashboard.vue`
- Test: `smart-traffic-frontend/tests/selective-integration.test.js`

**Interfaces:**
- Produces: `getChartTheme(isDark)` returning `text`, `secondaryText`, `axis`, `grid`, `tooltipBackground`, and `tooltipBorder` colors.

- [ ] **Step 1: Write and run a failing pure theme test**

```javascript
test('chart theme exposes distinct readable light and dark palettes', async () => {
  const { getChartTheme } = await import('../src/utils/chartTheme.js')
  const light = getChartTheme(false)
  const dark = getChartTheme(true)
  assert.notEqual(light.text, dark.text)
  assert.notEqual(light.grid, dark.grid)
  assert.equal(dark.tooltipBackground, '#1f2329')
})
```

Expected failure: module not found.

- [ ] **Step 2: Implement and consume the palette**

```javascript
export function getChartTheme(isDark) {
  return isDark
    ? {
        text: '#e5eaf3', secondaryText: '#a3a6ad', axis: '#8d9095',
        grid: '#3a3d43', tooltipBackground: '#1f2329', tooltipBorder: '#4c4d4f'
      }
    : {
        text: '#303133', secondaryText: '#606266', axis: '#909399',
        grid: '#e4e7ed', tooltipBackground: '#ffffff', tooltipBorder: '#dcdfe6'
      }
}
```

Dashboard imports the theme store, derives `chartColors`, applies it to every chart axis, grid, legend, label, title and tooltip, and watches `themeStore.isDark` to call `renderAll()` after `nextTick()`. Preserve instance disposal and resize cleanup.

- [ ] **Step 3: Verify and commit Task 3**

Run `npm test` and `npm run build`, then commit the helper, Dashboard, and test file with message `feat: adapt charts to dark mode`.

### Task 4: Complete Filtered Excel Export

**Files:**
- Create: `smart-traffic-frontend/src/utils/pagination.js`
- Create: `smart-traffic-frontend/src/utils/export.js`
- Modify: `smart-traffic-frontend/src/api/violation.js`
- Modify: `smart-traffic-frontend/src/views/admin/ViolationList.vue`
- Modify: `smart-traffic-frontend/src/views/review/ViolationList.vue`
- Modify: `smart-traffic-frontend/src/views/citizen/MyViolations.vue`
- Modify: `smart-traffic-frontend/src/views/citizen/MyReports.vue`
- Modify: `smart-traffic-frontend/package.json`
- Modify: `smart-traffic-frontend/package-lock.json`
- Test: `smart-traffic-frontend/tests/selective-integration.test.js`

**Interfaces:**
- Produces: `fetchAllPages(fetchPage, params, pageSize = 100)`, `exportToExcel(rows, columns, filename)`, and `formatExportTime(value)`.

- [ ] **Step 1: Write failing pagination tests**

Test two pages are collected, parameters are preserved, empty results return `[]`, and a second-page rejection propagates. Use a real async function recording `{ page, page_size }` calls.

- [ ] **Step 2: Implement `fetchAllPages` minimally**

```javascript
export async function fetchAllPages(fetchPage, params = {}, pageSize = 100) {
  const rows = []
  for (let page = 1; ; page += 1) {
    const response = await fetchPage({ ...params, page, page_size: pageSize })
    const payload = response.data ?? response
    const items = payload.items ?? []
    rows.push(...items)
    if (rows.length >= (payload.total ?? rows.length) || items.length === 0) return rows
  }
}
```

Run the selective tests. Expected: pagination tests pass.

- [ ] **Step 3: Install SheetJS and implement export formatting**

Run `npm install xlsx@^0.18.5`. Implement `exportToExcel` with `XLSX.utils.aoa_to_sheet`, explicit column widths, one `Sheet1`, and `XLSX.writeFile`. `formatExportTime` returns a Chinese locale string or an empty string.

- [ ] **Step 4: Wire all four export pages**

Change `fetchOwnerViolations` to accept optional params:

```javascript
export const fetchOwnerViolations = (ownerId, params) =>
  request.get(`/owners/${ownerId}/violations`, { params })
```

Each page adds one export button with `exporting` loading state. It calls `fetchAllPages` using the same filter builder as the table, transforms timestamps, and invokes `exportToExcel` only after all pages succeed. MyReports exports raw case rows without loading protected media blobs. Disable export when `total === 0`.

- [ ] **Step 5: Verify and commit Task 4**

Run `npm test`, `npm run build`, and `npm audit --omit=dev`. Record audit findings without changing unrelated dependency versions. Commit with message `feat: export complete filtered records`.

### Task 5: Citizen Owner Selector in Vehicle Management

**Files:**
- Modify: `smart-traffic-frontend/src/views/admin/VehicleList.vue`
- Test: `smart-traffic-frontend/tests/selective-integration.test.js`

**Interfaces:**
- Consumes: `fetchAllPages`, `fetchUsers`, existing vehicle payload builder.

- [ ] **Step 1: Write failing source tests**

Assert VehicleList imports `fetchUsers` and `fetchAllPages`, requests `{ role: 'citizen' }`, renders `owner_name`, uses an `el-select` bound to `form.owner_id`, and contains no editable numeric owner ID input.

- [ ] **Step 2: Implement the selector**

Load all citizen pages once per mount:

```javascript
const citizenUsers = ref([])
const ownerById = computed(() => new Map(citizenUsers.value.map(user => [user.id, user.username])))
const displayedVehicles = computed(() => list.value.map(vehicle => ({
  ...vehicle,
  owner_name: ownerById.value.get(vehicle.owner_id) || '未知用户'
})))

async function loadCitizenUsers() {
  citizenUsers.value = await fetchAllPages(
    params => fetchUsers(params),
    { role: 'citizen' }
  )
}
```

Use `displayedVehicles` in the table and a filterable, clearable select for create/edit. Keep `owner_id` required only for creation, matching the existing backend contract.

- [ ] **Step 3: Verify and commit Task 5**

Run `npm test` and `npm run build`; commit with message `feat: select citizen vehicle owners`.

### Task 6: Batch Reject Without Batch Approve

**Files:**
- Create: `smart-traffic-frontend/src/utils/batchReject.js`
- Modify: `smart-traffic-frontend/src/views/review/Workbench.vue`
- Test: `smart-traffic-frontend/tests/selective-integration.test.js`

**Interfaces:**
- Produces: `batchRejectCases(ids, reason, rejectFn)` returning `{ succeededIds, failedIds }`.

- [ ] **Step 1: Write failing batch behavior tests**

```javascript
test('batch reject sends the exact payload and reports partial failure', async () => {
  const { batchRejectCases } = await import('../src/utils/batchReject.js')
  const calls = []
  const result = await batchRejectCases([1, 2], ' 证据不足 ', async (id, payload) => {
    calls.push([id, payload])
    if (id === 2) throw new Error('failed')
  })
  assert.deepEqual(calls, [
    [1, { reject_reason: '证据不足' }],
    [2, { reject_reason: '证据不足' }]
  ])
  assert.deepEqual(result, { succeededIds: [1], failedIds: [2] })
})
```

Also assert an empty reason rejects with `TypeError`, and Workbench contains no `batchApprove` or `批量通过` text.

- [ ] **Step 2: Implement the helper and workbench UI**

Use unique IDs, trim and require the reason, call `Promise.allSettled`, and partition IDs by result status. Workbench selection is available only for `uploaded` and `pending_human_review`. The prompt requires nonblank input. After submission, remove successful IDs, retain failed IDs, reload cases, and display `已驳回 X 件，失败 Y 件` when partial.

- [ ] **Step 3: Verify and commit Task 6**

Run `npm test` and `npm run build`; commit with message `feat: add batch case rejection`.

### Task 7: Backend-Persisted Announcement Admin CRUD

**Files:**
- Modify: `smart-traffic-frontend/src/views/admin/Announcement.vue`
- Test: `smart-traffic-frontend/tests/selective-integration.test.js`

**Interfaces:**
- Consumes: existing `fetchAnnouncements`, `createAnnouncement`, `updateAnnouncement`, `deleteAnnouncement`.

- [ ] **Step 1: Write failing announcement page tests**

Assert the page imports the four API functions, sends only `{ title, content }`, has pagination, has edit/delete commands, and contains neither `localStorage` nor `is_published`.

- [ ] **Step 2: Implement the real CRUD page**

Use state `{ list, page, pageSize, total, loading, saving, deletingId }`. `loadList()` requests the current page. `save()` validates and awaits create/update before closing. `remove(id)` awaits delete, decrements `page` when the deleted row was the last row on a nonfirst page, then reloads. Use `ElMessageBox.confirm` or `el-popconfirm` and preserve form input after failed saves.

- [ ] **Step 3: Verify and commit Task 7**

Run `npm test`, `npm run build`, and the existing backend announcement API tests with uv. Commit with message `feat: add announcement administration`.

### Task 8: Rule Deletion API and Admin UI

**Files:**
- Modify: `backend/app/services/violation_rule_service.py`
- Modify: `backend/app/api/v1/rules.py`
- Modify: `backend/tests/api/test_rules_api.py`
- Modify: `smart-traffic-frontend/src/api/system.js`
- Modify: `smart-traffic-frontend/src/views/admin/RuleConfig.vue`
- Test: `smart-traffic-frontend/tests/selective-integration.test.js`

**Interfaces:**
- Produces: `ViolationRuleService.delete_rule(rule_id) -> None`, `DELETE /api/v1/admin/rules/{rule_id}`, and `deleteRule(id)`.

- [ ] **Step 1: Write failing backend delete tests**

Add tests for admin `204` with database removal, missing `404`, unauthenticated `401`, and citizen/reviewer `403`. Run only these tests and confirm the route returns 405 before implementation.

- [ ] **Step 2: Implement service and route**

```python
def delete_rule(self, rule_id: int) -> None:
    rule = self.get_rule(rule_id)
    self.db.delete(rule)
    self.db.commit()
```

```python
@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> None:
    ViolationRuleService(db).delete_rule(rule_id)
```

- [ ] **Step 3: Write failing frontend rule tests and implement UI**

Assert `system.js` exports `deleteRule`, RuleConfig awaits it behind confirmation, and the page contains no `localStorage` or built-in defaults. Add:

```javascript
export const deleteRule = id => request.delete(`/admin/rules/${id}`)
```

Track `deletingIds`, reload after success, and leave the list unchanged on failure. Keep the existing active switch rollback.

- [ ] **Step 4: Verify and commit Task 8**

Run frontend tests/build and `uv ... pytest ... tests/api/test_rules_api.py`. Commit with message `feat: delete violation rules`.

### Task 9: Heatmap Creation-Date Filtering

**Files:**
- Modify: `backend/app/services/statistics_service.py`
- Modify: `backend/tests/services/test_statistics_service.py`

**Interfaces:**
- Keeps: hour slot derived from `Violation.occurred_at`.
- Changes: date-window predicate to `Violation.created_at.between(st, et)`.

- [ ] **Step 1: Write the failing semantic test**

Seed one violation created inside the query range but occurred outside, and another created outside but occurred inside. Assert only the first appears, in the slot derived from its outside-range occurrence hour.

- [ ] **Step 2: Verify RED and implement one-line filter change**

Run the single new test. Expected: current code counts the occurred-inside row. Change only:

```python
Violation.created_at.between(st, et),
```

- [ ] **Step 3: Verify and commit Task 9**

Run the complete statistics service test file, then commit with message `fix: filter heatmap by creation date`.

### Task 10: Full Verification, UI Smoke, and Fast-Forward Merge

**Files:**
- No production files unless verification reveals a defect; any defect starts a new failing test before a fix.
- Generated screenshots: store outside the repository or in the Codex visualization writable directory.

**Interfaces:**
- Consumes: all tasks above.
- Produces: a tested local `main` containing only the approved selective integration.

- [ ] **Step 1: Run complete automated verification**

```powershell
npm test
npm run build
uv run --cache-dir .uv-cache --extra dev pytest -q --basetemp .pytest-tmp
git diff --check main...HEAD
git status --short
```

Expected: all tests pass, frontend build exits 0, diff check exits 0, and only intentional tracked files differ from `main`.

- [ ] **Step 2: Review scope against the design**

Run `git diff --stat main...HEAD`, `git log --oneline main..HEAD`, and inspect every changed path. Confirm there is no `auth.ts`, `contracts.ts`, local announcement/rule persistence, batch approve code, or unrelated PR file.

- [ ] **Step 3: Run browser smoke checks**

Start the backend through uv and the frontend Vite server on available local ports. Use the browser control skill to verify desktop 1440x900 and mobile 390x844 for:

- citizen, reviewer, and admin layout menus and headers;
- profile contact form and role avatar;
- announcement and rule dialogs;
- vehicle citizen selector;
- batch reject selection and prompt;
- Dashboard light/dark chart readability;
- breadcrumb navigation, route cache state, and back-to-top visibility.

Capture screenshots for each role and both Dashboard themes. Confirm no overlap, clipped controls, blank chart canvas, or console errors.

- [ ] **Step 4: Commit any verification-only test adjustments**

Only when a new failing test was added and fixed, commit it with the related production fix. Do not make untested visual-only corrections.

- [ ] **Step 5: Fast-forward local main**

Confirm the original `main` worktree has no tracked modifications and has not advanced unexpectedly. From the main worktree run:

```powershell
git merge --ff-only codex/pr17-selective-integration
```

Then rerun `npm test` and the focused backend tests affected by the integration from `main`. Do not push unless the user separately requests it.
