## ADDED Requirements

### Requirement: Teacher console uses a component-library foundation
The `web-teacher` frontend SHALL use a maintained component library as the foundation for standard desktop management controls.

#### Scenario: Teacher frontend dependencies are inspected
- **WHEN** a maintainer inspects `apps/web-teacher/package.json`
- **THEN** the package SHALL include the selected component library as a runtime dependency
- **AND** the selected dependency version SHALL be pinned through the package lockfile.

#### Scenario: Standard controls are implemented
- **WHEN** teacher pages render buttons, forms, selects, cards, alerts, empty states, loading states, modals, dropdowns, tabs, tables, or list-style management surfaces
- **THEN** those controls SHALL use component-library primitives directly or through local teacher UI adapters
- **AND** new broad hand-written primitive control styles SHALL NOT be introduced as a replacement for the component library.

### Requirement: Teacher UI adapters preserve the legacy visual identity
The teacher frontend SHALL expose local UI adapters or theme wrappers that make component-library primitives match the existing SYSU legacy teacher-console style.

#### Scenario: Component library provider renders the teacher app
- **WHEN** `web-teacher` starts
- **THEN** the app SHALL be wrapped in the selected component library provider or equivalent theme entry point
- **AND** theme tokens SHALL preserve SYSU red, warm paper backgrounds, muted borders, low-radius rectangular controls, and dense desktop spacing.

#### Scenario: Migrated pages are visually inspected
- **WHEN** login, shell, experiment management, LLM question generation, analytics, and report pages are rendered after migration
- **THEN** they SHALL keep the existing left sidebar, header hierarchy, SYSU brand assets, and warm teacher-console palette
- **AND** they SHALL NOT look like the component library's default blue/white theme.

### Requirement: Migration preserves teacher workflows and routes
The component-library migration SHALL preserve existing teacher-console workflow behavior.

#### Scenario: Authenticated teacher opens canonical routes
- **WHEN** an authenticated teacher opens `/experiments`, `/questions`, `/analytics`, or `/reports`
- **THEN** each route SHALL render the same workflow purpose as before the component-library migration
- **AND** API calls, route paths, data loading behavior, and authorization behavior SHALL remain compatible.

#### Scenario: Existing E2E selectors are used
- **WHEN** Playwright E2E tests locate teacher login, shell, navigation, and page test IDs
- **THEN** those selectors SHALL remain available or be deliberately updated together with the E2E tests
- **AND** the browser E2E smoke SHALL continue to cover the same teacher and student journeys.

### Requirement: Hand-written CSS shrinks toward layout and compatibility ownership
The teacher frontend SHALL reduce broad hand-written primitive CSS as surfaces migrate to the component library.

#### Scenario: A teacher surface is migrated
- **WHEN** a page surface is converted to component-library controls
- **THEN** obsolete CSS for the replaced primitive controls SHALL be removed or narrowed to compatibility styles
- **AND** remaining CSS SHALL focus on brand tokens, shell layout, feature-specific composition, or temporary compatibility.

#### Scenario: New CSS is added
- **WHEN** implementation requires new teacher CSS
- **THEN** the CSS SHALL be scoped to the teacher shell, local UI adapter, or owning feature surface
- **AND** it SHALL NOT introduce a second global primitive control system alongside the component library.

### Requirement: Component-library migration is verified by behavior and visual gates
The migration SHALL include automated and manual verification gates appropriate for a UI foundation change.

#### Scenario: Local validation runs
- **WHEN** the component-library migration is implemented
- **THEN** `web-teacher` typecheck, unit tests, production build, and legacy Playwright E2E smoke SHALL pass
- **AND** any component wrapper with behavior SHALL have focused unit coverage or be covered by E2E.

#### Scenario: Visual review is performed
- **WHEN** migrated teacher pages are ready for handoff
- **THEN** screenshots or equivalent browser inspection SHALL confirm no broken layout, unreadable text, overlapping controls, or accidental default component-library theme
- **AND** generated screenshot/report artifacts SHALL remain ignored unless intentionally promoted to documentation.
