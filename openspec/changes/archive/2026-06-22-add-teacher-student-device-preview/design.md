## Context

The repository already has three separate frontend products: `web-student` for the student H5 app, `web-teacher` for teacher workflows, and `web-admin` for platform operations. The student app owns mobile learning routes, shell context, auth token handling, app-config feature flags, assessment, assistant, feedback, catalog navigation, and styles. The teacher app already contains a point-level catalog preview window using `react-device-mockup` plus an iframe, and the backend already mints point-scoped preview tokens for draft point detail/media access.

The new requirement is broader: teachers need a page in the teacher console that behaves like a Chrome DevTools Device Mode subset for the full student app. The page is for visual review, interaction review, and guidance. Teachers do not need to select a real student identity, do not need to inspect preview writes in analytics, and do not need a browser debugger. Each teacher should get one default test student under a hidden preview class. Ordinary teacher class management must not show this hidden class; `web-admin` must be able to manage and audit it.

The key architectural constraint is that the teacher preview must not become a second student frontend. If student pages, styles, routes, or interaction logic change in `web-student`, the teacher preview must reflect those changes automatically. Any preview-only differences must be introduced through a small preview runtime layer, backend policy, route guards, and API write guards rather than component forks.

## Research Context: DevTools-Like Means External Control, Not Page Forks

Chrome DevTools Device Mode is useful as an architectural analogy, but not as a literal embeddable dependency. DevTools itself is an external control surface. It talks to Chromium through Chrome DevTools Protocol domains such as Emulation, Network, Runtime, and Page; the inspected webpage does not import DevTools UI components or carry page-local business branches for every emulated condition.

Relevant external patterns from the research:

- Chrome DevTools Protocol defines a remote debugging and instrumentation boundary between tooling and the page. Device emulation is expressed through browser-level commands such as device metrics, touch emulation, user agent, media, geolocation, orientation, CPU, and network controls.
- Chrome Device Mode documentation describes the feature as an approximation of mobile user experience rather than a real mobile runtime. It changes the environment around the page; it does not fork the application.
- Puppeteer `page.emulate()` and Playwright device descriptors follow the same principle: a device profile is applied to the browser context through viewport, user agent, screen size, device scale factor, mobile mode, and touch support. The application under test remains the same app.
- The DevTools frontend is open source, but it is a debugger UI coupled to Chromium protocol/backend assumptions. It is not a clean library for a teacher product surface and would introduce the wrong mental model for this feature.

The translation for this product is:

```text
web-teacher preview shell
  owns device chrome, preset, orientation, zoom, refresh, iframe lifecycle
        |
        v
iframe boundary
  runs the real web-student SPA
        |
        v
web-student preview sandbox adapter
  owns preview identity projection, capability decisions, mutation interception
        |
        v
backend preview policy and write guards
  owns security, isolation, hidden preview class/test-student state
```

The iframe/device shell is our replacement for browser-level DevTools control. The preview sandbox adapter is our replacement for CDP-style environment policy that cannot be injected from the browser in a normal web app. Student business pages should consume semantic adapters, not know the raw preview details.

## Goals / Non-Goals

**Goals:**

- Provide a teacher-console full student H5 preview that uses the real `web-student` SPA inside a phone-sized iframe shell.
- Give every teacher one system-managed hidden preview class and one default test student account/session.
- Keep hidden preview classes invisible in ordinary teacher class/roster workflows while making them visible and manageable in `web-admin`.
- Support future preview-only differences, such as allowing feedback form interaction while blocking real submit side effects, without copying student pages or sprinkling page-local preview branches.
- Keep preview implementation route-owned and feature-local so teacher shell, student shell, backend routers, and web-admin remain maintainable.
- Preserve existing point-preview behavior where practical by extracting reusable device-shell primitives instead of duplicating device preset code.

**Non-Goals:**

- Do not embed Chrome DevTools or expose DOM/network/debugger tools inside the teacher console.
- Do not simulate full browser-level emulation such as real user-agent override, CPU throttling, network shaping, native virtual keyboard, or browser chrome.
- Do not import student business page components into `web-teacher` or recreate student UI markup in teacher modules.
- Do not allow teachers to choose arbitrary real student identities in this change.
- Do not require preview writes to appear in teacher analytics, student reports, or class learning dashboards.
- Do not redesign the student H5 visual system as part of this change.

