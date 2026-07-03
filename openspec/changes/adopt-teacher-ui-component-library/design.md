## Context

`apps/web-teacher` is currently a legacy React/Vite application with only `react` and `react-dom` runtime dependencies. The main teacher console is concentrated in `LegacyTeacherApp.tsx` and `styles.css`, where page shell, navigation, forms, cards, lists, menus, dialogs, loading states, and error states are all hand-written.

The product decision from the previous legacy collapse is that this branch has two browser products: `web-student` and `web-teacher`. This change is only about the teacher console presentation and implementation foundation. It must preserve current teacher workflows, route paths, authentication, backend contracts, and the already-added Playwright teacher/student E2E smoke.

The user-facing direction is not "make it look like a new product." The direction is "use a component library so it stops looking hand-made, while keeping the current style basically consistent."

## Goals / Non-Goals

**Goals:**

- Adopt a mature desktop component library for `web-teacher`.
- Preserve the current SYSU red, warm paper background, compact desktop density, low-radius rectangular controls, and left-sidebar teacher-console structure.
- Replace primitive hand-written UI with library-backed local adapters before migrating feature surfaces.
- Reduce the long-term size and ownership risk of the current monolithic teacher React/CSS files.
- Keep frontend unit tests, Playwright E2E smoke, and production readiness validation green throughout the migration.

**Non-Goals:**

- Do not change backend API behavior, database schema, role semantics, or Compose topology.
- Do not redesign student-facing `web-student`.
- Do not introduce a new teacher information architecture or revive removed admin/platform workflows.
- Do not replace all feature code in one risky rewrite if a staged migration can preserve behavior.
- Do not adopt a generic default component-library theme that visually erases the current legacy teacher identity.

## Decisions

### ADR 1: Use Ant Design as the teacher component library

Use Ant Design for the teacher console because it is a mature desktop management UI library with strong coverage for the controls this app already hand-rolls: layout, menu, card, form, input, select, checkbox, modal, dropdown, alert, empty, table/list, tabs, and loading states. The existing OpenSpec tree also already contains an Ant Design admin-console direction, so this decision aligns with prior architecture rather than introducing a new UI stack.

Alternatives considered:

- Mantine: viable and flexible, but would create a second design-system direction unrelated to the existing Ant Design spec.
- shadcn/Radix + Tailwind: strong composability, but this repo does not currently use Tailwind and the migration would become a tooling/style-system change rather than a focused teacher-console cleanup.
- Keep hand-written CSS and only polish visuals: lowest dependency cost, but it does not solve the maintainability problem.

### ADR 2: Hide Ant Design behind local teacher UI adapters

Do not scatter raw Ant Design usage everywhere immediately. Add a small local UI adapter layer under `apps/web-teacher/src/ui/` or equivalent. It should own teacher-specific wrappers such as `TeacherButton`, `TeacherCard`, `TeacherPage`, `TeacherMetric`, `TeacherFormItem`, `TeacherEmptyState`, `TeacherAlert`, and layout helpers. Feature pages can still use Ant Design directly for complex primitives like `Form`, `Table`, `Modal`, and `Tabs` when a wrapper would add no value.

This keeps SYSU styling, density, accessibility defaults, and test hooks consistent while allowing migration page by page.

Alternatives considered:

- Direct Ant Design components everywhere: faster first pass, but risks inconsistent overrides and a generic Ant Design look.
- Build a full design system before migrating pages: cleaner in theory, but too slow and too abstract for a legacy rescue pass.

### ADR 3: Theme tokens preserve the current teacher identity

Configure Ant Design through `ConfigProvider` theme tokens and a small CSS compatibility layer. Tokens should map the current CSS variables to library concepts:

- primary color: `--legacy-sysu-red`
- background/container: `--legacy-bg` and `--legacy-paper`
- border: `--legacy-line`
- text: `--legacy-ink` and `--legacy-muted`
- radius: low radius, never a soft SaaS card style
- density: compact enough for repeated teacher operations

The teacher console must not switch to the default blue Ant Design identity.

Alternatives considered:

