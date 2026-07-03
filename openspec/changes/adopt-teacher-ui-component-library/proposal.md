## Why

The legacy teacher console currently implements most controls, cards, menus, dialogs, forms, and page states by hand inside one large React file and one large stylesheet, which makes the UI look uneven and makes further maintenance risky. The next pass should adopt a mature component library while preserving the current SYSU-style teacher-console identity, so the backend can feel more polished without changing the product shape.

## What Changes

- Introduce a component-library foundation for `apps/web-teacher`, using Ant Design as the canonical desktop management UI library.
- Add a local teacher UI adapter layer that maps Ant Design components to the existing visual language: SYSU red, warm paper background, dense desktop layout, low-radius rectangular controls, and the current sidebar/header structure.
- Replace hand-written teacher-console controls incrementally with library-backed components for buttons, inputs, selects, cards, metrics, alerts, empty/loading states, modals, dropdown menus, tabs, tables/lists, and form validation.
- Preserve the current teacher workflows, route paths, API calls, role behavior, test IDs, and Playwright E2E coverage.
- Remove obsolete global CSS only after the equivalent library-backed component or scoped style exists.
- Do not migrate `web-student` as part of this change.

## Capabilities

### New Capabilities
- `teacher-ui-component-system`: Defines the component-library adoption, teacher-console design tokens, adapter components, migration boundaries, visual compatibility expectations, and regression coverage for `web-teacher`.

### Modified Capabilities
- `react-ant-design-admin-console`: Align the existing Ant Design console requirement with the legacy two-role teacher console and current SYSU red/warm-paper visual identity instead of the older admin/green-teal assumptions.
- `frontend-admin-maintainability`: Require component-library migration to reduce the current monolithic teacher React/CSS surface through feature-owned components and shared UI adapters rather than another broad hand-written style layer.

## Impact

- `apps/web-teacher/package.json` and lockfile will gain component-library dependencies.
- `apps/web-teacher/src/LegacyTeacherApp.tsx` will be decomposed or partially wrapped behind local UI components as pages migrate.
- `apps/web-teacher/src/styles.css` will shrink toward theme tokens, shell layout, and scoped compatibility styles instead of owning every primitive control.
- Teacher frontend unit tests and legacy Playwright E2E smoke must continue to pass.
- No backend API, database, Compose service, role model, or student frontend behavior should change.
