## Why

Teachers need a way to inspect the real student H5 experience from the teacher console without separately logging in to the student frontend or asking students to demonstrate screens. The current point-level catalog preview proves the iframe/device-shell direction, but it is limited to one point page and cannot exercise full student navigation, common interactions, or future controlled preview-only differences.

This change introduces a DevTools-like phone preview shell that embeds the real `web-student` app through a teacher-owned test-student session. It preserves one student frontend codebase while adding explicit preview policy, hidden preview roster ownership, and web-admin governance so the implementation does not become a duplicated or forked student UI.

## What Changes

- Add a teacher-console student device preview page that renders a curated phone emulator shell with device presets, orientation, zoom, refresh, and external-open controls.
- Embed the real `web-student` SPA in the preview shell via iframe; teacher-side code MUST NOT recreate, import, or fork student learning pages.
- Add teacher-preview session APIs that create or reuse one default hidden preview class and one default test student per teacher, then issue a short-lived bootstrap ticket for the student app.
- Add a student preview bootstrap route that exchanges the ticket for a preview student session and then runs the normal student router and shell.
- Add preview-mode policy plumbing so future differences from the real student frontend are expressed through backend policy, app-config feature gates, route guards, and API write guards instead of page-by-page preview forks.
- Add a student-side preview sandbox adapter boundary so teacher-preview presentation and write-interaction differences are centralized instead of hard-coded in ordinary student pages.
- Allow web-admin to view, audit, reset, and manage hidden preview classes/test students while keeping those classes invisible to ordinary teacher class workflows.
- Keep student-side writes isolated to preview/test-student behavior and make sensitive or unsupported features blockable without mutating normal student data or teacher-authored content.
- Preserve and eventually supersede the existing point-level preview path by reusing the same device shell and real-student-page principle where possible.

## Capabilities

### New Capabilities

- `teacher-student-device-preview`: Defines the end-to-end teacher phone preview, teacher-owned test student session, real `web-student` iframe runtime, preview policy/guard model, and verification expectations.

### Modified Capabilities

- `class-roster-management`: Hidden teacher-preview classes and test students must be excluded from ordinary teacher class/roster workflows while remaining auditable through platform administration.
- `web-console-product-boundaries`: `web-admin` expands from teacher-account management only to include platform governance for teacher-preview classes/test students without duplicating teacher learning workflows.
- `web-console-role-boundaries`: Clarifies that platform operators can manage preview infrastructure in `web-admin`, while teachers use only the preview shell in `web-teacher`.
- `backend-admin-router-ownership`: Adds platform-owned `/api/web-admin/*` endpoints for preview class/test-student governance and teacher-owned `/api/admin/student-preview/*` endpoints for session creation.

## Impact

- Affected teacher frontend:
  - `apps/web-teacher/src/app/routes.tsx` and `AdminApp.tsx` for a new lazy route.
  - New `apps/web-teacher/src/features/student-preview/*` modules for the device shell, toolbar, iframe, API hook, and feature-local styles.
  - Existing `CatalogPointPreviewWindow` device preset/frame logic may be extracted or shared through a teacher-owned preview module rather than copied.
- Affected student frontend:
  - `apps/web-student/src/App.tsx`, router configuration, and API/auth helpers for preview bootstrap and preview-runtime context.
  - Student pages remain canonical; changes should be limited to runtime extension points, route guards, app-config/policy handling, preview sandbox adapters, and shared API/command behavior.
- Affected backend:
  - New teacher-preview session service and router under teacher/admin API ownership.
  - New web-admin governance endpoints under the platform web-admin router namespace.
  - Roster/class domain support for hidden preview classes and teacher-owned test students.
  - Student auth/token helpers for preview-session claims and ticket exchange.
  - Preview policy enforcement in student app-config and sensitive student write endpoints.
- Affected web-admin:
  - New platform operations surface for hidden preview classes and test students, scoped to audit/reset/manage actions.
- Affected data model:
  - Class and roster/account records need explicit preview/system classification and teacher ownership metadata.
  - Preview/test-student records must be excluded from ordinary teacher class lists and normal learning analytics unless a future explicit admin diagnostic requests them.
- Dependencies:
  - No browser DevTools embedding is required.
  - The teacher frontend may reuse existing `react-device-mockup` and `motion`; `@use-gesture/react` is optional for shell-level zoom/pan gestures only.
