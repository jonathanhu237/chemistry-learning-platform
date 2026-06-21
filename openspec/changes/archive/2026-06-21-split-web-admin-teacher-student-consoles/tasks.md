## 1. OpenSpec and Repository Boundary

- [x] 1.1 Validate proposal, design, and spec deltas with `openspec validate split-web-admin-teacher-student-consoles --strict`.
- [x] 1.2 Rename frontend app directories/package semantics to `web-admin`, `web-teacher`, and `web-student`.

## 2. Backend Platform Admin Account Management

- [x] 2.1 Add backend web-admin config-token auth and teacher-console role helpers.
- [x] 2.2 Implement `/api/web-admin/teacher-accounts` list/create/patch/reset-password/delete routes backed by `app_users`.
- [x] 2.3 Ensure teacher account responses omit `password_hash`, create uses `role='admin'`, delete soft-disables accounts, and password reset increments `password_version`.
- [x] 2.4 Register the web-admin router in the backend runtime.
- [x] 2.5 Add backend tests for config-token authorization, CRUD, soft delete, password reset token invalidation versioning, and invalid-token rejection.

## 3. Teacher Console Refactor

- [x] 3.1 Remove `adminOnly` learning-assistant navigation and non-admin teacher redirects from the teacher frontend.
- [x] 3.2 Update teacher frontend package, labels, auth role types, and copy from admin-web semantics to web-teacher semantics.
- [x] 3.3 Keep legacy `teacher` users compatible while ensuring all teacher-console roles see complete functionality.

## 4. Platform Web Admin Frontend

- [x] 4.1 Create the `apps/web-admin` React + TypeScript + Ant Design app with green theme and focused account-management shell.
- [x] 4.2 Add web-admin API client, token login guard, teacher-account table, create/edit role/status/reset/delete interactions, and safe response handling.
- [x] 4.3 Add web-admin package scripts for dev/typecheck/build.

## 5. Deployment, Docs, and Validation Metadata

- [x] 5.1 Update Docker Compose service names, frontend app build args, default ports, and allowed origins for `web-admin`, `web-teacher`, and `web-student`.
- [x] 5.2 Update `.env.example`, README, and validation scripts/documentation references from admin-web/student-web to web-teacher/web-student/web-admin.
- [x] 5.3 Update any frontend Docker/runtime package references needed by the renamed apps.
- [x] 5.4 Add a deployment script that builds the canonical Compose stack, removes obsolete service containers, and runs post-deploy smoke validation.

## 6. Verification

- [x] 6.1 Run relevant backend tests for auth and web-admin teacher-account APIs.
- [x] 6.2 Run `web-admin` typecheck and build.
- [x] 6.3 Run `web-teacher` typecheck and build.
- [x] 6.4 Run `web-student` typecheck and build.
- [x] 6.5 Re-run OpenSpec strict validation and review repository diff for unintended files.
- [x] 6.6 Deploy the Compose stack and verify `web-admin`, `web-teacher`, and `web-student` containers are running and healthy.
