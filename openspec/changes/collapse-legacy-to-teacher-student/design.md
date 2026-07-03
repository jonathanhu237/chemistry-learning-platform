## Context

The previous legacy runtime reshape made the old student and teaching-management products the only browser-facing apps on the `legacy` branch. The branch still has mixed vocabulary and contracts from earlier product lines:

```text
Current legacy branch after runtime reshape

apps/web-student       student-facing old product
apps/web-backoffice    teaching-management old product

roles                  admin | teacher | student, with platform_admin remnants
teacher API            /api/admin/*
token operations API   /api/web-admin/*
student API            /api/student/*
```

The user decision for this version is intentionally simpler than a multi-teacher SaaS model:

```text
Target legacy product model

apps/web-teacher       global teaching-management backend
apps/web-student       student-facing learning product

roles                  teacher | student
teacher API            /api/teacher/*
student API            /api/student/*
```

`teacher` is a global teaching-administrator identity in this legacy version. It is not a tenant-isolated instructor identity, and the branch will not support per-teacher class ownership, teacher-specific student visibility, or multi-teacher data isolation in this change.

## Goals / Non-Goals

**Goals:**
- Rename `web-backoffice` to `web-teacher` across app directory, package metadata, Compose service names, CI, docs, and validation.
- Collapse canonical roles to `teacher` and `student`.
- Migrate existing `admin` and `platform_admin` account rows to `teacher`.
- Replace teacher-facing `/api/admin/*` browser/API contracts with `/api/teacher/*`.
- Remove token-based `/api/web-admin/*` operations endpoints and `WEB_ADMIN_ACCESS_TOKEN` from the legacy runtime.
- Keep the student product on `web-student`, `student` role, and `/api/student/*`.
- Make tests, route inventory, and OpenSpec specs enforce the new vocabulary rather than tolerating old names.

**Non-Goals:**
- Do not implement multi-teacher isolation, scoped admin permissions, class ownership filtering, or per-teacher feature permissions.
- Do not preserve `/api/admin/*`, `/api/web-admin/*`, `admin`, or `platform_admin` as supported compatibility contracts.
- Do not rewrite historical migration files; add a new migration for data and constraint changes.
- Do not redesign the old student learning flows beyond keeping them compatible with `student` auth.
- Do not rename every internal Python module in one risky mechanical pass unless it is necessary to remove public contracts; internal names can be cleaned when touched, but tests and public route names must not expose old contracts.

## Decisions

1. **Use `teacher` and `student` as the only canonical roles.**
   - Decision: `app_users.role` SHALL only allow `teacher` and `student` after the new migration.
   - Rationale: This matches the two product entries and removes ambiguity around `admin` versus `teacher`.
   - Alternative considered: Keep `admin` and `student`. Rejected because the product language is teacher/student and the user wants symmetrical identities.
   - Alternative considered: Keep `admin`, `teacher`, and `student`. Rejected because this version has no multi-teacher or scoped-admin requirement.

2. **Treat `teacher` as global teaching administration.**
   - Decision: Any authenticated `teacher` can access all teacher product workflows and all teaching data.
   - Rationale: The current version has no requirement to isolate multiple teachers, and pretending otherwise would add complexity without product need.
   - Alternative considered: Scoped teacher access through `teacher_classes`. Rejected for this version; it can be a future change if multi-teacher use becomes real.

3. **Rename the app to `web-teacher`, not `web-backoffice`.**
   - Decision: `apps/web-backoffice` becomes `apps/web-teacher`; Compose and validation use service `web-teacher`.
   - Rationale: The role is `teacher`, and the legacy product pair becomes easy to understand: `web-teacher` and `web-student`.
   - Alternative considered: Keep `web-backoffice` while role is `teacher`. Rejected because it keeps a product-name mismatch immediately after an identity cleanup.

4. **Move teacher browser API contracts to `/api/teacher/*`.**
   - Decision: Teacher-facing frontend calls and backend route registration move from `/api/admin/*` to `/api/teacher/*`.
   - Rationale: Keeping `/api/admin/*` would preserve the old `admin` mental model and violate the no-technical-debt direction.
   - Alternative considered: Add `/api/teacher/*` aliases while retaining `/api/admin/*`. Rejected because the user explicitly does not want compatibility debt.

5. **Remove token operations routes rather than migrating the UI.**
   - Decision: `/api/web-admin/*` and `WEB_ADMIN_ACCESS_TOKEN` are removed from the legacy runtime. Teacher account creation remains script/bootstrap driven in this version.
   - Rationale: There is no standalone operations product after the legacy runtime collapse, and the user accepted script/bootstrap account management.
   - Alternative considered: Move teacher-account management into `web-teacher`. Rejected for this change because it expands the product surface; bootstrap is enough for the current need.

