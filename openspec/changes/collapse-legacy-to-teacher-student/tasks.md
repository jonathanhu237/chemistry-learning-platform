## 1. Role And Auth Collapse

- [x] 1.1 Add a forward migration that converts existing `admin` and `platform_admin` users to `teacher`.
- [x] 1.2 Update the `app_users.role` constraint and seed expectations to allow only `teacher` and `student`.
- [x] 1.3 Replace teacher-product auth helpers so teacher routes accept only active `teacher` users.
- [x] 1.4 Confirm student auth remains `student`-only and rejects teacher sessions for student-only data.
- [x] 1.5 Remove `WEB_ADMIN_ACCESS_TOKEN` from settings, validation, environment examples, Compose, and docs.
- [x] 1.6 Update bootstrap/account scripts so the supported setup path creates or updates `teacher` accounts.

## 2. Frontend Product Rename

- [x] 2.1 Rename `apps/web-backoffice` to `apps/web-teacher`.
- [x] 2.2 Update teacher frontend package names, lockfile metadata, document title, local storage keys, and tests.
- [x] 2.3 Update teacher frontend API client calls from `/api/admin/*` to `/api/teacher/*`.
- [x] 2.4 Update Compose service, image names, host variables, CI paths, validation scripts, and README references from `web-backoffice` to `web-teacher`.
- [x] 2.5 Verify `apps/` contains only canonical active frontend packages `web-teacher` and `web-student`.

## 3. Teacher API Contract Migration

- [x] 3.1 Move teacher-facing backend route prefixes from `/api/admin/*` to `/api/teacher/*`.
- [x] 3.2 Remove `/api/admin/*` compatibility aliases from production app wiring and route inventory.
- [x] 3.3 Remove `/api/web-admin/*` token-operation routers and related tests.
- [x] 3.4 Update route inventory and backend architecture checks to treat `/api/teacher/*` as canonical.
- [x] 3.5 Update backend tests for classes, analytics, catalog, question bank, report prompts, legacy teacher demo, and auth to use `/api/teacher/*`.
- [x] 3.6 Remove or rewrite docs/spec references that present `/api/admin/*` or `/api/web-admin/*` as supported legacy contracts.

## 4. Legacy Product Semantics

- [x] 4.1 Document that `teacher` is a global teaching administrator in this legacy version.
- [x] 4.2 Remove teacher-scope or platform-admin UI/API affordances that imply multi-teacher tenancy or token operations.
- [x] 4.3 Keep legacy teacher workflows globally visible for authenticated teachers.
- [x] 4.4 Preserve existing `web-student` behavior and student API contracts under `/api/student/*`.

## 5. Validation

- [x] 5.1 Run `npm ci`, `npm run typecheck`, `npm test`, and `npm run build` for `apps/web-teacher`.
- [x] 5.2 Run `npm ci`, `npm run typecheck`, `npm test`, and `npm run build` for `apps/web-student`.
- [x] 5.3 Run focused backend auth and teacher/student route tests.
- [x] 5.4 Run backend route inventory and architecture validation.
- [x] 5.5 Run `docker compose config --services` and a Compose smoke check for the legacy runtime.
- [x] 5.6 Run `openspec validate collapse-legacy-to-teacher-student --strict`.