## Decisions

### Decision 1: Use an iframe shell around the real student SPA

The teacher preview page will be a `web-teacher` feature module that owns only the device shell, toolbar, iframe lifecycle, preview-session request, and shell-level styles. The iframe `src` will point at a `web-student` preview bootstrap URL returned by the backend, for example `/preview/session?ticket=...`.

The device shell may reuse or extract logic from the existing catalog point preview window:

- curated iPhone/Android presets
- portrait/landscape dimensions
- zoom levels
- refresh-by-key iframe reload
- external-open command
- optional shell-level drag/zoom gestures

The iframe content remains the real student app. The teacher preview shell does not render student pages, does not import student route components, and does not own student feature state.

Alternatives considered:

- Embedding Chrome DevTools frontend: rejected because it is a debugger UI, not a teacher product surface, and most device emulation powers rely on browser internals/CDP rather than normal web app code.
- Rebuilding student pages inside `web-teacher`: rejected because it creates a permanent duplicate UI that will drift from student code and styles.
- Using module federation to mount student React components in teacher React: rejected for this phase because it would couple two app runtimes, routers, providers, package versions, and CSS cascades. An iframe keeps product boundaries cleaner and matches the existing preview direction.

### Decision 2: Bootstrap through a teacher-owned test student session

The teacher app requests a preview session from a teacher-console endpoint:

`POST /api/admin/student-preview/session`

The backend verifies the teacher-console user, ensures a hidden preview class and test student exist for that teacher, mints a short-lived one-time ticket, and returns the student preview URL plus expiry metadata. The student app opens `/preview/session?ticket=...`, exchanges the ticket through a preview endpoint, stores the returned student preview token with the normal student auth mechanism or an explicit preview token slot, and redirects to `/home`.

The resulting request context is still a student role/session, but it carries preview claims such as:

- `preview: true`
- `preview_purpose: teacher_student_device_preview`
- `teacher_user_id`
- `preview_class_id`
- `preview_student_id`
- ticket/session expiry

This keeps the existing student API and router behavior usable while giving backend policy enough context to block, rewrite, or isolate unsupported preview actions.

Alternatives considered:

- Teacher token directly calls student APIs: rejected because existing student route contracts correctly reject teacher/admin roles and should not be weakened.
- Public unauthenticated preview API for every student endpoint: rejected because it would duplicate the student API surface and increase authorization risk.
- Requiring teachers to manually log into a test student: rejected because it defeats the goal of a one-click teacher workflow.

### Decision 3: Model hidden preview classes explicitly

Preview classes and preview students should be ordinary-enough records to reuse roster/student auth infrastructure, but they must be explicitly classified as system preview data. The exact schema can be chosen during implementation, but it must support:

- a class purpose/type such as `teacher_preview`
- owner teacher user id
- system-managed flag
- visibility or listing scope
- preview student account/roster classification
- stable one-to-one teacher to preview class/test student mapping
- timestamps and audit metadata

Ordinary teacher class list APIs must exclude preview classes by default. `web-admin` endpoints can list, inspect, reset, disable, or recreate preview classes/test students for operational support. These operations must be platform governance, not duplicated teacher class workflows.

Alternatives considered:

- Store test-student identity only in token claims without class/roster records: rejected because student APIs expect student/class context and web-admin needs auditability.
- Reuse a single global preview student for all teachers: rejected because it creates cross-teacher state collisions and makes operational audit/debug unclear.
- Show the preview class in the teacher class page with a hidden label: rejected because it pollutes normal class management and can confuse teachers.

### Decision 4: Preview differences are policy-driven, not page forks

The student app will get a thin preview runtime extension point. That layer may include:

- preview bootstrap route
- preview-aware app-config response
- `previewMode` and `previewPolicy` in student runtime context
- centralized route guard/visibility helpers
- centralized API behavior for preview media/auth and unsupported writes
- a preview sandbox adapter that exposes semantic view models and commands to pages

Future differences must follow this priority order:

