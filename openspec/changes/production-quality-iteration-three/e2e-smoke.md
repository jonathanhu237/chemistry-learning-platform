# Repeatable E2E Smoke

Date: 2026-06-17

## Changes

- Added `apps/admin-web/scripts/e2e-smoke.mjs`.
- Added `npm run e2e:smoke`.
- Added Playwright as a frontend development dependency.
- Added `--run-e2e` to `scripts/validate_production_readiness.py`.
- Updated production operations docs with e2e prerequisites and smoke admin handling.

## Behavior

The smoke script:

- checks backend `/health`
- checks the frontend login page
- prepares a disposable local `codex_smoke_admin` through the Docker backend when no `E2E_ADMIN_PASSWORD` is provided
- logs in through `/api/auth/login`
- injects the bearer token into local storage
- visits `/admin/overview`, `/admin/videos`, `/admin/learning-assistant`, `/admin/question-banks`, and `/admin/analytics`
- reports route results, console warnings/errors, known Ant Design deprecations, 404 responses, failed requests, and page errors

Default validation still does not run browser e2e. It is opt-in with:

```powershell
python scripts/validate_production_readiness.py --run-e2e
```

## Verification

`npm run e2e:smoke` passed against the local Docker backend and frontend dev server on `http://localhost:5174`.
The run reported no console warnings/errors, no known Ant Design deprecations, no 404s, no failed requests, and no page errors.
