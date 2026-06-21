## Context

The repository currently has two frontend apps: `apps/student-web` and `apps/admin-web`. The second app is already architecturally the teacher console: it owns experiment catalog editing, classes, learning resources, question banks, AI configuration, settings, analytics, and the learning assistant test surface. Its route guards and nav metadata still treat `role='admin'` as a privileged feature role and hide some teacher-facing modules, especially learning assistant.

The backend uses `app_users` for all app accounts and already stores `role`, `status`, `password_hash`, `must_change_password`, and `password_version`. `password_version` is already included in tokens and compared on authenticated requests, so teacher password resets can invalidate sessions without a new token model. The new split should reuse this table instead of adding a parallel teacher-account store.

Docker Compose currently exposes `student-web` on `5173` and `admin-web` on `5174`. Product semantics now require three surfaces:

```text
web-student  :5173  student H5
web-teacher  :5174  teacher console formerly apps/admin-web
web-admin    :5175  platform operations console for teacher-account management
```

## Goals / Non-Goals

**Goals:**

- Rename product/service/package semantics so the teacher console is `web-teacher`.
- Create a new `web-admin` frontend app with only teacher account management.
- Keep `web-student` available as the student frontend service.
- Add backend config-token semantics and isolate web-admin access to a long token stored in configuration.
- Add `/api/web-admin/teacher-accounts` endpoints for list/create/patch/reset-password/delete.
- Ensure teacher accounts created by web-admin use `role='admin'`.
- Treat historical `role='teacher'` as a login compatibility alias for the teacher console only, not as a feature-limiting role.
- Remove role-based feature hiding and learning-assistant redirects inside `web-teacher`.
- Update documentation, environment examples, service names, package names, and tests.

**Non-Goals:**

- Do not decompose the large teacher feature modules beyond the permissions and naming changes required here.
- Do not build platform-operations management of students, classes, experiments, questions, AI configuration, media, or logs.
- Do not change the student H5 route stack or mobile design.
- Do not introduce a new database table for platform or teacher accounts.
- Do not return password hashes or expose password hash mutation directly to frontend code.

## Decisions

### Decision: Rename app directories to match product boundaries

The current teacher app will move from `apps/admin-web` to `apps/web-teacher`. The student app will move from `apps/student-web` to `apps/web-student`. The new platform console will live at `apps/web-admin`.

Rationale:

- Directory, package, build command, and Compose names align with the product names users and operators now see.
- It prevents new code from accidentally treating the teacher console as the platform admin console.

Alternative considered: keep `apps/admin-web` and only rename package/service labels. Rejected because future contributors would keep reading the directory name as the platform app.

### Decision: Add web-admin API under `/api/web-admin`

The new platform console will call `/api/web-admin/teacher-accounts`. These routes will not live under `/api/admin`, because `/api/admin` is already the teacher-console API namespace.

Rationale:

- Backend route namespaces match product surfaces.
- Tests can assert config-token-only authorization without confusing it with existing teacher APIs.

Alternative considered: add account routes under `/api/admin/platform`. Rejected because it preserves the old naming ambiguity.

### Decision: Reuse `app_users` and add role semantics in code

Teacher accounts created through web-admin token requests will be inserted into `app_users` with `role='admin'`, `status='active'`, hashed password, `must_change_password=true` by default, and `password_version=1`. Password reset will update `password_hash`, set `must_change_password` according to the request/default policy, and increment `password_version`.

Rationale:

- The table already supports every required field.
- Existing token invalidation already depends on `password_version`.
- This keeps migration risk low and avoids a duplicate identity source.

Alternative considered: add a `teacher_accounts` table. Rejected because it would duplicate login data and require synchronization.

### Decision: Keep `teacher` as compatibility only

`role='teacher'` users may still authenticate to `web-teacher` and use the teacher API routes that already allow `admin`/`teacher`, but `web-teacher` UI must not use that role to hide features. New accounts are created with `role='admin'`.

Rationale:

- Historical accounts keep working.
- The product no longer has partial teacher-console feature tiers.
- The future migration path can update old teacher rows to `admin` without changing UI behavior.

Alternative considered: migrate all `teacher` rows immediately and stop accepting them. Rejected because existing deployments may still contain those rows and the change does not require a destructive data migration.

### Decision: Web-admin login accepts only the configured access token

The `web-admin` frontend will not use the shared username/password login endpoint. It stores the configured long token locally and sends it as a Bearer token to `/api/web-admin/*`; the backend compares it against `WEB_ADMIN_ACCESS_TOKEN`. The teacher console guard still rejects students and any platform-only role, while allowing `admin` and legacy `teacher`.

Rationale:

- Backend authorization is the security boundary.
- A single deployment-scoped token keeps the platform operations surface separate from teacher-console accounts.
- Frontend token storage provides the right product experience but does not replace backend checks.

Alternative considered: use `role='platform_admin'` app users and the shared auth endpoint. Rejected because the platform operations console now uses a deployment config token instead of username/password accounts.

### Decision: Web-admin is a focused desktop workbench

`web-admin` will use React, TypeScript, Ant Design, React Query, and the existing green visual language, but it will only implement account management. It will not import teacher feature modules or their heavy dependencies.

Rationale:

- Keeps the platform console small and auditable.
- Avoids accidentally exposing teacher workflows inside the platform console.

Alternative considered: reuse the teacher shell and hide all unrelated routes. Rejected because it keeps the products coupled and risks route leakage.

## Risks / Trade-offs

- Old scripts or documentation may still reference `admin-web` or `student-web` -> Update Compose, README, env examples, and package names; use repository search before final validation.
- Legacy `teacher` behavior can leak into new account creation -> Tests assert created teacher-console accounts use `role='admin'`.
- Password reset may fail to invalidate tokens if `password_version` is not incremented -> Backend tests assert the version increments.
- Platform routes could accidentally expose `password_hash` -> Response schemas omit the field and tests assert it is absent.
- Duplicating frontend dependencies in a new package increases install/build cost -> Keep `web-admin` minimal and reuse only necessary dependencies.
- Some backend teacher APIs still distinguish admin/teacher for data ownership, especially class ownership -> This change removes teacher-console feature visibility restrictions; deeper data ownership migrations can be handled separately if required.

## Migration Plan

1. Create OpenSpec deltas and validate strict format.
2. Move frontend directories to `apps/web-teacher` and `apps/web-student`; add new `apps/web-admin`.
3. Add backend web-admin router/service, config-token auth, and teacher role helpers.
4. Remove `web-teacher` UI role-based feature hiding and learning-assistant redirects.
5. Update Compose/env/docs/scripts to canonical service names and ports.
6. Add backend tests for config-token access, CRUD, soft delete, password reset, and response shape.
7. Run backend tests and frontend typecheck/build for `web-admin`, `web-teacher`, and `web-student`.

Rollback is a git/deployment rollback. Do not add compatibility containers named `admin-web`; the product names are intentionally changed.

## Open Questions

- Existing seed/bootstrap scripts may create `role='admin'` accounts that are now teacher-console accounts. This implementation will preserve that behavior; production operators must set `WEB_ADMIN_ACCESS_TOKEN` before using `web-admin`.