6. **Use a forward migration for role data and constraints.**
   - Decision: Add a new migration that converts `admin` and `platform_admin` rows to `teacher`, updates role constraints, and removes/neutralizes platform-admin-only assumptions.
   - Rationale: Historical migrations are identity records and should remain immutable.
   - Alternative considered: Edit `022_platform_admin_role.sql`. Rejected because historical migrations must not be rewritten.

7. **Route inventory becomes the source of truth.**
   - Decision: Backend route inventory and tests must assert absence of `/api/admin/*` and `/api/web-admin/*` and presence of `/api/teacher/*` for teacher workflows.
   - Rationale: The branch has many old specs and modules; route inventory prevents hidden compatibility routes from surviving.

## Risks / Trade-offs

- **Risk: The name `teacher` later implies multi-teacher isolation.** -> Mitigation: Document in ADR/specs that `teacher` is global in this legacy version and multi-teacher isolation requires a separate change.
- **Risk: Removing `/api/admin/*` breaks untracked clients.** -> Mitigation: The legacy branch supports only repository-managed `web-teacher` and `web-student`; update all tracked frontend calls and tests in the same change.
- **Risk: Existing seed data contains `admin` or `platform_admin` roles.** -> Mitigation: Add data migration and update seed/bootstrap scripts to emit `teacher`.
- **Risk: `/api/web-admin/*` tests and route inventory currently assert token operations routes.** -> Mitigation: Update tests to assert removal and replace any required teacher bootstrap coverage with script-level tests.
- **Risk: Internal module names still contain `admin` after public cleanup.** -> Mitigation: Treat public contracts as mandatory cleanup; internal names can remain only if they are not user-facing, not route-facing, and not documented as canonical. Prefer opportunistic module renames where blast radius is manageable.
- **Risk: Completed historical specs still describe older product lines.** -> Mitigation: This change updates current requirements for the legacy branch; historical archived context remains historical, but active specs and README/operations docs must describe the teacher/student model.

## Migration Plan

1. Add a migration that maps `app_users.role IN ('admin', 'platform_admin')` to `teacher` and changes the role check constraint to `teacher | student`.
2. Update auth helpers so teacher product authorization accepts only active `teacher` users and student authorization accepts only active `student` users.
3. Rename `apps/web-backoffice` to `apps/web-teacher` and update package metadata, title, storage keys, tests, CI, Compose, docs, and validation scripts.
4. Move backend teacher routers from `/api/admin/*` to `/api/teacher/*` and update the frontend API client/tests.
5. Remove `/api/web-admin/*` router registration, token auth helper usage, `WEB_ADMIN_ACCESS_TOKEN` settings, and token-console tests/docs.
6. Update bootstrap scripts and seed validation so the bootstrap account is a `teacher` account.
7. Regenerate or update route inventory to make `/api/teacher/*` canonical and reject `/api/admin/*`/`/api/web-admin/*`.
8. Run frontend validation for `apps/web-teacher` and `apps/web-student`, focused backend auth/route tests, route inventory validation, Compose config/smoke, and OpenSpec validation.

Rollback is a normal git rollback plus database restore or a deliberate reverse migration if the role migration has been applied to a shared database.

## Glossary

- **Teacher**: The global teaching-management identity in this legacy branch. A teacher can access all teacher product workflows and all teaching data.
- **Student**: The learner identity for `web-student`. A student can access only their own student session, learning, assessment, and report data.
- **web-teacher**: The legacy teaching-management frontend, formerly `web-backoffice` and before that old teacher product code.
- **web-student**: The legacy student learning frontend.
- **Teacher API**: Browser-facing backend contract under `/api/teacher/*`.
- **Student API**: Browser-facing backend contract under `/api/student/*`.
- **Token operations API**: The retired `/api/web-admin/*` surface that was authorized by `WEB_ADMIN_ACCESS_TOKEN`.

## Open Questions

- Should the bootstrap script be renamed from `bootstrap_admin.py` to `bootstrap_teacher.py`, or should the existing filename remain temporarily while its behavior creates teacher accounts? Default recommendation: rename it if references are manageable.
- Should internal Python modules under `server/app/api/admin/` be renamed to `server/app/api/teacher/` in the same change? Default recommendation: yes for route owners with frontend contracts, while avoiding unrelated deep domain renames unless tests remain tractable.
