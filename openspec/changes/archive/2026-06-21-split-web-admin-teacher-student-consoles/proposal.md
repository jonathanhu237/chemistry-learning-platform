## Why

The current `apps/admin-web` product is really the teacher console, but its name and role checks imply it is also the platform operations console. This mixes two different account models and keeps teacher-facing functionality hidden behind admin-only branches that no longer match the product.

## What Changes

- **BREAKING** Rename the current teacher-facing `admin-web` frontend product semantics to `web-teacher`, with a `web-teacher` service/container and default port `5174`.
- **BREAKING** Add a new independent `web-admin` frontend/container on default port `5175` for platform operations only.
- Keep `web-student` as the student frontend/container on default port `5173`.
- **BREAKING** Teacher console accounts have complete teacher-console functionality; role-based feature hiding inside `web-teacher` is removed for learning assistant, AI access, system settings, experiment catalog, question bank, and related teacher modules.
- Add backend config-token authentication for `web-admin`; the platform console no longer uses `app_users` username/password login.
- Keep teacher-console accounts as `role='admin'` going forward, with legacy `teacher` accepted only as a compatibility login alias and never as a feature-visibility limiter.
- Add `/api/web-admin/teacher-accounts` endpoints for list, create, patch display/status, reset password, and delete operations; responses must never expose `password_hash`.
- Make teacher-account delete soft by default using `status='disabled'`.
- Make teacher-account password reset increment `password_version` so existing teacher tokens are invalidated.
- Update Docker Compose, environment examples, documentation, package/service names, and validation to use `web-admin`, `web-teacher`, and `web-student`.
- Add backend and frontend coverage for the split login/role behavior and teacher-account management workflow.

## Capabilities

### New Capabilities

- `web-console-product-boundaries`: Defines the three independent web consoles, their service names, ports, product meanings, and access boundaries.
- `platform-teacher-account-management`: Defines the config-token-only teacher account management API and web-admin desktop workbench.

### Modified Capabilities

- `react-ant-design-admin-console`: The existing admin console becomes the teacher console, keeps the green Ant Design visual system, and removes teacher-facing feature permission branches.
- `backend-admin-router-ownership`: Backend ownership expands to include `web-admin` routes separate from teacher-facing admin routes, with explicit config-token authorization.
- `frontend-admin-maintainability`: Frontend app ownership changes from a single admin app to separate `web-teacher` and `web-admin` app surfaces.
- `production-readiness-governance`: Validation and deployment documentation must prove three frontend services plus the web-admin token boundary and teacher role compatibility.
- `production-engineering-quality`: Compose/service validation must use the canonical `web-admin`, `web-teacher`, and `web-student` service names.

## Impact

- `apps/admin-web` package metadata, source labels, auth guard behavior, learning assistant route visibility, and build output semantics.
- New `apps/web-admin` frontend package with Ant Design account-management workbench.
- Backend web-admin config-token checks and a new web-admin teacher-account router/service.
- `app_users` usage for `role`, `status`, `password_hash`, `must_change_password`, and `password_version`.
- Docker Compose frontend services, frontend runtime configuration, `.env.example`, README, and service validation scripts.
- Backend tests for config-token-only APIs and frontend typecheck/build coverage for all three web apps.