1. Backend preview policy or endpoint guard.
2. Student app-config feature flags and preview policy.
3. Central route guard or navigation visibility helper.
4. Preview sandbox adapter view models and command guards.
5. Shared shell/entry component behavior.
6. Page-local preview logic only when the difference cannot be expressed centrally, with explicit tests, documentation, and a follow-up plan to remove it if an adapter abstraction becomes possible.

Examples:

- Preview profile identity: the page asks the preview sandbox adapter for the display profile. The adapter returns `00000000`, `施测平`, and `数智一班` in teacher preview mode, while normal student sessions receive the real user profile.
- Feedback in preview: the normal profile entry and feedback page remain usable for visual/interaction review; submit goes through a feedback command guard. The guard opens a preview-only dialog before a normal feedback API write is attempted, and the backend still rejects preview feedback writes as a guardrail.
- Assessment allowed for interaction only: test-student session may create preview/test-owned state; the data is excluded from normal analytics.
- Password/profile account mutation blocked: backend rejects preview claims and the student route shows a controlled unavailable state.

This design accepts a small, intentional preview runtime hook in `web-student`. It rejects widespread page-local `if preview` checks and any teacher-side copy of student page UI.

### Decision 4.1: The preview sandbox adapter is the student-side isolation boundary

The project should treat `web-student/src/app/preview/*` or an equivalent package-local module as the only student-side place where teacher-preview product decisions are encoded. Student routes and feature components may call adapter hooks/functions, but they should not directly branch on `previewMode`, `user.preview_mode`, `previewPolicy`, preview purpose strings, or hard-coded preview identity values.

Recommended adapter surface:

- `isTeacherStudentPreview(runtime)` returns whether the current session is the teacher-owned student preview.
- `getStudentProfilePresentation(runtime)` returns the visible profile identity for the profile page.
- `getFeedbackCapability(runtime)` returns whether the feedback entry/form should be visible and whether submit must be intercepted.
- `createFeedbackSubmitCommand(runtime, submitRealFeedback)` or equivalent command guard centralizes preview submit behavior.
- `getPreviewBlockedDialog(kind)` returns stable copy and tone for preview-only blocked writes.

The adapter does not render teacher UI, import `web-teacher`, or call teacher endpoints. It only translates preview runtime/policy into student-app presentation and command decisions. This keeps preview product differences explicit and testable while preserving the normal student pages as canonical.

Current implementation note: the first pass introduced a small number of page-local preview branches in profile and feedback pages. The boundary-hardening follow-up moves those teacher-preview branches into the preview sandbox adapter and adds source checks that prevent new raw preview branches from spreading into student pages.

### Decision 5: Web-admin governs preview infrastructure

`web-admin` expands to include platform operations for hidden preview classes/test students. It should not gain teacher learning workflows, catalog editors, question banks, analytics, or student app pages. Its preview management surface should be operational:

- list preview classes/test students
- inspect owner teacher and status
- reset or recreate a teacher's preview student
- disable or restore preview infrastructure
- view last session metadata and cleanup status where available

The backend owner must be `/api/web-admin/*` under platform token authorization. Teacher session creation remains `/api/admin/student-preview/*` under teacher-console authorization.

Alternatives considered:

- Put preview class management in `web-teacher`: rejected because ordinary teachers should not manage hidden system classes.
- Hide preview records from all UI and rely on database access: rejected because support/audit would become opaque and risky.

### Decision 6: Verification must prove reuse and boundaries

The change should include tests and checks that fail if implementation drifts into duplicated frontend code or mixed product ownership:

- teacher preview shell tests assert iframe URL/session loading and device controls
- student tests assert preview bootstrap redirects to normal student routes and uses normal student shell
- route guard tests assert disabled preview features are blocked centrally
- backend tests assert hidden preview classes are excluded from teacher class list APIs
- web-admin tests assert preview classes can be listed/managed only via platform endpoints
- import-boundary or source checks assert `web-teacher` does not import `web-student` route/page modules
- typecheck/build for `web-teacher`, `web-student`, and `web-admin`
- targeted browser/screenshot QA for the preview shell at common device presets

This explicit verification is important because the easiest implementation shortcut is to copy student UI into the teacher console. The tests should make that shortcut expensive.

## Risks / Trade-offs

