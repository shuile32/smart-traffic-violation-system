# Task 3 Report: Frontend Announcement Contract and Shared Header Entry

## Files

- Created `smart-traffic-frontend/src/api/announcement.js`
- Created `smart-traffic-frontend/src/components/AnnouncementBell.vue`
- Created `smart-traffic-frontend/src/utils/announcementController.js`
- Updated `smart-traffic-frontend/src/utils/contracts.js`
- Updated `smart-traffic-frontend/tests/contracts.test.js`
- Updated `smart-traffic-frontend/src/layouts/CitizenLayout.vue`
- Updated `smart-traffic-frontend/src/layouts/ReviewLayout.vue`
- Updated `smart-traffic-frontend/src/layouts/AdminLayout.vue`

## TDD Evidence

### RED

Command: `cd smart-traffic-frontend; npm test`

Result: exit 1, 32 passed and 2 failed. The failures were the expected missing-feature failures:

- `TypeError: contracts.buildAnnouncementPayload is not a function`
- `ENOENT` for `src/api/announcement.js`

### GREEN

Command: `cd smart-traffic-frontend; npm test`

Result: exit 0, 34 passed and 0 failed.

The new coverage verifies payload trimming and field selection, all five exact API method/path contracts, the latest-five request, the accessible Element Plus bell entry without a badge, and mounting in all three shared layouts.

## Build

Command: `cd smart-traffic-frontend; npm run build`

Result: exit 0. Vite transformed 2,277 modules and completed the production build. Output retained the baseline `@vueuse` PURE-comment and chunk-size warnings.

## Self-Review

- API functions use the existing Axios wrapper and exact Task 2 routes.
- The payload helper emits only trimmed `title` and `content` fields.
- Opening the popover refreshes page 1 with `page_size: 5`; selecting a row fetches full detail.
- Request failures are left to the shared Axios interceptor; the component does not import or call `ElMessage`.
- The trigger has a stable 32 by 32 pixel footprint, an Element Plus `Bell`, tooltip, and `aria-label`; no unread state or badge exists.
- The popover is constrained to the viewport, the list/loading/empty surface has fixed height, and long titles/content wrap without overlapping. Detail content preserves body whitespace in a scrollable responsive dialog.
- `AnnouncementBell` appears immediately before the theme toggle in Citizen, Review, and Admin layouts.
- `git diff --check` completed without whitespace errors.

## Concerns

- No task-specific concerns. The production build continues to report the two known categories of baseline warnings noted above.

## Review Fixes

### Changes

- Replaced the `ElTooltip` direct Popover reference child with a fixed-size native `span`. The tooltip and Element Plus icon button remain inside it, so bell clicks bubble to the concrete trigger where Popover installs its reference listeners.
- Capped the complete dialog to `calc(100dvh - 24px)` with a `100vh` fallback, made the dialog a clipped flex column, kept the header fixed, and moved vertical scrolling to `.el-dialog__body`.
- Clamped announcement detail titles to two lines, bounding backend titles up to the 100-character schema limit without overlapping the close control or body.
- Added a focused source-contract regression test that requires the native reference wrapper and rejects the previous direct-tooltip structure. It also protects the viewport cap, flex layout, two-line title clamp, and dialog-body scrolling contract.

### TDD and Verification Evidence

- RED: `npm test` exited 1 with 34 passing and the new regression failing because the Popover reference began with `ElTooltip` instead of the required native `span`.
- GREEN: `npm test` exited 0 with 35 passing and 0 failing after the component fix.
- Build: `npm run build` exited 0 after transforming 2,277 modules. Only the baseline `@vueuse` PURE-comment and chunk-size warnings remained.
- `git diff --check` exited 0.

### Acceptance Boundary

- The existing Node harness can strongly enforce the event-target structure and viewport-safe CSS contract but does not mount Element Plus in a browser. Task 5 browser acceptance will exercise the real bell click, Popover opening, detail selection, and narrow-viewport behavior.

## Second Review Fixes

This section supersedes the first review iteration's two-line detail-title clamp. List-row previews remain two lines, but the detail dialog now exposes every character of the selected announcement title.

### Changes

- Removed `overflow: hidden` and `-webkit-line-clamp` from the detail title. The title wraps with `overflow-wrap: anywhere` and is never silently truncated.
- Kept the complete dialog viewport-capped and changed its header to a shrinkable region capped at `min(35dvh, 220px)` with its own vertical scrolling. The body remains a separate flex scrolling region, so an unusually tall title cannot push the body or dialog outside the viewport.
- Added `src/utils/announcementController.js`, a dependency-injected pure state controller for announcement list and detail requests. `AnnouncementBell.vue` wraps the controller state with Vue reactivity and uses its `loadAnnouncements` and `selectAnnouncement` methods directly.
- Added executable Node coverage for the pending and completed list/detail transitions. Tests assert the exact latest-five request, selected row ID, dialog visibility/loading changes, and published response data.
- Retained the source regression that rejects an `ElTooltip` direct Popover reference child and strengthened the dialog contract to prohibit detail-title truncation while requiring bounded header and body scrolling.

### TDD and Verification Evidence

- RED: `npm test` exited 1 with 33 passing and 4 failing. Two tests failed because the controller module did not exist, the component-use assertion failed, and the viewport contract detected the existing title clamp.
- GREEN: `npm test` exited 0 with 37 passing and 0 failing after the controller extraction, Vue wiring, and title/header CSS changes.
- Build: `npm run build` exited 0 after transforming 2,278 modules. Only the baseline `@vueuse` PURE-comment and chunk-size warnings remained.
- `git diff --check` exited 0.

### Acceptance Boundary

- The controller tests execute API calls and state transitions without adding dependencies, but they do not synthesize an Element Plus DOM click. Task 5 browser acceptance remains responsible for the real bell click, Popover, row-selection, long-title, and narrow-viewport interactions.
