## 1. Data Model and Domain Foundations

- [x] 1.1 Add a migration for explicit preview/system classification on classes and preview test-student records, including teacher owner metadata and required indexes or unique constraints.
- [x] 1.2 Add domain constants/types for preview class purpose, preview account purpose, and teacher-student-device-preview session purpose.
- [x] 1.3 Implement an idempotent service to ensure one active hidden preview class exists for a teacher.
- [x] 1.4 Implement an idempotent service to ensure one active preview test student exists for a teacher's hidden preview class.
- [x] 1.5 Add reset/disable/restore service operations for preview class/test-student infrastructure without touching instructional classes.
- [x] 1.6 Add backend tests for preview class/test-student creation, reuse, uniqueness, reset, and ownership isolation.

## 2. Backend Session, Policy, and Guards

- [x] 2.1 Add a teacher-console route under `/api/admin/student-preview/*` that creates a short-lived student preview bootstrap ticket.
- [x] 2.2 Add a student preview ticket exchange route that accepts only valid preview tickets and returns a student-compatible preview session.
- [x] 2.3 Add preview claims to the issued session, including teacher owner id, preview class id, preview student id, preview purpose, and expiry.
- [x] 2.4 Add preview policy resolution for the test-student session, including initial blocked/allowed feature decisions for feedback, account mutation, assessment, assistant, and analytics side effects.
- [x] 2.5 Enforce server-side guards on blocked preview write endpoints so frontend hiding is never the only protection.
- [x] 2.6 Ensure allowed preview interactions write only to preview/test-student state or return controlled preview responses according to policy.
- [x] 2.7 Add backend tests for ticket expiry, ticket reuse rejection, teacher authorization, student exchange behavior, and blocked preview writes.

## 3. Teacher Class and Analytics Exclusions

- [x] 3.1 Update ordinary teacher class list APIs to exclude teacher-preview classes by default.
- [x] 3.2 Update ordinary teacher roster APIs to exclude preview test students by default.
- [x] 3.3 Update class counts and roster metrics used by teacher workflows to ignore preview classes/test students.
- [x] 3.4 Update normal learning analytics/report queries to exclude preview classes/test students by default.
- [x] 3.5 Add backend tests proving preview classes and test students do not appear in teacher class cards, roster tables, class counts, or normal analytics.

## 4. Web-Admin Preview Infrastructure Governance

- [x] 4.1 Add platform-owned `/api/web-admin/*` endpoints for listing preview classes/test students with teacher owner and status metadata.
- [x] 4.2 Add web-admin endpoints for resetting, disabling, restoring, or recreating a teacher's preview test student.
- [x] 4.3 Keep web-admin preview governance endpoints behind the configured web-admin platform authorization.
- [x] 4.4 Add a `web-admin` feature page for preview infrastructure governance using platform operations UI patterns rather than teacher workflow components.
- [x] 4.5 Add web-admin tests for list rendering, reset action behavior, authorization rejection, and absence of teacher learning workflow imports.

## 5. Student Frontend Preview Runtime

- [x] 5.1 Add a student preview bootstrap route such as `/preview/session` that exchanges the backend ticket and then redirects into normal student routes.
- [x] 5.2 Decide and implement preview token storage so preview sessions do not accidentally corrupt normal student login state in the same browser.
- [x] 5.3 Extend student auth/API helpers to recognize preview sessions without weakening normal student authentication.
- [x] 5.4 Extend student app-config/runtime context with `previewMode` and `previewPolicy`.
- [x] 5.5 Add centralized route guard or route visibility handling for preview-blocked routes.
- [x] 5.6 Add shared blocked-feature UI copy/state for preview-only unavailable actions.
- [x] 5.7 Add student frontend tests for preview bootstrap success, invalid ticket state, runtime policy exposure, route blocking, and normal student login preservation.
- [x] 5.8 Keep preview feedback entry/page editable while intercepting submit with a preview-mode dialog, and show a stable preview profile identity for teacher guidance.

## 6. Teacher Frontend Device Preview Shell

