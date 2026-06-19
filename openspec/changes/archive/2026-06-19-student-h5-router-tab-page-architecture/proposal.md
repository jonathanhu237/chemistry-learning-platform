## Why

The student H5 app now behaves like a set of tab-switched panels rather than a real mobile mini-program route stack. Page-local actions such as asking AI or starting assessment can change the active bottom tab, which breaks mobile navigation expectations and makes each page hard to optimize independently.

This change introduces a clear route model: five root tabs for top-level destinations, shared second-level task pages that hide the bottom navigation, and source-preserving back behavior.

## What Changes

- Introduce `@tanstack/react-router` as the student H5 route layer for typed root routes, detail routes, parameters, and search/context handoff.
- Replace the current `StudentAppShell` state-only navigation with a route-driven tab/page architecture.
- **BREAKING structural refactor**: remove the current state-driven tab/screen implementation and reorganize the student frontend around real root/detail route boundaries instead of layering the new router over the old shell.
- Define five first-level tab roots: `home`, `learn`, `ai`, `assessment`, and `profile`.
- Define P0 second-level pages that are opened from one or more root pages and hide the bottom navigation:
  - chapter learning page
  - experiment point/video detail page
  - AI chat page
  - assessment session page
  - assessment report page
  - feedback page
- Preserve source-aware back behavior: opening a shared detail page from `home`, `learn`, `ai`, `assessment`, or `profile` returns to the originating root route.
- Reorganize student frontend files around route boundaries so root pages and detail pages can be optimized, tested, and fixed independently.
- Remove or relocate existing files whose ownership no longer matches the first-level/second-level page model; the implementation should favor a clean route-page structure over preserving the current directory shape.
- Clarify bottom navigation behavior:
  - Detail pages hide the bottom navigation.
  - Returning from detail to root restores the bottom navigation quickly.
  - Root pages may still hide or compress the bottom navigation during scroll for content focus, but root route identity remains active.
- Remove content actions that directly switch `activeTab`; page-local actions push detail routes instead.

## Capabilities

### New Capabilities

- `student-h5-route-stack-navigation`: Defines the route stack, root tabs, shared detail pages, bottom navigation visibility, and source-aware return behavior for the authenticated student H5 app.

### Modified Capabilities

- `student-h5-learning-flow`: Learning entry, chapter learning, point detail, AI handoff, and assessment handoff must use route-stack navigation instead of changing the active tab.
- `student-h5-platform-shell`: Student SPA serving must support direct refresh and deep links for route-driven student H5 paths without intercepting API or admin routes.

## Impact

- Affected frontend code:
  - `apps/student-web/src/app/StudentAppShell.tsx`
  - `apps/student-web/src/app/routes.ts`
  - `apps/student-web/src/features/learning/*`
  - `apps/student-web/src/features/experiments/*`
  - `apps/student-web/src/features/assistant/*`
  - `apps/student-web/src/features/assessment/*`
  - `apps/student-web/src/features/feedback/*`
  - student CSS for app shell, bottom navigation, page transitions, and safe-area spacing
- New dependency: `@tanstack/react-router`.
- Backend APIs should remain unchanged for P0. Server SPA fallback may need route-serving validation for nested H5 paths.
- Tests and mobile QA must change from tab-state expectations to route-stack expectations.