- [Risk] Preview sessions accidentally pollute normal analytics or teacher dashboards. -> Mitigation: classify preview classes/students and preview token claims; exclude them from normal class/analytics queries; add backend tests for exclusions.
- [Risk] Future feature blocking becomes scattered across student pages. -> Mitigation: require preview policy, app-config, route guard, and backend guard first; only allow page-local exceptions with tests.
- [Risk] Preview product behavior slowly leaks into normal student components through repeated `previewMode` checks. -> Mitigation: introduce a preview sandbox adapter, forbid raw preview checks in student route/feature modules, and add source-boundary tests.
- [Risk] Iframe origin/CSP settings block local or deployed preview. -> Mitigation: define explicit environment variables for student app base URL and allowed frame origins; test local ports and production-like origins.
- [Risk] Student app auth storage conflicts with a teacher's real student login in the same browser. -> Mitigation: use a preview-specific token key or clearly scoped bootstrap/session handling if normal localStorage would overwrite real student sessions.
- [Risk] Hidden preview class lifecycle creates orphan records. -> Mitigation: make ensure/reset idempotent, store owner metadata, expose web-admin cleanup/reset actions, and add unique constraints for one active preview class/test student per teacher.
- [Risk] Device shell is mistaken for complete mobile emulation. -> Mitigation: product copy and requirements restrict it to viewport/device-shell simulation, not Chrome DevTools or real device emulation.
- [Risk] Existing point preview and new full preview duplicate device code. -> Mitigation: extract reusable device-shell primitives or share a feature-local module during implementation.

## Migration Plan

1. Add data classification fields and migration for preview classes/test students, including indexes/constraints for teacher ownership and listing filters.
2. Add backend service functions to ensure/reset teacher preview class and test student records idempotently.
3. Add teacher-console preview session endpoint returning a short-lived student bootstrap URL.
4. Add student preview ticket exchange and preview-aware auth/session claims.
5. Add student preview bootstrap route and runtime policy plumbing.
6. Add teacher preview page using a feature-local device shell and iframe.
7. Add web-admin preview infrastructure page and platform endpoints for listing/resetting hidden preview records.
8. Add backend exclusions so preview classes/students do not appear in ordinary teacher class workflows or normal analytics.
9. Add tests and browser QA for device shell, session bootstrap, policy/guard behavior, web-admin governance, and product/import boundaries.
10. Optionally refactor existing catalog point preview to use the shared device-shell primitives once the full preview shell is stable.

Rollback is safe if feature-gated: disable the teacher preview route and session endpoint while leaving hidden preview records inert. The student app should continue to run normal student sessions when no preview ticket is present.

## Open Questions

- Exact schema names for class/account classification can be chosen during implementation, but they must be explicit and queryable rather than hidden in opaque JSON only.
- Whether preview auth should reuse the normal student localStorage token key or use a preview-specific token key depends on how often teachers may also open `web-student` directly in the same browser.
- The current implementation keeps feedback entry/page available in preview, fixes the displayed preview profile identity for teacher guidance, and blocks real feedback submission through frontend interception plus backend write guards.

## Implementation Notes

- `web-teacher` owns only the device shell, toolbar, iframe lifecycle, and preview-session request. It does not import or recreate `web-student` route pages, feature components, CSS files, or router internals.
- `web-student` preview-specific behavior should be centralized in the `/preview/session` bootstrap, preview token helpers, app-config/runtime policy, shared authenticated layout route guard, and preview sandbox adapter.
- The profile page must use a preview-only display identity (`00000000`, `施测平`, `数智一班`) while preserving the underlying teacher-owned preview student session and backend claims. The source of that presentation decision should be the preview sandbox adapter.
- The feedback page remains the normal student feedback route in preview mode. Its submit behavior should flow through a preview-aware command guard that opens a preview-only dialog and does not call the feedback API, while the backend still returns a controlled rejection for direct preview feedback writes.
- No teacher student-preview profile or feedback branch should remain in ordinary student route/feature modules. The remaining `previewMode` usage in catalog point-preview components belongs to the pre-existing point preview surface, is covered by source-boundary allowlisting, and must not be used as a precedent for teacher-preview product branching.
