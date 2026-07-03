## Why

The legacy branch now runs only the old student product and the old teaching-management product, but its contracts still carry `admin`, `platform_admin`, `web-backoffice`, `/api/admin/*`, and `/api/web-admin/*` concepts from earlier product splits. This change removes that mismatch by making the legacy branch a clean two-identity system: `teacher` and `student`.

## What Changes

- **BREAKING**: Rename the canonical backend-facing frontend from `web-backoffice` to `web-teacher`.
- **BREAKING**: Collapse canonical application roles to `teacher` and `student`.
- **BREAKING**: Migrate existing `admin` and `platform_admin` users to `teacher` or remove/disable obsolete platform-token-only access paths.
- **BREAKING**: Replace teacher-facing `/api/admin/*` browser contracts with `/api/teacher/*`.
- **BREAKING**: Remove `/api/web-admin/*` token-authorized platform operations endpoints and `WEB_ADMIN_ACCESS_TOKEN` from the legacy runtime.
- Treat `teacher` as a global teaching administrator in this legacy version; no multi-teacher data isolation, class ownership scoping, or per-teacher tenancy is supported.
- Keep `web-student` and `/api/student/*` as the student-facing product and API surface.
- Update Compose, validation scripts, package metadata, docs, route inventory, and tests to use `web-teacher`, `web-student`, `/api/teacher/*`, `/api/student/*`, and `teacher | student`.
- Keep historical migrations immutable; add a new migration to collapse role data and role constraints.

## Capabilities

### New Capabilities
- `legacy-teacher-student-identity`: Defines the legacy branch as a two-identity system with global `teacher` access and self-scoped `student` access.

### Modified Capabilities
- `web-console-product-boundaries`: Replace current three-console and backoffice naming requirements with canonical `web-teacher` and `web-student` legacy products.
- `web-console-role-boundaries`: Replace `admin`/`teacher`/`platform_admin` console rules with `teacher` and `student` identity boundaries.
- `backend-admin-router-ownership`: Replace teacher-facing `/api/admin/*` and token-based `/api/web-admin/*` contracts with `/api/teacher/*` ownership.
- `split-frontend-deployment`: Require the legacy deployment topology to build and serve only `web-teacher` and `web-student` frontend services.
- `bkt-legacy-competition-profile`: Update the old competition profile to use `web-teacher` as the canonical teaching-management app and document that teacher access is global.
- `platform-teacher-account-management`: Retire token-based platform teacher-account management in favor of script/bootstrap-managed teacher accounts for this legacy branch.

## Impact

- Frontend apps: `apps/web-backoffice` is renamed to `apps/web-teacher`; package names, document titles, local storage keys, tests, and API clients are updated.
- Backend API: teacher product routes move from `/api/admin/*` to `/api/teacher/*`; `/api/web-admin/*` routes are removed from production app wiring.
- Auth and data: `app_users.role` canonical values become `teacher` and `student`; existing `admin` and `platform_admin` rows migrate to `teacher`.
- Configuration: `WEB_ADMIN_ACCESS_TOKEN` and web-admin token validation are removed from settings, docs, Compose, tests, and production validation.
- Validation: route inventory, focused backend tests, frontend typecheck/tests/build, Compose config/smoke, and OpenSpec validation must be updated and pass.
