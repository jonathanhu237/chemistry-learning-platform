## MODIFIED Requirements

### Requirement: Frontend feature modules are decomposed incrementally
The admin frontend SHALL reduce large feature-page modules through behavior-preserving extraction of pure helpers, local components, local hooks, or component-library-backed teacher UI adapters.

#### Scenario: A large feature slice is extracted
- **WHEN** a feature-page slice is moved into a new module
- **THEN** existing route paths, API calls, query keys, mutation behavior, and visible workflows MUST remain compatible

#### Scenario: A teacher UI primitive is migrated
- **WHEN** a hand-written teacher-console button, form field, card, modal, alert, empty state, menu, tab, table, or list primitive is replaced by a component-library-backed implementation
- **THEN** the replacement MUST live in a shared teacher UI adapter or the owning feature module
- **AND** the migration MUST reduce or scope the corresponding global CSS rather than adding another broad hand-written primitive style.

#### Scenario: A migrated surface keeps behavior
- **WHEN** a teacher-console page surface is migrated to component-library primitives
- **THEN** existing route behavior, auth behavior, API payloads, loading states, error states, and user-visible workflow outcomes MUST remain compatible
- **AND** focused tests or browser E2E MUST cover the migrated surface before completion.

## ADDED Requirements

### Requirement: Component-library ownership stays product-local
The component-library migration SHALL stay owned by `web-teacher` unless another product explicitly proposes its own UI foundation.

#### Scenario: Teacher UI adapters are introduced
- **WHEN** shared teacher UI adapters, theme providers, or component-library wrappers are added
- **THEN** they MUST live under `apps/web-teacher`
- **AND** `web-student` MUST NOT import those teacher-specific adapters.

#### Scenario: Student frontend is inspected after migration
- **WHEN** the component-library migration is complete
- **THEN** `apps/web-student` package dependencies and visual behavior MUST remain unchanged except for shared tooling updates that are explicitly justified
- **AND** no student route SHALL depend on teacher component-library styling.
