# web-teacher-engineering-structure Specification

## Purpose
TBD - created by archiving change standardize-application-engineering-structure. Update Purpose after archive.
## Requirements
### Requirement: Teacher console shell is separated from feature pages
The `web-teacher` frontend SHALL separate app providers, auth guard, route registry, navigation model, shell layout, and feature pages.

#### Scenario: Admin shell behavior changes
- **WHEN** a change modifies login, auth redirection, role-based visibility, global theme, navigation, or shell layout
- **THEN** the change MUST be owned by an app/shell-level module
- **AND** feature page modules MUST NOT become responsible for global shell behavior.

#### Scenario: A new teacher page is added
- **WHEN** a new teacher-console page is introduced
- **THEN** it MUST be added through a route registry or equivalent app route owner
- **AND** its nav metadata SHOULD live with the route/nav owner rather than being duplicated in page code.

### Requirement: Teacher console features are business capability modules
`web-teacher` frontend features SHALL be grouped by business capability and decomposed into page orchestration, hooks, panels, forms, tables, and adapters when they grow.

#### Scenario: A page owns multiple responsibilities
- **WHEN** a feature page mixes data fetching, table logic, form state, modal/drawer workflows, upload flows, domain formatting, and rendering in one module
- **THEN** the feature SHOULD split those responsibilities into local feature modules
- **AND** route-level lazy loading MUST continue to expose a page entrypoint.

#### Scenario: Cross-feature UI is extracted
- **WHEN** a component is reused by multiple admin features
- **THEN** it MAY move to `components/*`
- **AND** it MUST NOT import feature-specific data types or feature API clients.

### Requirement: Teacher console API clients are domain-owned
The `web-teacher` frontend SHALL split HTTP primitives from domain-specific clients and schemas.

#### Scenario: A new admin API contract is consumed
- **WHEN** a feature consumes a new admin API contract
- **THEN** shared request primitives MAY remain in `api`
- **AND** feature/domain schemas and endpoint helpers SHOULD live in a domain-specific API owner rather than expanding a single global `api/index.ts`.

#### Scenario: A backend route moves ownership
- **WHEN** backend API route ownership changes without changing canonical paths
- **THEN** admin frontend API clients MUST keep public behavior stable
- **AND** tests or smoke checks MUST prove the page still reaches the canonical route.

### Requirement: Teacher console structure changes keep e2e smoke
Teacher console shell and top-level page structure changes SHALL keep admin e2e smoke as a release gate.

#### Scenario: Admin shell, auth, navigation, or top-level routes change
- **WHEN** a change touches admin shell, auth, navigation, route registry, or lazy page boundaries
- **THEN** admin e2e smoke MUST run
- **AND** it MUST fail on console errors, page errors, unexpected 404s, or known UI-library warnings that the project treats as regressions.
