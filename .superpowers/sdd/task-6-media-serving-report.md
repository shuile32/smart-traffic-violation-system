# Task 6 Media Serving Report

## Scope

- Added `GET /media/{filename}` to the FastAPI application.
- Reads `settings.MEDIA_STORAGE_DIR` for every request so runtime configuration and tests are honored.
- Serves only regular, single-level files from the configured storage root with `FileResponse`.
- Returns HTTP 404 for missing files and rejects forward-slash, backslash, dot-segment, resolved-parent, and out-of-root symlink traversal.
- Did not modify AI routes/providers, `backend/app/ai`, or YOLO code.

## TDD Evidence

1. Existing file RED: `test_get_media_returns_stored_file` expected 200 but received 404 because no media route existed.
2. Existing file GREEN: after the minimal `FileResponse` route, `1 passed`.
3. Missing file RED: the route raised `RuntimeError` from `FileResponse` instead of returning 404.
4. Missing file GREEN: after the regular-file guard, `2 passed`.
5. Traversal RED: `/media/%2E%2E%5C<outside-file>` returned 200 and exposed a file outside the storage root.
6. Traversal GREEN: after separator and resolved-parent validation, `3 passed`.

## Verification

- Focused: `cd backend && uv run pytest -q tests/api/test_media.py`
  - Result: `3 passed, 1 warning in 0.16s`.
- Full backend: `cd backend && uv run pytest -q`
  - Result: `195 passed, 1 warning in 30.11s`.
- Diff check: `git diff --check` (recorded after report creation).
- Warning: existing Starlette deprecation warning for the `httpx` TestClient compatibility layer.

## Commit

The implementation, regression tests, and this report are contained in this scoped commit.
