# Third Quality Pass Baseline

Date: 2026-06-17

## Repository And Workflow

- Branch: `codex/productionize-admin-platform`
- Workflow trigger: `.github/workflows/production-readiness.yml` uses `workflow_dispatch` only.
- Docker runtime at baseline: backend and BGE services were healthy.

## Production Readiness

`python scripts/validate_production_readiness.py --change production-quality-iteration-three` passed:

- protected resource manifest: PASS
- OpenSpec strict validation: PASS
- admin app import smoke: PASS
- backend tests: PASS, 50 passed
- frontend typecheck: PASS
- frontend tests: PASS, 7 passed
- frontend production build: PASS
- frontend build chunk report: PASS

Protected resource counts remained unchanged.

## Browser Smoke Baseline

The useful local browser-smoke origin is `http://localhost:5174`; backend CORS currently allows `5174`, not the preview origin `4174`.

Representative pages loaded without login redirect:

- `/admin/overview`
- `/admin/videos`
- `/admin/learning-assistant`
- `/admin/question-banks`
- `/admin/analytics`

Known console noise captured at baseline:

- `Warning: [antd: Space] direction is deprecated. Please use orientation instead.`
- `Warning: [antd: Tooltip] overlayClassName is deprecated. Please use classNames.root instead.`
- `Warning: [antd: Alert] message is deprecated. Please use title instead.`
- `Warning: [antd: Spin] tip is deprecated. Please use description instead.`
- `Warning: [antd: Drawer] width is deprecated. Please use size instead.`

The browser also logged a generic `Failed to load resource: the server responded with a status of 404 (Not Found)` on the overview page. The temporary smoke script did not capture a matching Playwright `response` event, so the committed e2e script should include richer diagnostics before this is closed.
