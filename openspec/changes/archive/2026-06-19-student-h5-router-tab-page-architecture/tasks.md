## 1. Router Foundation

- [x] 1.1 Add `@tanstack/react-router` to `apps/student-web` dependencies and update lockfile.
- [x] 1.2 Create `app/router` modules for router creation, typed route helpers, and route visibility helpers.
- [x] 1.3 Replace authenticated `StudentAppShell` state navigation with a route-backed authenticated layout.
- [x] 1.4 Ensure login, password-change, pretest loading, pretest error, and pretest onboarding remain outside the authenticated route shell.
- [x] 1.5 Remove `activeTab`, `learningRoute`, `experimentRoute`, and `assessmentRoute` as the global authenticated navigation model after route parity is reached.

## 2. Root Tab Routes

- [x] 2.1 Add the `home` root route and page module for recommendations, progress, recent learning, and task entry points.
- [x] 2.2 Convert the learning root route to an entry/search/selection surface using the existing periodic-table and chapter entry components.
- [x] 2.3 Convert the AI root route to an AI center with new-chat, history, and suggested entry points.
- [x] 2.4 Convert the assessment root route to an assessment center with available assessments and report entry points.
- [x] 2.5 Convert the profile root route to student identity, feedback entry, account, and logout actions.
- [x] 2.6 Update bottom navigation to route to `home`, `learn`, `ai`, `assessment`, and `profile`, with `AI` centered.

## 3. P0 Detail Routes

- [x] 3.1 Add a chapter learning detail route that reuses the current chapter learning content and hides the bottom navigation.
- [x] 3.2 Add an experiment point/video detail route that reuses the current experiment detail content and hides the bottom navigation.
- [x] 3.3 Add an AI chat detail route that reuses the chat panel, accepts optional source/context state, and hides the bottom navigation.
- [x] 3.4 Add an assessment session detail route that reuses the posttest answer flow and hides the bottom navigation.
- [x] 3.5 Add an assessment report detail route that reuses the posttest summary/report flow and hides the bottom navigation.
- [x] 3.6 Add a feedback detail route that reuses the authenticated feedback form and hides the bottom navigation.

## 4. Source-Aware Navigation

- [x] 4.1 Replace page-local `setActiveTab` calls with route pushes to detail pages.
- [x] 4.2 Ensure contextual AI from home, chapter learning, point detail, and report pages opens the shared AI chat detail page without switching root tab identity.
- [x] 4.3 Ensure chapter recommendations from home and chapter selections from learn open the same chapter detail page and return to their source route through history.
- [x] 4.4 Ensure learning completion from chapter and point detail opens the assessment session detail route without switching to the assessment root.
- [x] 4.5 Provide a shared detail-page back helper that prefers browser/history back and has a safe fallback to the source root route.

## 5. Navigation Visibility And Layout

- [x] 5.1 Implement route-level bottom-navigation visibility so root routes are nav-eligible and P0 detail routes hide the nav.
- [x] 5.2 Restore the bottom navigation quickly when returning from a detail route to a root route.
- [x] 5.3 Add restrained root-page scroll hide/compress behavior for the bottom navigation where it improves content space.
- [x] 5.4 Ensure root scroll hiding does not change active root identity and does not apply on detail routes.
- [x] 5.5 Update mobile safe-area spacing so hidden-nav detail pages and root pages with visible nav both avoid content/action overlap.

## 6. Frontend Organization

- [x] 6.1 Create route page folders under `src/routes` for home, learn, AI, assessment, and profile.
- [x] 6.2 Move shell-specific components under `src/app/shell`.
- [x] 6.3 Keep reusable learning, experiment, assistant, assessment, and feedback UI under `src/features`.
- [x] 6.4 Remove obsolete experiment-root tab code from the bottom navigation model while preserving reusable experiment detail/list components where needed.
- [x] 6.5 Split large shell logic into route pages and shared hooks so each root/detail page can be optimized independently.
- [x] 6.6 Delete or decompose obsolete `StudentAppShell` responsibilities so it no longer owns root/detail page selection.
- [x] 6.7 Remove or relocate files whose current location conflicts with the root-page/detail-page ownership model.

## 7. Serving And Deep Links

- [x] 7.1 Verify the FastAPI student SPA fallback serves direct root routes such as `/home`, `/learn`, and `/ai`.
- [x] 7.2 Verify the FastAPI student SPA fallback serves direct detail routes such as `/chapter/{profileId}`, `/point/{experimentId}`, `/ai/chat`, `/assessment/session/{sessionId}`, `/assessment/report/{sessionId}`, and `/feedback/new`.
- [x] 7.3 Ensure `/api` and `/admin` routes remain excluded from the student SPA fallback.

## 8. Verification

- [x] 8.1 Update student H5 unit/e2e tests to assert route URLs, root tab activation, detail-page bottom-nav hiding, and history back behavior.
- [x] 8.2 Update mobile viewport QA to cover 360px, 390px, and 430px widths for all five root tabs and all P0 detail pages.
- [x] 8.3 Verify contextual AI, chapter recommendation, learning completion, report opening, and feedback opening never change root tab identity as a side effect.
- [x] 8.4 Run student typecheck, tests, build, and mobile QA.
- [x] 8.5 Run or update production readiness checks for student nested route serving.
