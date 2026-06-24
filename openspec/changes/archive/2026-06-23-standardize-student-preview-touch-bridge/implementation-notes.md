## Baseline Audit

- `@use-gesture/react` usage before implementation:
  - `apps/web-teacher/src/features/student-preview/input/PreviewGestureSurface.tsx`
  - `apps/web-teacher/src/features/student-preview/studentPreviewContracts.test.ts`
  - `apps/web-teacher/package.json`
  - `apps/web-teacher/package-lock.json`
- Matching protocol modules before implementation:
  - `apps/web-teacher/src/features/student-preview/input/previewInputProtocol.ts`
  - `apps/web-student/src/app/preview/input/previewInputProtocol.ts`
  - Both originally exposed `hover`, `touchStart`, `touchMove`, `touchEnd`, `touchCancel`, `tap`, and `longPress`.
- Focused test files:
  - `apps/web-teacher/src/features/student-preview/input/previewInputProtocol.test.ts`
  - `apps/web-teacher/src/features/student-preview/studentPreviewContracts.test.ts`
  - `apps/web-student/src/app/preview/input/PreviewInputRuntime.test.ts`
  - `apps/web-student/src/roleBoundaries.test.ts`
- Manual QA surfaces:
  - Teacher page: `http://127.0.0.1:5174/student-preview`
  - Student iframe/default container: `http://222.200.189.249:5173`
  - Popover dismissal: 学习首页 -> 元素分区气泡 -> press outside bubble.
  - Horizontal rail: chapter detail page with element tiles, e.g. 过渡金属 or 碱金属和碱土金属.
  - Vertical scroll: 学习首页 and chapter catalog pages.
  - Ordinary tap activation: bottom navigation, element area buttons, chapter list rows, and “进入学习”.

## Implementation Decisions

- Preview protocol v2 is the active protocol for this change.
- Student-facing protocol event types are lifecycle-only: `hover`, `touchStart`, `touchMove`, `touchEnd`, and `touchCancel`.
- `tap` and `longPress` are rejected as protocol messages and are covered by protocol tests.
- The student runtime uses standards-aligned synthetic Pointer Events as the required baseline. Synthetic Touch Events were not added because desktop/JSDOM construction support is inconsistent; product behavior is verified through Pointer Events, DOM activation, and scroll outcomes.
- The student preview browser QA uses iPhone SE plus a regenerated preview session so the iframe has a real small-screen scroll range. Regenerating after a consumed preview ticket can leave a harmless 401 from the stale iframe request; the active regenerated iframe loads and passes interaction checks.
- Browser QA result on `http://127.0.0.1:5174/student-preview` with student iframe served from `http://222.200.189.249:5173`: iframe loaded; short tap opened the learning-area popover; outside press dismissed it without click-through; short tap entered the d-area chapter detail; vertical drag scrolled the catalog from `0` to `125` without activation; horizontal drag moved the element rail from `0` to `131`; long press did not activate an inactive tile; touch indicator cleared after idle.