- Full custom CSS overrides for every Ant Design class: powerful but brittle.
- CSS-only theme without `ConfigProvider`: misses component-library state and token integration.

### ADR 4: Migrate by surface, not by primitive search-and-replace

The first implementation pass should create the library foundation and migrate stable high-leverage surfaces:

- app provider/theme shell
- login form
- sidebar/header/user menu
- page frame, alerts, empty/loading states
- metric cards
- common forms and buttons
- create-node modal/context menu

Feature-specific complex areas such as catalog tree editing, question generation review cards, analytics matrix, and report prompt editor should move only after the shared primitives are in place. This avoids breaking behavior by replacing every `<button>` and `<input>` mechanically.

Alternatives considered:

- Whole-file rewrite: likely to regress route behavior, loading states, and test fixtures.
- Only restyle with Ant Design CSS classes: does not reduce local component complexity.

### ADR 5: Verification includes visual and behavior gates

Keep existing unit tests and Playwright E2E smoke as required gates. Add focused tests where wrappers have behavior, especially form submit state, forbidden route redirect, menu interactions, modal open/close, and preserved test IDs. Use screenshots or Playwright traces as local debugging artifacts, but do not commit generated visual reports.

## Risks / Trade-offs

- [Risk] Ant Design default styles leak into the product and make the console look unrelated to the current legacy style. → Mitigation: route all top-level rendering through `ConfigProvider`, keep SYSU tokens, and add E2E/visual review tasks for login, shell, and each migrated page.
- [Risk] The migration increases bundle size. → Mitigation: measure production build output before and after, prefer direct imports through the library's supported tree-shaking path, and avoid importing optional heavy components that are not used.
- [Risk] Wrappers become an unnecessary second component library. → Mitigation: wrap only teacher-specific conventions and use raw Ant Design for complex primitives where the library API is already clear.
- [Risk] Monolithic files remain large even after adding Ant Design. → Mitigation: require page/surface extraction alongside migration tasks rather than adding wrappers inside the same monolith indefinitely.
- [Risk] Component-library form behavior changes submit timing or validation messages. → Mitigation: migrate forms one at a time with focused tests and keep API payload shapes unchanged.

## Migration Plan

1. Add Ant Design dependencies with an exact lockfile update and verify React 19 compatibility locally.
2. Add a teacher UI provider and token bridge from current CSS variables to Ant Design theme tokens.
3. Introduce local adapter components for common teacher-console primitives.
4. Migrate login, shell, header, menu, page frame, alerts, loading/empty states, metrics, and buttons.
5. Migrate forms, selects, modal/dialog, dropdown/context-menu, and tabs surface by surface.
6. Reduce obsolete CSS after each migrated surface has equivalent scoped styles.
7. Run `apps/web-teacher` typecheck/tests/build, legacy Playwright E2E, and focused visual inspection.

Rollback is straightforward while this remains frontend-only: revert the dependency and UI migration commit(s), rebuild `web-teacher`, and keep backend/Compose unchanged.

## Open Questions

- Should the implementation pin the current latest Ant Design major or an older major already familiar to the team? At proposal time, npm reports `antd@latest` as a React >=18 compatible major, but implementation should pin the exact selected version in `package-lock.json`.
- Should charts or data visualization components be included in this pass? The conservative answer is no unless a migrated page already needs them.
- Should the final UI adapter folder be named `ui`, `components`, or `teacher-ui`? Use the existing codebase naming preference if one emerges during implementation.

## Glossary

- **Component library**: A maintained third-party UI package used for standard controls and stateful components.
- **Teacher UI adapter**: A local wrapper or helper that maps component-library primitives to this project's teacher-console style and behavior conventions.
- **SYSU legacy theme**: The current teacher-console visual identity built around SYSU red, warm background, dense desktop layout, and low-radius rectangular controls.
- **Surface migration**: Replacing one coherent UI area, such as login or the catalog editor header, rather than replacing all matching HTML primitives globally.
- **Compatibility CSS**: Temporary or scoped CSS that preserves current layout and brand while migration is incomplete.
