## 1. Foundation

- [x] 1.1 Add the selected Ant Design dependency set to `apps/web-teacher` and commit the lockfile update.
- [x] 1.2 Add a teacher component-library provider that maps the current SYSU red/warm-paper CSS variables into library theme tokens.
- [x] 1.3 Keep existing brand assets, sidebar dimensions, desktop minimum width, and route structure unchanged while the provider is introduced.
- [x] 1.4 Run `npm run typecheck`, `npm test`, and `npm run build` in `apps/web-teacher` after the provider is wired.

## 2. Teacher UI Adapter Layer

- [x] 2.1 Create a product-local teacher UI adapter module under `apps/web-teacher/src` for common primitives.
- [x] 2.2 Implement library-backed adapters for buttons, cards/page sections, metric display, alerts, empty/loading states, form fields, and modal/dialog shells.
- [x] 2.3 Ensure adapters expose stable class names or `data-testid` pass-through where existing tests and E2E need them.
- [x] 2.4 Add focused tests for adapter behavior that is not already covered by the component library.

## 3. Shell And Login Migration

- [x] 3.1 Migrate the teacher login form to component-library form/input/button primitives without changing `/api/auth/login` payloads.
- [x] 3.2 Migrate the teacher shell, sidebar navigation, breadcrumb/header, and user menu to component-library layout/menu/dropdown primitives or local adapters.
- [x] 3.3 Preserve canonical routes `/experiments`, `/questions`, `/analytics`, `/reports`, and forbidden-route redirects.
- [x] 3.4 Verify login, shell, navigation, and forbidden-route redirect behavior with existing unit tests and Playwright E2E.

## 4. Page Surface Migration

- [x] 4.1 Migrate shared page frame, loading, empty, notice, and error states.
- [x] 4.2 Migrate the experiment-management surface: chapter selector, catalog tree container, node editor forms, create-node dialog, and visibility controls.
- [x] 4.3 Migrate the LLM question-generation surface: metrics, point selector, prompt form, candidate review cards, and question-bank list.
- [x] 4.4 Migrate the analytics surface: class selector, metric cards, learning matrix, and student report summary.
- [x] 4.5 Migrate the report surface: prompt editor, variable chips, student/report selectors, and report detail panels.
- [x] 4.6 After each surface migration, remove or narrow obsolete hand-written CSS for the replaced primitives.

## 5. Visual And Behavior Regression

- [x] 5.1 Run `npm run typecheck`, `npm test`, and `npm run build` in `apps/web-teacher`.
- [x] 5.2 Run `python scripts/validate_legacy_e2e.py --skip-up` against a seeded Compose runtime.
- [x] 5.3 Capture or inspect browser renderings for login, shell, experiment management, LLM question generation, analytics, and reports to confirm the UI keeps the current SYSU red/warm-paper identity.
- [x] 5.4 Check production build output for material bundle-size regressions introduced by the component library and document any accepted increase.
- [x] 5.5 Run `openspec validate adopt-teacher-ui-component-library --strict`.

## 6. Documentation And Cleanup

- [x] 6.1 Update README or operations docs with the new teacher UI dependency and validation command if needed.
- [x] 6.2 Document the teacher UI adapter boundaries so future pages do not reintroduce broad hand-written primitive styles.
- [x] 6.3 Confirm `apps/web-student` package dependencies and tests remain unaffected by the teacher-only component-library migration.