- [x] 6.1 Add a lazy teacher route for the full student preview page without eagerly loading preview-only dependencies in the teacher shell.
- [x] 6.2 Create a feature-owned student-preview API client/hook for requesting preview sessions.
- [x] 6.3 Extract or share device preset/frame primitives from the existing catalog point preview instead of duplicating device-shell code.
- [x] 6.4 Build the preview toolbar with device preset, orientation, zoom, refresh, and open-in-window controls.
- [x] 6.5 Build the iframe stage with allowed-origin URL validation, controlled loading/error states, and refresh-by-key behavior.
- [x] 6.6 Add teacher frontend tests for session request, iframe URL handling, device controls, refresh behavior, and external-open behavior.

## 7. Product Boundary and Maintainability Checks

- [x] 7.1 Add or update import-boundary validation so `web-teacher` preview modules cannot import `web-student` route pages, feature components, CSS files, or router internals.
- [x] 7.2 Add source or test coverage confirming student business pages are not recreated inside the teacher preview feature.
- [x] 7.3 Keep preview-only student logic centralized in bootstrap, runtime context, route guard, app-config, and API helpers unless a task documents a narrow page-local exception.
- [x] 7.4 Keep backend route handlers thin by moving SQL-heavy preview class, ticket, policy, and reset behavior into services.
- [x] 7.5 Document any accepted page-local preview exception and its tests in implementation notes before marking the change complete.

## 8. Security, Configuration, and Deployment

- [x] 8.1 Add configuration for student preview base URL and allowed iframe origins across local and production-like deployments.
- [x] 8.2 Add CSP/frame-ancestor or equivalent policy updates that allow only the expected teacher/student preview framing relationship.
- [x] 8.3 Add session/ticket expiry configuration and tests for expired preview sessions.
- [x] 8.4 Add audit metadata for preview session creation and web-admin reset operations where existing audit patterns allow.
- [x] 8.5 Update relevant docs or environment examples for teacher preview URL/origin configuration.

## 9. Verification and QA

- [x] 9.1 Run backend tests covering preview class services, session exchange, route ownership, teacher exclusions, web-admin governance, and preview write guards.
- [x] 9.2 Run `npm run typecheck --prefix apps/web-student` and focused student preview tests.
- [x] 9.3 Run `npm run typecheck --prefix apps/web-teacher`, focused teacher preview tests, and teacher import-boundary validation.
- [x] 9.4 Run `npm run typecheck --prefix apps/web-admin` and focused web-admin preview governance tests.
- [x] 9.5 Run production builds for affected frontend apps or document concrete blockers.
- [x] 9.6 Run browser or screenshot QA for the teacher preview page covering iPhone preset, Android preset, orientation switch, iframe refresh, and normal student route navigation.
- [x] 9.7 Run `openspec validate add-teacher-student-device-preview --strict`.
- [x] 9.8 Run `git diff --check` and fix whitespace issues before implementation is considered complete.
- [x] 9.9 Run focused browser QA for the preview profile-to-feedback flow and confirm no feedback API write is attempted.

## 10. Preview Sandbox Boundary Hardening

- [x] 10.1 Add a dedicated `web-student` preview sandbox adapter module for teacher-preview presentation and interaction decisions.
- [x] 10.2 Move fixed teacher-preview profile presentation (`00000000`, `施测平`, `数智一班`) out of profile route components and into the preview adapter.
- [x] 10.3 Move feedback entry capability and feedback submit interception out of route/form components and into a preview-aware capability or command guard.
- [x] 10.4 Add focused student frontend tests proving normal student profile/feedback behavior still bypasses the preview adapter decisions and calls the real submit API.
- [x] 10.5 Add source-boundary validation that flags raw `previewMode`, `user.preview_mode`, preview purpose strings, or hard-coded preview identities in ordinary student route/feature modules.
- [x] 10.6 Document any remaining page-local preview exception with a concrete reason, owner, test coverage, and removal path.
- [x] 10.7 Re-run OpenSpec validation, student e2e tests, student typecheck, backend preview tests, browser QA for profile-to-feedback, and `git diff --check` after the adapter hardening.
